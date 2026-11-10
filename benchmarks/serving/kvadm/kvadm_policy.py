"""Flag-gated admission prototypes for vLLM 0.31.0 + LMCache 0.5.5 (2026-11-10 study, Experiment B).

Nothing here patches vLLM or LMCache source: the mechanisms act through three existing interfaces, wrapped by
kvadm/sitecustomize.py in the EngineCore process —
  (1) the connector's answer to the scheduler (get_num_new_matched_tokens): returning (None, True) makes the stock
      scheduler skip a waiting request for this step and scan on (what it does for a pending lookup); returning (0, False)
      makes it compute the prompt instead of loading it;
  (2) the reserved_blocks argument of KVCacheManager.allocate_slots (the stock in-flight reservation of async loads);
  (3) scheduler_config.long_prefill_token_threshold, the stock per-step cap of a prefill chunk, set before each schedule().
With KVADM_POLICY unset or empty every function returns its input: stock behaviour.

KVADM_POLICY = comma-separated mechanisms (vLLM process environment; serving_env.py: adm_env="KVADM_POLICY=...")
  storefix        undo the repeated addition of the hit length to the connector's num_stored_tokens when a waiting hit is
                  polled more than once (LMCache 0.5.5, lmcache_mp_connector.py:1065); implied by every mechanism below
                  that makes the scheduler poll a request again.
  alpha=<a>       scale the in-flight prefill reservation charged to an async load (stock = 1; 0 = a load is admitted
                  under the same block rule as a miss).
  tokres=<n>      token reserve for short work: when loads have arrived and wait for promotion, when short requests
                  (compute need <= n tokens) wait, or when unvisited requests wait, running long prefills are capped so
                  that up to n tokens of the step's budget are left for them (at most n; 1 token when only the scan is needed).
  fastchunk=<n>   with tokres: while short work is under way next to a long prefill (a lookup pending, a load in transfer or
                  arrived, a short tail running), the token budget of the whole step is n instead of the configured one, so
                  that the next step boundary -- where lookup results, finished loads and promotions are picked up -- comes
                  sooner; long prefills continue at what the short work leaves of n (at least mincap, default 128).
  fastmax=<s>     (default 1.5) a request counts as short work for the reserve and for short steps for at most s seconds per phase
                  (lookup, transfer, promotion): one that stays longer is waiting for memory, which neither helps.
  minchunk=<n>    do not start a compute request (miss, GPU-prefix hit) in a step that has fewer than min(its need, n)
                  budget tokens left (the stock scheduler starts it with whatever is left); default tokres + 256 when
                  tokres is set, so that the reserve cannot start a long prefill.
  skip=<s>        do not let a request that fails the block gates stop the scan: it is skipped (others behind it may be
                  admitted) until it has waited <s> seconds since its lookup result, after which stock behaviour returns
                  (its refusal stops the scan, i.e. freed blocks go to it first).
  hitres=<b>      bounded block reservation for skipped external hits: other compute requests are admitted only if they
                  leave min(b, blocks the pending hits need) free (needs skip).
  fallback=<s>    an external hit that still fails the block gates <s> seconds after its lookup result is computed
                  instead of loaded if the compute path passes the gates (needs storefix; implied).
Decisions are summarised per request in the admission stream: {"ev":"pol","rid","t0","t","skip_kv","skip_tok","fb"}.
"""
import os, sys, time

P = {}
for _item in filter(None, (os.environ.get("KVADM_POLICY") or "").split(",")):
    _k, _, _v = _item.strip().partition("=")
    P[_k] = float(_v) if _v else 1.0
if "tokres" in P and "minchunk" not in P: P["minchunk"] = P["tokres"] + 256
DECIDE = any(k in P for k in ("minchunk", "skip", "fallback"))            # mechanisms that change the connector's answer
ST = {"req": {}, "pending_hit": {}, "tm": {}, "capped": False, "mismatch": 0}

def needs(kvm, request, new, loc, ncb, look, ext, enc):
    """(blocks the full sequence still needs, blocks this allocation takes): the two gates of KVCacheManager.allocate_slots"""
    num_local = request.num_computed_tokens + loc
    total = min(num_local + ext, kvm.max_model_len)
    prefill_end = max(request.num_prompt_tokens, request.num_tokens - 1)
    full_num = min(request.num_tokens, kvm.max_model_len); co = kvm.coordinator
    full = co.get_num_blocks_to_allocate(request_id=request.request_id, num_tokens=full_num, new_computed_blocks=ncb, num_encoder_tokens=enc,
                                         total_computed_tokens=total, num_local_computed_tokens=num_local, num_tokens_main_model=full_num,
                                         apply_admission_cap=True, prefill_end=prefill_end)
    main = total + new; slot = min(main + look, kvm.max_model_len)
    now = co.get_num_blocks_to_allocate(request_id=request.request_id, num_tokens=slot, new_computed_blocks=ncb, num_encoder_tokens=enc,
                                        total_computed_tokens=num_local + ext, num_local_computed_tokens=num_local, num_tokens_main_model=main,
                                        prefill_end=prefill_end)
    return full, now

