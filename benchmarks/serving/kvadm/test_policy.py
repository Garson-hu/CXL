#!/usr/bin/env python3
"""Mock tests of kvadm_policy.py (2026-11-10 admission study): the module is driven with stand-ins for the scheduler, the KV cache
manager and the connector, one KVADM_POLICY at a time (a fresh interpreter per case, because the flags are read at import).
Checks: with no flags every hook returns its input; the token reserve caps a running long prefill and shortens the step while short
work is under way; minchunk sets a long compute request aside when the step has too little budget left; resvall sets a compute request
aside that does not fit under the in-flight reservation; skip sets a request aside that fails the block gates, for a bounded time;
the store-counter fix resets the connector's counter; agecap suspends everything while a long request has waited too long.
usage: test_policy.py [path of the directory that holds kvadm_policy.py]      (exit status 0 = all cases passed)"""
import os, subprocess, sys
HERE = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
CASE = r'''
import enum, sys, time, types
sys.path.insert(0, HERE)
class RS(enum.Enum): WAITING = 1; WAITING_FOR_REMOTE_KVS = 2; RUNNING = 3; PREEMPTED = 4
for name in ("vllm", "vllm.v1"): sys.modules[name] = types.ModuleType(name)
m = types.ModuleType("vllm.v1.request"); m.RequestStatus = RS; sys.modules["vllm.v1.request"] = m
import kvadm_policy as pol
class Req:
    def __init__(s, rid, ntok, comp=0, status=RS.WAITING, loc=0): s.request_id = rid; s.num_tokens = ntok; s.num_prompt_tokens = ntok; s.num_computed_tokens = comp; s.status = status; s.loc = loc
class Pool:
    def __init__(s, free): s.free = free
    def get_num_free_blocks(s): return s.free
class Coord:
    def get_num_blocks_to_allocate(s, request_id, num_tokens, new_computed_blocks, num_encoder_tokens, total_computed_tokens, num_local_computed_tokens, num_tokens_main_model, apply_admission_cap=False, prefill_end=0):
        return max(0, -(-num_tokens // 16) - num_local_computed_tokens // 16)
class KVM:
    def __init__(s, free): s.block_pool = Pool(free); s.coordinator = Coord(); s.max_model_len = 32768
    def get_computed_blocks(s, request): return types.SimpleNamespace(blocks=[]), request.loc, None
class Sched:
    def __init__(s, free=5000, resv=0):
        s.max_num_scheduled_tokens = 2048; s.scheduler_config = types.SimpleNamespace(long_prefill_token_threshold=0); s.block_size = 16
        s.requests = {}; s.waiting = []; s.kv_holding_waiting = []; s.running = []; s.finished_recving_kv_req_ids = set(); s.kv_cache_manager = KVM(free)
        s._inflight_prefills = set(); s._resv = resv
    def _inflight_prefill_reserved_blocks(s): return s._resv
    def _spec_decode_step_blocks(s): return 0
    def add(s, r, where): s.requests[r.request_id] = r; getattr(s, where).append(r); return r
class Tracker:
    def __init__(s): s.num_scheduled_tokens = 0; s.num_lmcache_hit_tokens = 1024; s.num_stored_tokens = 3072
class Conn:
    def __init__(s): s.tr = Tracker()
    def _get_request_tracker(s, rid): return s.tr
class W:
    def __init__(s): s.ev = []
    def __call__(s, kind): return s
    def write(s, d): s.ev.append(d)
def setup(free=5000, resv=0):
    sch = Sched(free, resv); ctx = {"i": 1, "runtok": 0, "admtok": 0}; w = W(); pol.init(ctx, sch, w); return sch, ctx, w, Conn()
def step(ctx, sch): ctx["i"] += 1; ctx["runtok"] = 0; pol.before_schedule(ctx, sch)
'''
TESTS = {
 "": r'''
sch, ctx, w, conn = setup(); long = sch.add(Req("L", 20000, comp=2048, status=RS.RUNNING), "running"); q = sch.add(Req("q", 6000), "waiting")
step(ctx, sch); assert sch.max_num_scheduled_tokens == 2048 and sch.scheduler_config.long_prefill_token_threshold == 0
assert pol.on_lookup(ctx, sch, conn, q, 0, (0, False)) == ((0, False), None) and conn.tr.num_stored_tokens == 3072
assert pol.adjust_reserved(ctx, sch.kv_cache_manager, q, 7, True, 1, 1, 1) == 7
''',
 "storefix": r'''
sch, ctx, w, conn = setup(); q = sch.add(Req("q", 6000, loc=1024), "waiting"); step(ctx, sch)
assert pol.on_lookup(ctx, sch, conn, q, 1024, (0, False)) == ((0, False), None) and conn.tr.num_stored_tokens == 1024      # counter reset to the hit length
assert sch.max_num_scheduled_tokens == 2048
''',
 "tokres=768,fastchunk=512": r'''
sch, ctx, w, conn = setup(); long = sch.add(Req("L", 20000, comp=2048, status=RS.RUNNING), "running")
step(ctx, sch); assert sch.max_num_scheduled_tokens == 2048 and sch.scheduler_config.long_prefill_token_threshold == 0      # nothing waits: stock step
q = sch.add(Req("q", 6000), "waiting"); step(ctx, sch)                                                                     # an unvisited request: short step, scan kept alive
assert sch.max_num_scheduled_tokens == 512 and sch.scheduler_config.long_prefill_token_threshold == 511, (sch.max_num_scheduled_tokens, sch.scheduler_config.long_prefill_token_threshold)
ctx["runtok"] = 511
r, act = pol.on_lookup(ctx, sch, conn, q, 0, (0, False)); assert (r, act) == ((None, True), "skip_tok"), (r, act)             # a long miss is not started with 1 token
for _ in range(6): step(ctx, sch)                                                                                           # it is long work: no short step for it any more
assert sch.max_num_scheduled_tokens == 2048 and sch.scheduler_config.long_prefill_token_threshold == 2047, (sch.max_num_scheduled_tokens, sch.scheduler_config.long_prefill_token_threshold)
h = sch.add(Req("h", 4352, loc=0), "waiting"); step(ctx, sch); ctx["runtok"] = 511
r, act = pol.on_lookup(ctx, sch, conn, h, 0, (4096, True)); assert (r, act) == ((4096, True), None), (r, act)                 # an external hit that fits is admitted in the short step
sch.waiting.remove(h); h.status = RS.WAITING_FOR_REMOTE_KVS; sch.kv_holding_waiting.append(h); step(ctx, sch)
assert sch.max_num_scheduled_tokens == 512                                                                                 # load in transfer: steps stay short
s = sch.add(Req("s", 600, loc=0), "waiting"); step(ctx, sch); ctx["runtok"] = 300
r, act = pol.on_lookup(ctx, sch, conn, s, 0, (0, False)); assert act == "skip_tok", act                                      # budget left 212 < its need 600 in this step
step(ctx, sch); ctx["runtok"] = 0
assert sch.max_num_scheduled_tokens >= 600 + 256, sch.max_num_scheduled_tokens                                              # now reserved for: room for it plus a slice of the prefill
r, act = pol.on_lookup(ctx, sch, conn, s, 0, (0, False)); assert (r, act) == ((0, False), None), (r, act)
''',
 "tokres=768,fastchunk=512,resvall": r'''
sch, ctx, w, conn = setup(free=1000, resv=900); sch._inflight_prefills = {"X"}                                              # a prefill in flight that still needs 900 blocks; full budget left in this step
s = sch.add(Req("s", 4000, loc=0), "waiting"); step(ctx, sch); ctx["runtok"] = 0
r, act = pol.on_lookup(ctx, sch, conn, s, 0, (0, False)); assert act == "skip_resv", act                                     # 250 blocks do not fit under free - reservation = 100
sch._resv = 0; r, act = pol.on_lookup(ctx, sch, conn, s, 0, (0, False)); assert act is None, act
''',
 "skip=3,hitres=600": r'''
sch, ctx, w, conn = setup(free=200); h = sch.add(Req("h", 4352, loc=0), "waiting"); step(ctx, sch)
r, act = pol.on_lookup(ctx, sch, conn, h, 0, (4096, True)); assert (r, act) == ((None, True), "skip_kv"), (r, act)            # needs 272 blocks, 200 free: set aside, scan goes on
c = sch.add(Req("c", 1600, loc=0), "waiting")
r, act = pol.on_lookup(ctx, sch, conn, c, 0, (0, False)); assert act == "skip_kv", act                                       # 100 blocks would leave fewer than the hit's reservation
sch.kv_cache_manager.block_pool.free = 500
r, act = pol.on_lookup(ctx, sch, conn, h, 0, (4096, True)); assert act is None, act                                          # the hit fits now
pol.ST["req"]["h"]["t0"] -= 10; sch.kv_cache_manager.block_pool.free = 200
r, act = pol.on_lookup(ctx, sch, conn, h, 0, (4096, True)); assert (r, act) == ((4096, True), None), (r, act)                 # waited longer than skip: stock answer (its refusal stops the scan)
''',
 "tokres=768,fastchunk=512,resvall,agecap=5": r'''
sch, ctx, w, conn = setup(); long = sch.add(Req("L", 20000, comp=2048, status=RS.RUNNING), "running"); q = sch.add(Req("q", 6000), "waiting")
step(ctx, sch); ctx["runtok"] = 511
r, act = pol.on_lookup(ctx, sch, conn, q, 0, (0, False)); assert act == "skip_tok" and not pol.ST["protect"]
step(ctx, sch); assert sch.scheduler_config.long_prefill_token_threshold != 0                                               # mechanisms active while the request is young
pol.ST["seen"]["q"] -= 6; step(ctx, sch)                                                                                    # it has now waited 6 s > agecap
assert pol.ST["protect"] and sch.max_num_scheduled_tokens == 2048 and sch.scheduler_config.long_prefill_token_threshold == 0
ctx["runtok"] = 2047
r, act = pol.on_lookup(ctx, sch, conn, q, 0, (0, False)); assert (r, act) == ((0, False), None), (r, act)                     # stock answer: it starts with whatever is left
assert pol.adjust_reserved(ctx, sch.kv_cache_manager, q, 7, True, 1, 1, 1) == 7
sch.waiting.remove(q); step(ctx, sch); assert not pol.ST["protect"]                                                         # admitted: mechanisms back on
assert [e["on"] for e in w.ev if e.get("ev") == "prot"] == [True, False], w.ev
''',
 "tokres=768,fastchunk=512,agecap=5 ": r'''
sch, ctx, w, conn = setup(); long = sch.add(Req("L", 20000, comp=2048, status=RS.RUNNING), "running"); s = sch.add(Req("s", 300), "waiting")
step(ctx, sch); ctx["runtok"] = 0; r, act = pol.on_lookup(ctx, sch, conn, s, 0, (0, False)); pol.ST["seen"]["s"] -= 60; pol.ST["req"]["s"] = {"t0": 0, "skip_kv": 0, "skip_tok": 0, "fb": False, "kind": "c", "need": 300}
step(ctx, sch); assert not pol.ST["protect"]                                                                               # short work never triggers the bound
''',
}
bad = 0
for flags, body in TESTS.items():
    env = dict(os.environ, KVADM_POLICY=flags.strip())
    r = subprocess.run([sys.executable, "-c", f"HERE = {HERE!r}\n" + CASE + body], env=env, capture_output=True, text=True)
    print(("ok  " if r.returncode == 0 else "FAIL"), repr(flags.strip() or "(no flags)"))
    if r.returncode: bad += 1; print(r.stderr[-1500:])
sys.exit(1 if bad else 0)
