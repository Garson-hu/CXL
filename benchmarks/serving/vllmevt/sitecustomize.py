"""Logging-only instrumentation of vLLM 0.31.0 for the 2026-11-04 serving-scheduling study.

Loaded through PYTHONPATH into every vLLM process (API server and EngineCore; Python imports `sitecustomize` at
start-up). It installs a post-import hook that wraps two methods once their modules are imported; nothing is
changed in vLLM's behaviour, the wrappers only append JSON lines to `$VLLMEVT_OUT.<kind>.<pid>.jsonl`:

  kind "req"  (API-server process; OutputProcessor._update_stats_from_finished, one line per finished request):
        rid = the external request id (the client's X-Request-Id, as vLLM names the request), irid = internal id,
        arrival_wall (frontend wall clock), queued_mono / scheduled_mono / first_token_mono / last_token_mono
        (EngineCore time.monotonic(); scheduled = the first step the request was scheduled for computation, i.e.
        AFTER an asynchronous KV load), prompt_tokens, cached_tokens (vLLM's count: local prefix cache + external),
        gen_tokens, preemptions, finish reason.
  kind "step" (EngineCore process; Scheduler.schedule and Scheduler.update_from_output, one line per engine step):
        {"ev":"step", i, t0, t1 (monotonic before / after schedule()), tok (scheduled tokens), new, cached (requests
        scheduled), run / wait / hold / wfr (running, waiting, kv-holding-waiting queue lengths and the number of
        requests in WAITING_FOR_REMOTE_KVS after this schedule()), fin (finished ids)}
        {"ev":"end", i, t (monotonic when the model output of step i was received; i is the index of the completed
        step, which with async scheduling is one behind the last schedule()), fr: ids whose asynchronous KV load the
        worker reported finished in this step}
        {"ev":"req", rid, kv_wait_mono (first schedule() that left the request in WAITING_FOR_REMOTE_KVS),
        kv_arrived_mono (the update_from_output that received its finished load), run_mono (first schedule() that
        put it in RUNNING)}  -- written when the request finishes.
Every file starts with {"ev":"vllmevt.start", pid, t_wall, t_mono}: wall = mono + (t_wall - t_mono) on this host.
Remove the PYTHONPATH entry (or unset VLLMEVT_OUT) and vLLM is unmodified."""
import atexit, importlib.abc, importlib.util, json, os, sys, threading, time

