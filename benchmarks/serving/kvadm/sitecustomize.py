"""GPU-KV admission instrumentation for vLLM 0.31.0 + LMCache 0.5.5 (2026-11-10 study, Experiment A2).

Loaded through PYTHONPATH instead of benchmarks/serving/vllmevt (serving_env.py: adm=true). It first loads the
2026-11-04 logging hooks unchanged (vllmevt/sitecustomize.py: the "req" and "step" streams), then adds a third
stream `$VLLMEVT_OUT.adm.<pid>.jsonl` written by the EngineCore process. Logging only: every wrapper calls the
original function with the original arguments and returns its result; nothing in vLLM's or LMCache's decisions changes
unless a KVADM_* policy flag is set (kvadm_policy.py, Experiment B; absent flags = stock behaviour).

Events (t = time.monotonic() of the EngineCore, i = index of the schedule() call, identical to "i" of the step stream):
  {"ev":"poll","t","i","rid","loc","ext","as"}
        one call of connector.get_num_new_matched_tokens = one visit of a waiting request that has no computed tokens:
        loc = block-aligned local (GPU prefix cache) hit presented to the connector; ext = None while the LMCache lookup
        is pending (vLLM then skips the request and scans on), else the external tokens to load; as = async load.
  {"ev":"adm","t","i","rid","st","comp","ntok","new","loc","ext","as","resv","free","full","now","ok","gate","infl"}
        one KVCacheManager.allocate_slots call for a request that is not RUNNING = one admission attempt of the waiting
        loop (first admission of a miss or of an external load; promotion of a request whose load has arrived, comp > 0).
        st = request status (W waiting, P preempted); comp = request.num_computed_tokens before the call; ntok = tokens
        of the full sequence; new = tokens to compute in this step (0 for an async load); loc / ext = local and external
        hit tokens adopted by this call; resv = reserved_blocks passed by the scheduler (in-flight prefill reservation,
        non-zero only for async loads); free = free GPU KV blocks before the call; full = blocks the full sequence
        still needs (the scheduler_reserve_full_isl gate: full <= free); now = blocks this call allocates (gate:
        now <= free - resv); ok = allocated; gate = "ok" | "full" (full-sequence gate failed) | "resv" (fits in free
        but not in free - resv) | "free" (does not fit in the free blocks at all); infl = in-flight prefills.
        A failed attempt ends the waiting-queue scan of that step (the scheduler breaks).
  {"ev":"runfail","t","i","rid","new","free","now"}   a RUNNING request could not get the blocks of its next chunk
  {"ev":"preempt","t","i","rid","comp","ntok"}        Scheduler._preempt_request
  {"ev":"kv","i","t0","t1","free0","free1","tot","run","wait","hold","wfr","wfrb","infl","resv","runn","runtok",
   "tok","dfree","head","hhead"}
        one line per schedule(): free blocks before / after, pool size, queue lengths (running, waiting, kv-holding),
        requests in WAITING_FOR_REMOTE_KVS and the blocks they hold, in-flight prefills and their remaining-block
        reservation after this schedule(), RUNNING requests served in the running loop and their tokens (the token
        budget left for the waiting loop is max_num_scheduled_tokens - runtok), tokens scheduled in the step, blocks
        in the deferred-free list, and the request ids at the head of the waiting / kv-holding queues afterwards.
"""
import importlib.util, json, os, sys, time

_HERE = os.path.dirname(os.path.abspath(__file__))
_base_path = os.path.join(os.path.dirname(_HERE), "vllmevt", "sitecustomize.py")
_spec = importlib.util.spec_from_file_location("vllmevt_base", _base_path)
_base = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_base)

