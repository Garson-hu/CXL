"""Logging-only instrumentation of the LMCache 0.5.5 cache server (RQ1-B agent validation, 2026-10-17).

Loaded through PYTHONPATH by the `lmcache server` process only (Python imports `sitecustomize` at start-up). It wraps
lmcache.v1.mp_observability.config.init_observability so that one more subscriber sits on LMCache's own event bus and
appends one JSON line per event to $KVEVT_OUT. Nothing else is touched: no cache placement, eviction, admission or
transfer code path changes; the events below are the ones LMCache already publishes (some, like MP_LOOKUP and
L1_KEYS_ACCESSED, are only published when a subscriber exists, which this one is).

Line format: {"ev": <event type value>, "t": <time.time() at publish>, "sid": <session/request id>, ...metadata}
  keys         -> list of chunk-hash hex strings (ObjectKey.chunk_hash; "/<group>" appended for object group != 0)
  chunk_hashes -> "hashes": list of hex strings (MP_LOOKUP: the request's prefix chunks, in order)
  other metadata values are kept when scalar, stringified otherwise; "meta", "dtypes", "shapes" are dropped.
Remove the PYTHONPATH entry (or unset KVEVT_OUT) and the server is unmodified."""
import json, os, threading, time

if os.environ.get("KVEVT_OUT"):
    import lmcache.v1.mp_observability.config as _cfg
    from lmcache.v1.mp_observability.event import EventType
    from lmcache.v1.mp_observability.event_bus import EventSubscriber

    _WANT = ("MP_LOOKUP", "MP_LOOKUP_PREFETCH_START", "MP_LOOKUP_PREFETCH_END", "MP_REQUEST_START", "MP_REQUEST_END",
             "MP_VLLM_END_SESSION", "MP_STORE_START", "MP_STORE_END", "MP_RETRIEVE_START", "MP_RETRIEVE_END",
             "L1_WRITE_RESERVED", "L1_WRITE_FINISHED", "L1_WRITE_FINISHED_AND_READ_RESERVED", "L1_READ_RESERVED",
             "L1_READ_FINISHED", "L1_KEYS_EVICTED", "L1_KEYS_ACCESSED", "L1_ALLOCATION_FAILED", "L1_EVICTION_LOOP_TICK")

    def _hx(h):
        if isinstance(h, (bytes, bytearray)): return h.hex().lstrip("0") or "0"
        if isinstance(h, int): return format(h, "x")
        return str(h)

    def _key(k):
        h = getattr(k, "chunk_hash", None); s = _hx(h) if h is not None else str(k)
        g = getattr(k, "object_group_id", 0)
        return s if not g else f"{s}/{g}"

    class _KvEvt(EventSubscriber):
        def __init__(self, path):
            self.f = open(path, "a", buffering=1); self.lock = threading.Lock()
            self.f.write(json.dumps({"ev": "kvevt.start", "t": time.time(), "pid": os.getpid()}) + "\n")
        def get_subscriptions(self):
            return {getattr(EventType, n): self._on for n in _WANT if hasattr(EventType, n)}
        def _on(self, ev):
            d = {"ev": ev.event_type.value, "t": ev.timestamp or time.time(), "sid": ev.session_id}
            for k, v in (ev.metadata or {}).items():
                if k == "keys": d["keys"] = [_key(x) for x in v]
                elif k == "chunk_hashes": d["hashes"] = [_hx(x) for x in v]
                elif k in ("meta", "dtypes", "shapes"): continue
                elif isinstance(v, (int, float, str, bool)) or v is None: d[k] = v
                else: d[k] = str(v)[:200]
            line = json.dumps(d) + "\n"
            with self.lock: self.f.write(line)
        def shutdown(self):
            with self.lock: self.f.write(json.dumps({"ev": "kvevt.stop", "t": time.time()}) + "\n"); self.f.close()

    _orig = _cfg.init_observability
    def init_observability(*a, **kw):
        bus = _orig(*a, **kw); bus.register_subscriber(_KvEvt(os.environ["KVEVT_OUT"])); return bus
    _cfg.init_observability = init_observability