_OUT = os.environ.get("VLLMEVT_OUT")
if _OUT:
    class _Writer:
        def __init__(self, kind):
            self.f = open(f"{_OUT}.{kind}.{os.getpid()}.jsonl", "a", buffering=1 << 16); self.lock = threading.Lock(); self.n = 0
            self.write({"ev": "vllmevt.start", "kind": kind, "pid": os.getpid(), "t_wall": time.time(), "t_mono": time.monotonic()})
            atexit.register(self.close)
        def write(self, d):
            line = json.dumps(d, separators=(",", ":")) + "\n"
            with self.lock:
                self.f.write(line); self.n += 1
                if self.n % 20 == 0: self.f.flush()
        def close(self):
            with self.lock:
                try: self.f.flush(); self.f.close()
                except Exception: pass
    _writers = {}
    def _w(kind):
        if kind not in _writers: _writers[kind] = _Writer(kind)
        return _writers[kind]

    def _patch_output_processor(m):
        OP = m.OutputProcessor; orig = OP._update_stats_from_finished
        def _update_stats_from_finished(self, req_state, finish_reason, iteration_stats):
            try:
                st = req_state.stats
                _w("req").write({"ev": "finished", "rid": req_state.external_req_id, "irid": req_state.request_id,
                                 "arrival_wall": getattr(st, "arrival_time", None), "queued_mono": getattr(st, "queued_ts", None),
                                 "scheduled_mono": getattr(st, "scheduled_ts", None), "first_token_mono": getattr(st, "first_token_ts", None),
                                 "last_token_mono": getattr(st, "last_token_ts", None), "prompt_tokens": req_state.prompt_len,
                                 "cached_tokens": getattr(req_state, "num_cached_tokens", None),
                                 "gen_tokens": getattr(st, "num_generation_tokens", None), "preemptions": getattr(st, "num_preemptions", None),
                                 "finish": str(finish_reason), "t_wall": time.time()})
            except Exception as e:
                sys.stderr.write(f"vllmevt req: {e!r}\n")
            return orig(self, req_state, finish_reason, iteration_stats)
        OP._update_stats_from_finished = _update_stats_from_finished

    def _patch_scheduler(m):
        S = m.Scheduler; RS = m.RequestStatus
        orig_schedule, orig_update = S.schedule, S.update_from_output
        st = {"i": 0, "wait": {}, "arrived": {}, "run": {}}
        def schedule(self, *a, **k):
            t0 = time.monotonic(); out = orig_schedule(self, *a, **k); t1 = time.monotonic()
            try:
                st["i"] += 1; i = st["i"]; n_wfr = 0
                try: out._vllmevt_i = i          # so that update_from_output can name the step it completes (async scheduling runs one step ahead)
                except Exception: pass
                for rid, r in self.requests.items():
                    s = r.status
                    if s == RS.WAITING_FOR_REMOTE_KVS:
                        n_wfr += 1
                        if rid not in st["wait"]: st["wait"][rid] = t1
                    elif s == RS.RUNNING and rid not in st["run"]: st["run"][rid] = t1
                fin = out.finished_req_ids or ()
                for rid in fin:
                    d = {"ev": "req", "rid": rid, "kv_wait_mono": st["wait"].pop(rid, None), "kv_arrived_mono": st["arrived"].pop(rid, None), "run_mono": st["run"].pop(rid, None)}
                    if d["kv_wait_mono"] is not None or d["run_mono"] is not None: _w("step").write(d)
                cached = out.scheduled_cached_reqs
                _w("step").write({"ev": "step", "i": i, "t0": t0, "t1": t1, "tok": out.total_num_scheduled_tokens, "new": len(out.scheduled_new_reqs),
                                  "cached": len(getattr(cached, "req_ids", ()) or ()), "run": len(self.running), "wait": len(self.waiting),
                                  "hold": len(self.kv_holding_waiting), "wfr": n_wfr, "fin": len(fin)})
            except Exception as e:
                sys.stderr.write(f"vllmevt step: {e!r}\n")
            return out
        def update_from_output(self, scheduler_output, model_runner_output, *a, **k):
            t = time.monotonic(); fr = ()
            try:
                kvo = getattr(model_runner_output, "kv_connector_output", None)
                fr = tuple(getattr(kvo, "finished_recving", None) or ()) if kvo is not None else ()
                for rid in fr: st["arrived"].setdefault(rid, t)
                _w("step").write({"ev": "end", "i": getattr(scheduler_output, "_vllmevt_i", st["i"]), "t": t, "fr": list(fr)})
            except Exception as e:
                sys.stderr.write(f"vllmevt end: {e!r}\n")
            return orig_update(self, scheduler_output, model_runner_output, *a, **k)
        S.schedule = schedule; S.update_from_output = update_from_output

    _TARGETS = {"vllm.v1.engine.output_processor": _patch_output_processor, "vllm.v1.core.sched.scheduler": _patch_scheduler}

    class _PostImport(importlib.abc.MetaPathFinder):
        def __init__(self): self.busy = set()
        def find_spec(self, name, path, target=None):
            if name not in _TARGETS or name in self.busy: return None
            self.busy.add(name)
            try: spec = importlib.util.find_spec(name)
            finally: self.busy.discard(name)
            if spec is None or spec.loader is None or not hasattr(spec.loader, "exec_module"): return None
            loader, fn = spec.loader, _TARGETS[name]; orig_exec = loader.exec_module
            def exec_module(module):
                orig_exec(module)
                try: fn(module)
                except Exception as e: sys.stderr.write(f"vllmevt: patch of {name} failed: {e!r}\n")
            loader.exec_module = exec_module
            return spec
    sys.meta_path.insert(0, _PostImport())