def init(ctx, sched, w):
    import vllm.v1.request as rq
    ST.update(w=w, B=sched.max_num_scheduled_tokens, orig_thr=sched.scheduler_config.long_prefill_token_threshold, bs=sched.block_size, RS=rq.RequestStatus)
    ctx["admtok"] = 0
    w("adm").write({"ev": "policy", "t": time.monotonic(), "flags": P, "budget": ST["B"], "orig_thr": ST["orig_thr"]})

def _storefix(conn, rid):
    try:
        tr = conn._get_request_tracker(rid)
        if tr.num_scheduled_tokens == 0 and tr.num_lmcache_hit_tokens > 0 and tr.num_stored_tokens != tr.num_lmcache_hit_tokens:
            tr.num_stored_tokens = tr.num_lmcache_hit_tokens
    except Exception as e: sys.stderr.write(f"kvadm storefix: {e!r}\n")

def _pending_reserve(exclude=None):
    if "hitres" not in P or not ST["pending_hit"]: return 0
    return int(min(P["hitres"], sum(v for k, v in ST["pending_hit"].items() if k != exclude)))

def before_schedule(ctx, sched):
    ctx["admtok"] = 0
    if not P: return
    RS = ST["RS"]; reqs = sched.requests
    if ST["pending_hit"]:
        for rid in [k for k in ST["pending_hit"] if k not in reqs or reqs[k].status != RS.WAITING]: ST["pending_hit"].pop(rid, None)
    if len(ST["req"]) > 2048:
        for rid in [k for k in ST["req"] if k not in reqs]: ST["req"].pop(rid, None)
    if "tokres" not in P: return
    B = ST["B"]; T = int(P["tokres"]); fin = sched.finished_recving_kv_req_ids
    now = time.monotonic(); TM = ST["tm"]; FMAX = P.get("fastmax", 1.5)
    def fresh(rid, phase):
        """a request counts as short work under way only for FMAX seconds per phase: one that stays longer is blocked by memory, not by
        the step length, and neither a token reserve nor short steps help it"""
        return now - TM.setdefault((rid, phase), now) < FMAX
    tails = 0; small = 0; scan = 0; urgent = False
    for r in sched.kv_holding_waiting:
        rid = r.request_id
        if r.status != RS.WAITING_FOR_REMOTE_KVS or rid in fin:      # a load that has arrived: its uncached tail
            if fresh(rid, "p"): tails += max(1, r.num_tokens - r.num_computed_tokens); urgent = True
            else: scan = 1
        elif fresh(rid, "t"): urgent = True                           # a load in transfer: its arrival is noticed at a step boundary
    for r in sched.waiting:
        rid = r.request_id; st = ST["req"].get(rid)
        if st is None:                                                # not looked up yet, or lookup pending
            scan = 1
            if fresh(rid, "u"): urgent = True
        elif st.get("kind") == "c" and st["need"] <= T and fresh(rid, "s"): small += st["need"]; urgent = True   # a short compute request
        else: scan = 1                                                # a long miss, or a request that waits for blocks: 1 token keeps the scan alive
    want = min(T, tails + small) or scan
    short = 0; n_long = 0; n_dec = 0
    for r in sched.running:
        rem = r.num_prompt_tokens - r.num_computed_tokens
        if rem <= 0: n_dec += 1
        elif rem <= T: short += rem
        else: n_long += 1
    thr = ST["orig_thr"]; bud = B
    fast = "fastchunk" in P and (urgent or short > 0)
    if n_long and (want or short or fast):
        # fast mode: while short work is under way the whole step is kept short, so that the next step boundary -- where lookup results,
        # finished loads and promotions are picked up -- comes sooner
        if fast: bud = min(B, int(P["fastchunk"]))
        thr = max(int(P.get("mincap", 128)), (bud - want - short - n_dec) // n_long)
    if sched.scheduler_config.long_prefill_token_threshold != thr: sched.scheduler_config.long_prefill_token_threshold = thr
    if sched.max_num_scheduled_tokens != bud: sched.max_num_scheduled_tokens = bud
    ST["capped"] = thr != ST["orig_thr"]; ST["bud"] = bud
    if len(TM) > 8192:
        for k in [k for k in TM if k[0] not in reqs]: TM.pop(k, None)

def on_lookup(ctx, sched, conn, request, loc, r):
    """called after the connector's own answer r = (ext, async); returns (answer, action or None)"""
    ext, is_async = r
    if not P or ext is None: return r, None
    rid = request.request_id; RS = ST["RS"]
    if ext > 0: _storefix(conn, rid)
    t = time.monotonic(); s = ST["req"].get(rid)
    if s is None: s = ST["req"][rid] = {"t0": t, "skip_kv": 0, "skip_tok": 0, "fb": False}
    if request.status == RS.PREEMPTED:                       # the connector answers (0, False): a preempted request is recomputed (stock)
        s["kind"] = "c"; s["need"] = request.num_tokens; return r, None
    if not DECIDE: return r, None
    if s["fb"]: return (0, False), "fallback"                # decided earlier: stays a compute request
    kvm = sched.kv_cache_manager; free = kvm.block_pool.get_num_free_blocks()
    left = ST.get("bud", ST["B"]) - ctx["runtok"] - ctx["admtok"]
    blocks_obj, nloc, _ = kvm.get_computed_blocks(request); ncb = blocks_obj.blocks
    need_all = max(1, request.num_tokens - nloc)             # tokens to compute if nothing is loaded
    age = t - s["t0"]
    if is_async and ext > 0:
        s["kind"] = "h"; s["need"] = max(1, request.num_tokens - nloc - ext)
        full, now = needs(kvm, request, 0, nloc, ncb, 0, ext, 0)
        resv = sched._inflight_prefill_reserved_blocks() + sched._spec_decode_step_blocks()
        if "alpha" in P: resv = int(P["alpha"] * resv)
        if full <= free and now <= free - resv:
            ST["pending_hit"].pop(rid, None); return r, None
        if "fallback" in P and age >= P["fallback"]:
            chunk = min(need_all, max(left, 1)); fullc, nowc = needs(kvm, request, chunk, nloc, ncb, 0, 0, 0)
            if fullc <= free and nowc <= free and left >= min(need_all, P.get("minchunk", 1)):
                s["fb"] = True; s["kind"] = "c"; s["need"] = need_all; ST["pending_hit"].pop(rid, None)
                return (0, False), "fallback"
        if "skip" in P and age < P["skip"]:
            s["skip_kv"] += 1; ST["pending_hit"][rid] = now; return (None, True), "skip_kv"
        ST["pending_hit"].pop(rid, None)
        return r, None                                       # stock: the allocation is refused and the scan stops at this request
    s["kind"] = "c"; s["need"] = need_all
    if "minchunk" in P and left < min(need_all, P["minchunk"]):
        s["skip_tok"] += 1; return (None, True), "skip_tok"
    if "skip" in P:
        chunk = min(need_all, max(left, 1)); full, now = needs(kvm, request, chunk, nloc, ncb, 0, 0, 0)
        R = _pending_reserve(exclude=rid)
        if not (full <= free - R and now <= free - R):
            if age < P["skip"]: s["skip_kv"] += 1; return (None, True), "skip_kv"
            s["nores"] = True                                # waited long enough: stock gates decide, without the hit reservation
    return r, None

def adjust_reserved(ctx, kvm, request, reserved_blocks, is_async, full, now, free0):
    if not P: return reserved_blocks
    if is_async:
        return int(P["alpha"] * reserved_blocks) if "alpha" in P else reserved_blocks
    if "hitres" in P and request.num_computed_tokens == 0 and not ST["req"].get(request.request_id, {}).get("nores"):
        return reserved_blocks + _pending_reserve(exclude=request.request_id)
    return reserved_blocks

def after_attempt(ctx, kvm, request, ok, gate, is_async, full, now, free0, num_new_tokens):
    if not P: return
    rid = request.request_id
    if ok:
        ctx["admtok"] = ctx.get("admtok", 0) + num_new_tokens
        if is_async: ST["pending_hit"].pop(rid, None)
        s = ST["req"].get(rid)
        if s is not None and not s.get("logged") and (s["skip_kv"] or s["skip_tok"] or s["fb"]):
            s["logged"] = True
            ST["w"]("adm").write({"ev": "pol", "rid": rid, "t0": s["t0"], "t": time.monotonic(), "skip_kv": s["skip_kv"], "skip_tok": s["skip_tok"], "fb": s["fb"]})
        if not is_async: ST["req"].pop(rid, None)
