"""Logging-only instrumentation of the LMCache 0.5.5 cache server for the CXL-vs-NVMe serving study (2026-11-12).

Loaded through PYTHONPATH by the `lmcache server` process only (Python imports `sitecustomize` at start-up); with KVEVT_OUT unset
nothing happens. It adds, without changing a placement, eviction, admission or transfer decision:

 1. an event-bus mirror: every event LMCache publishes except the CB_* / TRACE_* families, one JSON line each
       {"ev": <type>, "t": <wall time>, "tm": <monotonic ns when the line was written>, "sid": <session id>, ...scalar metadata,
        "cpu": <CPU time of the server process, ns, on the MP_* events>, "keys": [first 16 hex digits of the chunk hash, ...], "bk": one letter per key for the L1 events (D = DRAM, X = Device-DAX: the medium LMCache reports in the
        event's L1ObjectMeta; for L1_READ_RESERVED, which carries none, looked up in the L1 manager when the line is written,
        "?" if the object is gone by then), "nb": bytes of those objects}
 2. the media copies of the L2 tiers, one line per chunk:
       {"ev": "dax.w" | "dax.r", "dev": <device path>, "off": <byte offset in the device>, "n": <bytes>, "t0": <monotonic ns>, "dt": <ns>}
          (DaxCore._default_do_write / _default_do_read: the ctypes.memmove between an L1 object and its DAX slot)
       {"ev": "fs.w" | "fs.r", "f": <file name>, "n": <bytes>, "t0", "dt"}   (FSL2Adapter._write_with_odirect / _read_with_odirect)
    The native file adapter (fs_native) does its I/O in C++ threads; its timing comes from the L2_LOAD_TASK_* / L2_STORE_* events.
 3. the Device-DAX L1 arenas: {"ev": "l1dax.arena", "dev", "size", "pinned": true|false} after each arena is mapped and registered
    with CUDA (pinned = cudaHostRegister succeeded, i.e. the GPU reads the DAX mapping directly; KVTIER_NO_PIN=1 skips the
    registration -- an experiment variant, the only behaviour-changing switch here);
    KVTIER_L1_EXTRA_DAX="<dev>:<GiB>[,<dev>:<GiB>...]" maps further devices into the L1 arena pool with LMCache's own
    DevDaxL1MemoryManager.add_device() right after the manager is built (the CLI can name only one device).
 4. a 1 Hz sampler: {"ev": "mem", process RSS (anon / file / shmem), system MemAvailable / Cached / Shmem / Dirty / Writeback,
    /proc/diskstats of KVTIER_DISK (sectors and I/Os read / written)} -- the DRAM-budget accounting and the proof that file
    reads reach the NVMe device and not the page cache.
 5. with KVTIER_VERIFY=1 (validation runs only; it costs a hash per chunk): the SHA-1 of every chunk written to a DAX slot
    ({"ev": "dax.w", ..., "sha1"}) and of sampled L1 Device-DAX objects three seconds after their allocation
    ({"ev": "l1dax.obj", "dev", "off", "n", "sha1"}), so that an independent process can read the device at that offset and
    compare (verify_residency.py)."""
import ctypes, hashlib, json, os, threading, time