if os.environ.get("VLLMEVT_OUT") and hasattr(_base, "_TARGETS"):
    _w = _base._w
    _ctx = {"i": 0, "sched": None, "runtok": 0, "runn": 0, "conn_wrapped": False}
    try:
        sys.path.insert(0, _HERE)
        import kvadm_policy as _pol
        if not _pol.P: _pol = None       # no KVADM_POLICY: instrumentation only, stock decisions
    except Exception as e:           # no policy module or import error: instrumentation only
        _pol = None
        if os.environ.get("KVADM_POLICY"): sys.stderr.write(f"kvadm: policy module failed to load: {e!r}\n")

    def _patch_scheduler_adm(m):
        S = m.Scheduler; RS = m.RequestStatus
        from vllm.v1.core.kv_cache_manager import KVCacheManager
        ST = {RS.WAITING: "W", RS.PREEMPTED: "P", RS.RUNNING: "R", RS.WAITING_FOR_REMOTE_KVS: "K"}
        orig_alloc = KVCacheManager.allocate_slots

        def _needs(self, request, new, loc, ncb_obj, look, ext, enc):
            ncb = ncb_obj.blocks if ncb_obj is not None else self.empty_kv_cache_blocks.blocks
            num_local = request.num_computed_tokens + loc
            total = min(num_local + ext, self.max_model_len)
            prefill_end = max(request.num_prompt_tokens, request.num_tokens - 1)
            full_num = min(request.num_tokens, self.max_model_len)
            co = self.coordinator
            full = co.get_num_blocks_to_allocate(request_id=request.request_id, num_tokens=full_num, new_computed_blocks=ncb, num_encoder_tokens=enc,
                                                 total_computed_tokens=total, num_local_computed_tokens=num_local, num_tokens_main_model=full_num,
                                                 apply_admission_cap=True, prefill_end=prefill_end)
            main = total + new; slot = min(main + look, self.max_model_len)
            now = co.get_num_blocks_to_allocate(request_id=request.request_id, num_tokens=slot, new_computed_blocks=ncb, num_encoder_tokens=enc,
                                                total_computed_tokens=num_local + ext, num_local_computed_tokens=num_local, num_tokens_main_model=main,
                                                prefill_end=prefill_end)
            return full, now

        def allocate_slots(self, request, num_new_tokens, num_new_computed_tokens=0, new_computed_blocks=None, num_lookahead_tokens=0,
                           num_external_computed_tokens=0, delay_cache_blocks=False, num_encoder_tokens=0, full_sequence_must_fit=False,
                           reserved_blocks=0, has_scheduled_reqs=True):
            st = request.status; t = time.monotonic(); full = now = None
            try:
                free0 = self.block_pool.get_num_free_blocks()
                if st != RS.RUNNING:
                    full, now = _needs(self, request, num_new_tokens, num_new_computed_tokens, new_computed_blocks, num_lookahead_tokens,
                                       num_external_computed_tokens, num_encoder_tokens)
                comp0 = request.num_computed_tokens
            except Exception as e:
                free0 = -1; comp0 = -1; sys.stderr.write(f"kvadm pre: {e!r}\n")
            if _pol is not None and st != RS.RUNNING:
                try: reserved_blocks = _pol.adjust_reserved(_ctx, self, request, reserved_blocks, bool(delay_cache_blocks), full, now, free0)
                except Exception as e: sys.stderr.write(f"kvadm policy reserved: {e!r}\n")
            out = orig_alloc(self, request, num_new_tokens, num_new_computed_tokens=num_new_computed_tokens, new_computed_blocks=new_computed_blocks,
                             num_lookahead_tokens=num_lookahead_tokens, num_external_computed_tokens=num_external_computed_tokens,
                             delay_cache_blocks=delay_cache_blocks, num_encoder_tokens=num_encoder_tokens, full_sequence_must_fit=full_sequence_must_fit,
                             reserved_blocks=reserved_blocks, has_scheduled_reqs=has_scheduled_reqs)
            try:
                if st == RS.RUNNING:
                    if out is None:
                        try: _, now = _needs(self, request, num_new_tokens, 0, None, num_lookahead_tokens, 0, 0)
                        except Exception: now = None
                        _w("adm").write({"ev": "runfail", "t": t, "i": _ctx["i"], "rid": request.request_id, "new": num_new_tokens, "free": free0, "now": now})
                    else: _ctx["runtok"] += num_new_tokens; _ctx["runn"] += 1
                else:
                    wm = self.watermark_blocks if has_scheduled_reqs else 0
                    if out is not None: gate = "ok"
                    elif full_sequence_must_fit and full is not None and full + wm > free0: gate = "full"
                    elif now is not None and now + wm > free0: gate = "free"
                    elif now is not None and now + wm > free0 - reserved_blocks: gate = "resv"
                    else: gate = "?"
                    sch = _ctx["sched"]
                    _w("adm").write({"ev": "adm", "t": t, "i": _ctx["i"], "rid": request.request_id, "st": ST.get(st, str(st)), "comp": comp0, "ntok": request.num_tokens,
                                     "new": num_new_tokens, "loc": num_new_computed_tokens, "ext": num_external_computed_tokens, "as": bool(delay_cache_blocks),
                                     "resv": reserved_blocks, "free": free0, "full": full, "now": now, "ok": out is not None, "gate": gate,
                                     "infl": len(sch._inflight_prefills) if sch is not None else None})
                    if _pol is not None: _pol.after_attempt(_ctx, self, request, out is not None, gate, bool(delay_cache_blocks), full, now, free0, num_new_tokens)
            except Exception as e:
                sys.stderr.write(f"kvadm adm: {e!r}\n")
            return out
        KVCacheManager.allocate_slots = allocate_slots

        orig_preempt = S._preempt_request
        def _preempt_request(self, request, *a, **k):
            try: _w("adm").write({"ev": "preempt", "t": time.monotonic(), "i": _ctx["i"], "rid": request.request_id, "comp": request.num_computed_tokens, "ntok": request.num_tokens})
            except Exception as e: sys.stderr.write(f"kvadm preempt: {e!r}\n")
            return orig_preempt(self, request, *a, **k)
        S._preempt_request = _preempt_request

        def _wrap_connector(sched):
            conn = sched.connector
            if conn is None: return
            orig = conn.get_num_new_matched_tokens
            def get_num_new_matched_tokens(request, num_computed_tokens):
                r = orig(request, num_computed_tokens); act = None
                try:
                    if _pol is not None:
                        raw = r; r, act = _pol.on_lookup(_ctx, sched, conn, request, num_computed_tokens, r)
                    d = {"ev": "poll", "t": time.monotonic(), "i": _ctx["i"], "rid": request.request_id, "loc": num_computed_tokens, "ext": r[0], "as": bool(r[1])}
                    if act is not None: d["act"] = act; d["raw"] = raw[0]
                    _w("adm").write(d)
                except Exception as e: sys.stderr.write(f"kvadm poll: {e!r}\n")
                return r
            conn.get_num_new_matched_tokens = get_num_new_matched_tokens

        prev_schedule = S.schedule            # already wrapped by the base hook (step stream)
        def schedule(self, *a, **k):
            _ctx["sched"] = self; _ctx["i"] += 1; _ctx["runtok"] = 0; _ctx["runn"] = 0
            if not _ctx["conn_wrapped"]:
                _ctx["conn_wrapped"] = True
                try: _wrap_connector(self)
                except Exception as e: sys.stderr.write(f"kvadm connector wrap: {e!r}\n")
                if _pol is not None:
                    try: _pol.init(_ctx, self, _w)
                    except Exception as e: sys.stderr.write(f"kvadm policy init: {e!r}\n")
            try: bp = self.kv_cache_manager.block_pool; f0 = bp.get_num_free_blocks()
            except Exception: bp = None; f0 = -1
            if _pol is not None:
                try: _pol.before_schedule(_ctx, self)
                except Exception as e: sys.stderr.write(f"kvadm policy before: {e!r}\n")
            t0 = time.monotonic(); out = prev_schedule(self, *a, **k); t1 = time.monotonic()
            try:
                wfr = 0; wfrb = 0
                for r in self.kv_holding_waiting:
                    if r.status == RS.WAITING_FOR_REMOTE_KVS:
                        wfr += 1; wfrb += -(-r.num_computed_tokens // self.block_size)
                infl = self._inflight_prefills
                _w("adm").write({"ev": "kv", "i": _ctx["i"], "t0": t0, "t1": t1, "free0": f0, "free1": bp.get_num_free_blocks() if bp is not None else -1,
                                 "tot": bp.num_gpu_blocks if bp is not None else -1, "run": len(self.running), "wait": len(self.waiting), "hold": len(self.kv_holding_waiting),
                                 "wfr": wfr, "wfrb": wfrb, "infl": len(infl), "resv": self._inflight_prefill_reserved_blocks() if infl else 0,
                                 "runn": _ctx["runn"], "runtok": _ctx["runtok"], "tok": out.total_num_scheduled_tokens,
                                 "dfree": sum(len(b) for _, b in self.deferred_frees) if self.deferred_frees else 0,
                                 "head": self.waiting.peek_request().request_id if self.waiting else None,
                                 "hhead": self.kv_holding_waiting.peek_request().request_id if self.kv_holding_waiting else None})
            except Exception as e:
                sys.stderr.write(f"kvadm kv: {e!r}\n")
            return out
        S.schedule = schedule

    _name = "vllm.v1.core.sched.scheduler"; _prev = _base._TARGETS[_name]
    def _both(m):
        _prev(m); _patch_scheduler_adm(m)
    _base._TARGETS[_name] = _both