_OUT = os.environ.get("KVEVT_OUT")
try: _cmd = open("/proc/self/cmdline", "rb").read().split(b"\0")
except Exception: _cmd = []
# only the cache server itself: helper processes it starts inherit the environment and would write into the same file
if _OUT and b"server" in _cmd and any(a.endswith(b"lmcache") for a in _cmd[:3]):
    _f = open(_OUT, "a", buffering=1); _lock = threading.Lock(); _VERIFY = os.environ.get("KVTIER_VERIFY") == "1"
    def _w(d):
        line = json.dumps(d) + "\n"
        with _lock: _f.write(line)
    _w({"ev": "kvtier.start", "t": time.time(), "tm": time.monotonic_ns(), "pid": os.getpid(), "verify": _VERIFY})
    _L1 = {"mgr": None}

    # ---- 1. event-bus mirror
    import lmcache.v1.mp_observability.config as _cfg
    from lmcache.v1.mp_observability.event import EventType
    from lmcache.v1.mp_observability.event_bus import EventSubscriber

    def _hx(h):
        if isinstance(h, (bytes, bytearray)): return h.hex()
        if isinstance(h, int): return format(h, "x")
        return str(h)
    def _key(k):
        h = getattr(k, "chunk_hash", None); s = _hx(h) if h is not None else str(k); g = getattr(k, "object_group_id", 0)
        return s if not g else f"{s}/{g}"
    def _backends(keys):
        mgr = _L1["mgr"]
        if mgr is None: return None
        out = []
        for k in keys:
            try:
                e = mgr._objects.get(k); b = mgr._memory_manager.get_backend_type(e.memory_obj) if e is not None and e.memory_obj is not None else None
                out.append("?" if b is None else ("X" if "DAX" in str(b).upper() else "D"))
            except Exception: out.append("?")
        return "".join(out)

    class _Mirror(EventSubscriber):
        def get_subscriptions(self):
            # not mirrored: the CB_* / TRACE_* families, the token ids of every stored request (MP_TOKENS), vLLM's block lists and
            # the storage-manager (SM_*) events, which repeat the L1 events with stringified keys
            skip = ("CB_", "TRACE_", "SM_", "MP_TOKENS", "MP_VLLM_BLOCK_ALLOCATION")
            return {e: self._on for e in EventType if not e.name.startswith(skip)}
        def _on(self, ev):
            md = ev.metadata or {}
            if ev.event_type.name == "L1_EVICTION_LOOP_TICK" and not md.get("triggered"):
                self._ticks = getattr(self, "_ticks", 0) + 1
                if self._ticks % 10 != 1: return                 # an idle eviction loop tick every 10th time only
            d = {"ev": ev.event_type.value, "t": ev.timestamp or time.time(), "tm": time.monotonic_ns(), "sid": ev.session_id}
            if ev.event_type.name.startswith("MP_"): d["cpu"] = time.process_time_ns()      # CPU time of the whole server process so far
            for k, v in md.items():
                if k in ("model_name", "engine_id", "cache_salt", "key_count_per_salt", "token_chunks"): continue
                if k == "keys":
                    d["keys"] = [_key(x)[:16] for x in v]         # first 64 bits of the chunk hash: enough to join events
                    if ev.event_type.name == "L1_READ_RESERVED":      # no "meta" in this event: look the medium up
                        b = _backends(v)
                        if b is not None: d["bk"] = b
                elif k in ("chunk_hashes", "hashes"): d["hashes"] = [_hx(x)[:16] for x in v]
                elif k == "meta":      # list of L1ObjectMeta(size_bytes, backend): the medium LMCache itself reports for the object
                    try: d["bk"] = "".join("X" if "DAX" in str(getattr(x, "backend", "")).upper() else "D" for x in v); d["nb"] = sum(int(getattr(x, "size_bytes", 0)) for x in v)
                    except Exception: pass
                elif k in ("dtypes", "shapes"): continue
                elif isinstance(v, (int, float, str, bool)) or v is None: d[k] = v
                else:
                    try: d[k] = json.loads(json.dumps(dict(v) if hasattr(v, "items") else list(v)))
                    except Exception: d[k] = str(v)[:300]
            _w(d)
        def shutdown(self):
            _w({"ev": "kvtier.stop", "t": time.time(), "tm": time.monotonic_ns()})

    _orig_init = _cfg.init_observability
    def init_observability(*a, **kw):
        bus = _orig_init(*a, **kw); bus.register_subscriber(_Mirror()); return bus
    _cfg.init_observability = init_observability

    # the L1 manager instance (for the medium of an object); nothing is called on it but dictionary lookups
    try:
        from lmcache.v1.distributed import l1_manager as _l1m
        _l1_init = _l1m.L1Manager.__init__
        def _l1_init_wrapped(self, *a, **kw):
            _l1_init(self, *a, **kw); _L1["mgr"] = self
        _l1m.L1Manager.__init__ = _l1_init_wrapped
    except Exception as e: _w({"ev": "kvtier.warn", "what": f"L1Manager hook: {e!r}"})

    # ---- 2. media copies of the DAX L2 adapter and of the Python file adapter
    try:
        from lmcache.v1.storage_backend.dax import core as _dc
        _dw, _dr = _dc.DaxCore._default_do_write, _dc.DaxCore._default_do_read
        def _do_write(self, offset, memory_obj, size):
            t0 = time.monotonic_ns(); _dw(self, offset, memory_obj, size); t1 = time.monotonic_ns()
            d = {"ev": "dax.w", "dev": self.device_path, "off": offset, "n": size, "t0": t0, "dt": t1 - t0}
            if _VERIFY: d["sha1"] = hashlib.sha1(ctypes.string_at(memory_obj.data_ptr, size)).hexdigest()
            _w(d)
        def _do_read(self, offset, memory_obj, size):
            t0 = time.monotonic_ns(); _dr(self, offset, memory_obj, size); t1 = time.monotonic_ns()
            _w({"ev": "dax.r", "dev": self.device_path, "off": offset, "n": size, "t0": t0, "dt": t1 - t0})
        _dc.DaxCore._default_do_write = _do_write; _dc.DaxCore._default_do_read = _do_read
    except Exception as e: _w({"ev": "kvtier.warn", "what": f"DaxCore hook: {e!r}"})
    try:
        from lmcache.v1.distributed.l2_adapters import fs_l2_adapter as _fs
        _fr, _fw = _fs.FSL2Adapter._read_with_odirect, _fs.FSL2Adapter._write_with_odirect
        def _read_od(self, file_path, dst_buf, *a, **kw):
            t0 = time.monotonic_ns(); r = _fr(self, file_path, dst_buf, *a, **kw); t1 = time.monotonic_ns()
            try: n = len(memoryview(dst_buf).cast("B"))
            except Exception: n = -1
            _w({"ev": "fs.r", "f": os.path.basename(str(file_path)), "n": n, "t0": t0, "dt": t1 - t0}); return r
        def _write_od(self, file_path, buf, *a, **kw):
            t0 = time.monotonic_ns(); r = _fw(self, file_path, buf, *a, **kw); t1 = time.monotonic_ns()
            try: n = len(memoryview(buf).cast("B"))
            except Exception: n = -1
            _w({"ev": "fs.w", "f": os.path.basename(str(file_path)), "n": n, "t0": t0, "dt": t1 - t0}); return r
        _fs.FSL2Adapter._read_with_odirect = _read_od; _fs.FSL2Adapter._write_with_odirect = _write_od
    except Exception as e: _w({"ev": "kvtier.warn", "what": f"FSL2Adapter hook: {e!r}"})

    # ---- 3. Device-DAX L1 arenas: CUDA registration, further devices, sampled object hashes
    try:
        from lmcache.v1.memory_allocators import devdax_memory_allocator as _da
        _reg = _da.DevDaxMemoryAllocator._register_arena_pin
        _NO_PIN = os.environ.get("KVTIER_NO_PIN") == "1"
        def _register(self, arena):
            # KVTIER_NO_PIN=1 is the one switch of this module that changes behaviour, for a labelled experiment variant only: the
            # Device-DAX arenas are NOT registered with CUDA (no GPU memory spent on them; the GPU copies then go through the
            # driver's pageable path), which is what LMCache itself does when the registration fails.
            if not _NO_PIN: _reg(self, arena)
            _w({"ev": "l1dax.arena", "t": time.time(), "dev": arena.device_path, "size": arena.size, "pinned": arena.pinned_ptr is not None, "base": arena.buffer.data_ptr()})
        _da.DevDaxMemoryAllocator._register_arena_pin = _register
        if _VERIFY:
            _pend = []; _plock = threading.Lock(); _seen = {"n": 0}
            def _note(self, objs):
                try:
                    for o in objs:
                        _seen["n"] += 1
                        if _seen["n"] % 4 != 1 or not self.is_devdax_obj(o): continue      # every fourth allocation
                        with self.host_mem_lock: a = self._arena_for_obj_locked(o)
                        with _plock: _pend.append((time.monotonic() + 3.0, a.device_path, o.data_ptr - a.buffer.data_ptr(), o.data_ptr, o.get_physical_size()))
                except Exception as e: _w({"ev": "kvtier.warn", "what": f"l1dax note: {e!r}"})
            _a1, _a2 = _da.DevDaxMemoryAllocator._allocate_from_arenas, _da.DevDaxMemoryAllocator._batched_allocate_from_arenas
            def _alloc1(self, *a, **kw):
                o = _a1(self, *a, **kw)
                if o is not None: _note(self, [o])
                return o
            def _alloc2(self, *a, **kw):
                os_ = _a2(self, *a, **kw)
                if os_: _note(self, os_)
                return os_
            _da.DevDaxMemoryAllocator._allocate_from_arenas = _alloc1; _da.DevDaxMemoryAllocator._batched_allocate_from_arenas = _alloc2
            def _hash_loop():
                while True:
                    time.sleep(0.5); now = time.monotonic(); due = []
                    with _plock:
                        while _pend and _pend[0][0] <= now: due.append(_pend.pop(0))
                    for _, dev, off, ptr, n in due:
                        try: _w({"ev": "l1dax.obj", "t": time.time(), "dev": dev, "off": off, "n": n, "sha1": hashlib.sha1(ctypes.string_at(ptr, n)).hexdigest()})
                        except Exception as e: _w({"ev": "kvtier.warn", "what": f"l1dax hash: {e!r}"})
            threading.Thread(target=_hash_loop, daemon=True).start()
        _extra = os.environ.get("KVTIER_L1_EXTRA_DAX", "")
        if _extra:
            from lmcache.v1.distributed.memory_manager import devdax_l1_memory_manager as _dm
            _mi = _dm.DevDaxL1MemoryManager.__init__
            def _mgr_init(self, *a, **kw):
                _mi(self, *a, **kw)
                for item in _extra.split(","):
                    dev, gib = item.rsplit(":", 1)
                    st = self.add_device(dev, int(float(gib) * (1 << 30)))
                    _w({"ev": "l1dax.add", "t": time.time(), "dev": dev, "gib": float(gib), "status": str(st)[:300]})
            _dm.DevDaxL1MemoryManager.__init__ = _mgr_init
    except Exception as e: _w({"ev": "kvtier.warn", "what": f"devdax L1 hook: {e!r}"})

    # ---- 4. 1 Hz sampler: process and system memory, block-device counters
    _DISK = os.environ.get("KVTIER_DISK", "nvme1n1")
    def _sample_loop():
        while True:
            d = {"ev": "mem", "t": time.time(), "tm": time.monotonic_ns(), "pid": os.getpid(), "cpu": time.process_time_ns()}
            try:
                for l in open("/proc/self/status"):
                    k = l.split(":")[0]
                    if k in ("VmRSS", "RssAnon", "RssFile", "RssShmem", "VmLck", "VmPin"): d[k] = int(l.split()[1])
                for l in open("/proc/meminfo"):
                    k = l.split(":")[0]
                    if k in ("MemFree", "MemAvailable", "Cached", "Shmem", "Dirty", "Writeback", "Mlocked", "Unevictable"): d[k] = int(l.split()[1])
                for l in open("/proc/diskstats"):
                    p = l.split()
                    if p[2] == _DISK: d.update(rd_ios=int(p[3]), rd_sec=int(p[5]), wr_ios=int(p[7]), wr_sec=int(p[9]), io_ms=int(p[12]))
            except Exception as e: d["err"] = repr(e)
            _w(d); time.sleep(1.0)
    threading.Thread(target=_sample_loop, daemon=True).start()
