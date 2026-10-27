#!/usr/bin/env python3
"""Admission simulator for the RQ1-B practical / adaptive / robust admission studies (2026-10-21).

Same cache semantics as scripts/kv_agent_replay.py (reproduced exactly for lru / slru / 2nd / lhd / oracle, see the
2026-10-21 reports, Task G): one host KV cache of `cap` blocks; LMCache / vLLM order (a request's blocks are touched
tail-first at request end, so the tail is evicted first); prefix-aware scoring (a hit is usable only while every
earlier block of the request hit); scored accesses = the requests in --score-range (default the second half; the
first half warms the cache and the online statistics); writes = admissions in the scored range; residence = write ->
eviction.
Features:
  * a BOUNDED ghost history (exact LRU of N entries, TTL, or a double-buffered Bloom filter) feeding the second-touch
    rules and the adaptive policies; the ghost stores past lookups only, never data; a ghost hit is an admission
    signal, never a KV hit;
  * the classic policies 2Q, ARC, TinyLFU admission (adapted: no window) and W-TinyLFU;
  * second touch (`2nd`), second touch + gap <= online residence (`2nd_int`), and `2nd_int_auto`: the same with an
    automatic regime switch to normal (first-touch) admission when the online statistics say filtering no longer pays
    (--regime res: the residence that admitting everything would give exceeds the q-quantile of the observed re-lookup
    gaps; --regime model: the predicted hit rate with first-touch admission exceeds the one without), with hysteresis;
  * `adapt2` / `adaptive`: class tables of POLICY-INDEPENDENT labels "looked up again within w" and a replanned
    threshold on P(re-lookup within the residence);
  * several online residence estimators computed side by side (--res-mode picks the one that drives the policy):
    evict = EWMA of eviction ages (1/200), evict50 / evict1000 = faster / slower EWMA, dead = EWMA of the ages of
    blocks evicted without a hit, rate = capacity / admission rate, tail = age of the current LRU tail, median = median
    of the last 200 eviction ages; --res-log writes their time series and the realized residence of admitted blocks;
  * CONSTRUCTED dynamic load: --churn R,A,B (SYNTHETIC never-reused 8-block requests, R blocks per second during the
    span fraction [A,B)), --thin F,A,B (drop a fraction F of the requests in [A,B));
  * an optional GPU front cache; walk-forward scoring ranges, cold start, freezing; --audit (prefix-semantics
    invariants); --dec-log (per-decision log of the gap rules with the block's future next-use gap for ACCOUNTING only).
Policies: lru slru 2q arc tinylfu wtinylfu 2nd 2nd_int 2nd_int_auto adapt2 adaptive lhd oracle
  + window-based reuse policies (2026-10-27 exploratory study, suffix ':W' = window in seconds): wslru:W (LRU with a protected segment for
    blocks with >= 2 accesses inside the last W s; protection expires after W s without access), wlfu:W (evict, among the K least recently
    used, the block with the fewest accesses in the last W s), wslru2nd:W / wlfu2nd:W (the same with admission only of blocks looked up
    within the last W s, first blocks of a request always admitted)
usage: kv_admission_sim.py <trace.jsonl> <out_dir> <tag> [--mooncake] [--caps 3200] [--policies ...] [options]"""
import argparse, collections, csv, hashlib, heapq, json, math, os, random
OD = collections.OrderedDict
ap = argparse.ArgumentParser()
ap.add_argument("trace"); ap.add_argument("out"); ap.add_argument("tag")
ap.add_argument("--caps", default="3200"); ap.add_argument("--chunk-mb", type=float, default=67.1); ap.add_argument("--tok", type=int, default=512)
ap.add_argument("--mooncake", action="store_true"); ap.add_argument("--policies", default="lru,2nd,oracle")
ap.add_argument("--score-range", default="0.5,1.0", help="fractions of the requests that are scored (walk-forward: tune on 0.25,0.5 and test on 0.5,1.0)")
ap.add_argument("--ghost", default="inf", help="ghost history entries: 'inf' (unbounded), an integer, or a multiple of the capacity like '0.5c'")
ap.add_argument("--ghost-ttl", type=float, default=0.0, help="ghost entries older than this many seconds are forgotten (0 = never)")
ap.add_argument("--ghost-bloom", default="", help="double-buffered Bloom filter instead of the exact ghost: 'bits,k,reset_after_inserts' (membership only: usable by 2nd, not by the interval / adaptive rules)")
ap.add_argument("--gpu-blocks", type=int, default=0, help="GPU front cache (vLLM prefix cache) in blocks; 0 = none (every lookup reaches the host cache)")
ap.add_argument("--ghost-src", default="all", choices=["all", "host"], help="all: the ghost / tables see every request block (LMCache's store path computes every chunk hash); host: only lookups that reach the host cache")
ap.add_argument("--r0", type=float, default=0.000134); ap.add_argument("--r1", type=float, default=9.4e-9); ap.add_argument("--l", type=float, default=0.000005)
ap.add_argument("--tau", type=float, default=300.0, help="decay time constant of the online statistics (applied as 4 tau)")
ap.add_argument("--replan", type=float, default=10.0, help="adaptive / auto: seconds between re-plans")
ap.add_argument("--freeze-at", type=float, default=0.0, help="stop updating the online statistics after this fraction of the trace span (0 = never)")
ap.add_argument("--cold-start", action="store_true", help="clear the ghost and the online statistics at the first scored request (the cache content stays)")
ap.add_argument("--wgrid", default="15,30,60,120,240,480,960", help="adaptive: windows w (s) of the re-lookup labels")
ap.add_argument("--feat", default="c,int,pos,pre", help="adaptive: class features among c (touch count), int (last gap bucket), pos (position bucket), pre (existing-prefix bucket), root")
ap.add_argument("--label", default="relookup", choices=["relookup", "hitbe"], help="adaptive: relookup = policy-independent 'looked up again within w'; hitbe = the cache's own 'hit before eviction' (policy-dependent, admitted blocks only)")
ap.add_argument("--fixed-th", type=float, default=-1.0, help="adaptive ablation: a constant threshold on P(re-lookup within residence) instead of the replanned one")
ap.add_argument("--fixed-w", type=float, default=0.0, help="ablation: a constant window (s) instead of the online residence estimate")
ap.add_argument("--res-mode", default="evict", choices=["evict", "evict50", "evict1000", "dead", "rate", "tail", "median"], help="online residence estimate that drives the gap rules / adaptive policies")
ap.add_argument("--no-chain", action="store_true", help="adaptive ablation: do not refuse a block whose predecessor in the request was just refused")
ap.add_argument("--prior", type=float, default=10.0, help="adaptive: strength of the hierarchical prior (pseudo-samples)")
ap.add_argument("--window", type=float, default=0.01, help="W-TinyLFU window share of the capacity")
ap.add_argument("--tlfu-sample", type=float, default=10.0, help="TinyLFU: counters are halved after this many × capacity increments")
ap.add_argument("--kin", type=float, default=0.25); ap.add_argument("--kout", type=float, default=0.5)
ap.add_argument("--admit-th", type=float, default=0.15); ap.add_argument("--min-samples", type=float, default=50.0)
ap.add_argument("--regime", default="res", choices=["off", "res", "res_ft", "model", "always"], help="2nd_int_auto: regime rule (res: admit-all residence vs the gap quantile of re-seen blocks; res_ft: vs the gap quantile of FIRST-touch blocks' re-lookups; model: predicted hits; off = never normal admission; always = always normal = LRU)")
ap.add_argument("--regime-q", type=float, default=0.5, help="2nd_int_auto res rule: normal admission when the predicted admit-all residence >= this conditional quantile of the observed re-lookup gaps of re-seen blocks")
ap.add_argument("--regime-margin", type=float, default=0.0, help="2nd_int_auto model rule: normal admission when predicted hits(admit all) >= (1 + margin) × hits(filter)")
ap.add_argument("--regime-hold", type=float, default=30.0, help="2nd_int_auto: the criterion must hold continuously for this many seconds before a switch (hysteresis)")
ap.add_argument("--normal-mode", default="lru", choices=["lru", "slru"], help="2nd_int_auto: structure of the cache (slru = probation / protected in both regimes)")
ap.add_argument("--churn", default="", help="CONSTRUCTED load step: 'R,A,B' = SYNTHETIC never-reused 8-block requests (unique prefixes) at R blocks per second during the span fraction [A,B)")
ap.add_argument("--thin", default="", help="CONSTRUCTED load drop: 'F,A,B' = drop a fraction F of the requests in the span fraction [A,B)")
ap.add_argument("--dump-hits", default=""); ap.add_argument("--dump-admit", default="")
ap.add_argument("--dump-tables", default="", help="adaptive / shadow: write the class tables at the end of each scored fifth to <path>-<policy>-<cap>-tables.json")
ap.add_argument("--shadow", action="store_true", help="maintain the adaptive tables under any policy (selection-bias check), without using them")
ap.add_argument("--plan-log", default="", help="adaptive / auto: write the re-plan time series to <path>-<policy>-<cap>.json")
ap.add_argument("--res-log", default="", help="write the residence-estimator time series (every --log-dt s) and the per-estimator error statistics (log10 of estimate / realized residence of blocks admitted at that time and later evicted without a hit; ages >= 1 s) to <path>-<policy>-<cap>-res.json")
ap.add_argument("--log-dt", type=float, default=5.0)
ap.add_argument("--dec-log", default="", help="gap rules: per-decision log (t, touches, gap, residence estimate, admitted, regime, future next-use gap [accounting only], outcome) to <path>-<policy>-<cap>-dec.csv")
ap.add_argument("--audit", action="store_true", help="check the prefix-semantics invariants on every scored access and report counts")
A = ap.parse_args(); INF = float("inf"); TOK = A.tok

def load():
    out = []
    if A.mooncake:
        for i, l in enumerate(open(A.trace)):
            r = json.loads(l); out.append(dict(t=r["timestamp"] / 1000.0, hashes=[str(h) for h in r["hash_ids"]], task=i, L=r.get("input_length")))
    else:
        for l in open(A.trace):
            r = json.loads(l); out.append(dict(t=r["t_lookup"], hashes=list(r["hashes"]), task=r.get("task", 0), L=r.get("input_length")))
    out.sort(key=lambda r: r["t"])
    t0, t1 = out[0]["t"], out[-1]["t"]; span = max(1e-9, t1 - t0)
    if A.thin:
        f, a, b = (float(x) for x in A.thin.split(",")); rng = random.Random(11)
        out = [r for r in out if not (a <= (r["t"] - t0) / span < b and rng.random() < f)]
    if A.churn:
        rate, a, b = (float(x) for x in A.churn.split(",")); n = int(rate * span * (b - a) / 8)        # 8-block never-reused requests (a unique prefix each) at rate / 8 requests per second
        for j in range(n):
            t = t0 + span * (a + (j + 0.5) * (b - a) / n); out.append(dict(t=t, hashes=[f"churn{j:09d}_{b_}" for b_ in range(8)], task=-1, L=8 * TOK))
        out.sort(key=lambda r: r["t"])
    return out
R = load(); NR = len(R)
acc = [(r["t"], h, ri) for ri, r in enumerate(R) for h in r["hashes"]]
nu = [INF] * len(acc); last = {}
for i in range(len(acc) - 1, -1, -1):
    h = acc[i][1]; nu[i] = last.get(h, INF); last[h] = i
s0, s1 = (float(x) for x in A.score_range.split(",")); LO, HI = int(s0 * NR), int(s1 * NR)
T0, T1 = R[0]["t"], R[-1]["t"]; SPAN = max(1e-9, T1 - T0); FREEZE_T = (T0 + A.freeze_at * SPAN) if A.freeze_at > 0 else INF
WG = [float(x) for x in A.wgrid.split(",")]; WMAX = WG[-1]; FEAT = A.feat.split(",")
BLOCK_MB = A.chunk_mb

class Ghost:
    """history of hashes that are not resident: hash -> [last touch time, touches so far (capped at 3), class at last touch].
    Exact (unbounded or LRU-bounded to N entries, optional TTL) or a double-buffered Bloom filter (membership only)."""
    def __init__(s, cap):
        spec = A.ghost; s.N = INF if spec == "inf" else (int(float(spec[:-1]) * cap) if spec.endswith("c") else int(spec))
        s.ttl = A.ghost_ttl; s.od = OD(); s.max = 0; s.bloom = None
        if A.ghost_bloom:
            m, k, reset = A.ghost_bloom.split(","); s.bm = int(m); s.bk = int(k); s.breset = int(reset); s.bf = [bytearray(s.bm // 8 + 1), bytearray(s.bm // 8 + 1)]; s.bn = 0; s.bloom = True
    def _bits(s, h):
        d = hashlib.blake2b(h.encode(), digest_size=16).digest(); return [int.from_bytes(d[4 * i:4 * i + 4], "little") % s.bm for i in range(s.bk)]
    def bloom_put(s, h):
        for b in s._bits(h): s.bf[0][b >> 3] |= 1 << (b & 7)
        s.bn += 1
        if s.bn >= s.breset: s.bf = [bytearray(s.bm // 8 + 1), s.bf[0]]; s.bn = 0
    def bloom_has(s, h): return all((s.bf[0][b >> 3] >> (b & 7)) & 1 or (s.bf[1][b >> 3] >> (b & 7)) & 1 for b in s._bits(h))
    def get(s, h, t):
        e = s.od.get(h)
        if e is None: return None
        if s.ttl and t - e[0] > s.ttl: del s.od[h]; return None
        return e
    def put(s, h, e):
        s.od[h] = e; s.od.move_to_end(h)
        while len(s.od) > s.N: s.od.popitem(last=False)
        if len(s.od) > s.max: s.max = len(s.od)
    def pop(s, h): return s.od.pop(h, None)
    def bytes(s): return (s.bm // 8 * 2) if s.bloom else s.max * 32

class Tables:
    """online class statistics with a hierarchical prior. Policy-independent labels: for a touch of class k at t0, whether the
    same hash is looked up again within w (each w of the grid), resolved at the next lookup or at t0 + WMAX. Also the
    decayed rate of admission candidates (host misses) per class."""
    def __init__(s): s.tau4 = 4 * A.tau; s.c = {}; s.frozen = False
    @staticmethod
    def parents(k): return [k, k[:3] + (None,), k[:2] + (None, None), k[:1] + (None, None, None), (None, None, None, None)]
    def _e(s, k, t):
        e = s.c.get(k)
        if e is None: e = s.c[k] = [t, 0.0, [0.0] * len(WG), 0.0]
        elif t > e[0]:
            f = math.exp(-(t - e[0]) / s.tau4); e[1] *= f; e[3] *= f; cw = e[2]
            for i in range(len(cw)): cw[i] *= f
            e[0] = t
        return e
    def cand(s, k, t):
        if s.frozen: return
        for kk in s.parents(k): s._e(kk, t)[3] += 1.0
    def label(s, k, t, dt):
        if s.frozen: return
        for kk in s.parents(k):
            e = s._e(kk, t); e[1] += 1.0; cw = e[2]
            for i, w in enumerate(WG):
                if dt <= w: cw[i] += 1.0
    @staticmethod
    def _interp(cw, w):
        if w <= WG[0]: return cw[0] * w / WG[0]
        if w >= WG[-1]: return cw[-1]
        for i in range(1, len(WG)):
            if w <= WG[i]:
                a = (math.log(w) - math.log(WG[i - 1])) / (math.log(WG[i]) - math.log(WG[i - 1])); return cw[i - 1] + a * (cw[i] - cw[i - 1])
        return cw[-1]
    def F(s, k, w, t):
        p = 0.0
        for kk in reversed(s.parents(k)):
            e = s.c.get(kk)
            if e is None: continue
            if t > e[0]: s._e(kk, t)
            p = (s._interp(e[2], w) + A.prior * p) / (e[1] + A.prior)
        return p
    def raw(s, k, t):
        """(labelled touches, re-lookup counts per window) of a class without the prior (decayed to t)."""
        e = s.c.get(k)
        if e is None: return 0.0, [0.0] * len(WG)
        if t > e[0]: s._e(k, t)
        return e[1], list(e[2])
    def n(s, k): e = s.c.get(k); return e[1] if e else 0.0
    def rate(s, k, t=None):
        e = s.c.get(k)
        if not e: return 0.0
        norm = s.tau4 * (1.0 - math.exp(-max(1e-6, (t if t is not None else e[0]) - T0) / s.tau4))
        return e[3] / max(1e-9, norm)
    def snapshot(s, t):
        out = {}
        for k, e in s.c.items():
            s._e(k, t); out["/".join("-" if x is None else str(x) for x in k)] = dict(n=round(e[1], 1), rate=round(e[3] / s.tau4, 4), F=[round(x / max(1e-9, e[1]), 3) for x in e[2]])
        return out

def run(policy, cap):
    base = policy.split("+")[0]
    base, _, wstr = base.partition(":"); WIN = float(wstr) if wstr else 0.0       # window-based policies: "wslru:60", "wlfu:60", "wslru2nd:60", "wlfu2nd:60" (W in seconds; 2026-10-27 exploratory study)
    wbased = base in ("wslru", "wlfu", "wslru2nd", "wlfu2nd"); wacc = {}                 # wacc[h] = deque of access times within the last W seconds
    auto = base == "2nd_int_auto"
    use_ghost = base in ("2nd", "2nd_int", "2nd_int_auto", "adaptive", "adapt2", "wslru2nd", "wlfu2nd") or A.shadow
    feats = ["c"] if base in ("adapt2", "2nd_int_auto") else FEAT
    ghost = Ghost(cap); tab = Tables() if (base in ("adaptive", "adapt2", "2nd_int", "2nd_int_auto") or A.shadow) else None
    use_slru = base == "slru" or (auto and A.normal_mode == "slru")
    lru = OD(); where = {}
    prob = OD(); prot = OD()
    aT1 = OD(); aT2 = OD(); B1 = OD(); B2 = OD(); arc_p = [0.0]
    A1in = OD(); A1out = OD(); Am = OD(); KIN = max(1, int(A.kin * cap)); KOUT = max(1, int(A.kout * cap))
    win = OD(); WCAP = max(1, int(A.window * cap)); MAIN = cap - WCAP; PROBC = max(1, int(0.2 * MAIN))
    freq = {}; door = set(); incs = [0]; SAMPLE = int(A.tlfu_sample * cap)
    heap = []; nuv = {}
    rmeta = {}
    pend = {}; pend_dl = []
    hit_lbl = {}
    cls_stat = collections.defaultdict(lambda: [0.0, 0.0, None]); blk_cls = {}; blk_hit = {}
    seen_all = set(); known = set()
    # ---- residence estimators, all maintained; A.res_mode picks the driver ----
    est = dict(evict=None, evict50=None, evict1000=None, dead=None); adm_rate = [0.0, None]; ages = collections.deque(maxlen=200); med_cache = [None, -INF]
    thr = [0.0]; plan_t = [-INF]; plan_log = []
    regime = ["filter"]; cand_since = [None]; switches = []; reg_log = []
    st = collections.Counter(); st_res = []; st_res_dead = []; hits_f = [0] * 5; acc_f = [0] * 5; served_f = [0] * 5
    stored_at = {}; last_state = {}; last_idx = {}; n_dead = [0]; occ = [0.0, 0.0]; last_t = [None]
    hitlog = bytearray() if A.dump_hits else None; admlog = bytearray() if A.dump_admit else None; tab_dumps = {}
    gpu = OD(); GPU = A.gpu_blocks
    cur = [-1]; req_hs = []; req_new = []; usable = [True]; req_old = [0]; prev_ok = [True]; cold_done = [False]
    reuse = False; c_ = 0; dt_ = None; k = None
    adm_est = {}; err = {m: [] for m in ("evict", "evict50", "evict1000", "dead", "rate", "tail", "median")}
    res_series = []; win_cnt = [0, 0, 0, T0]
    dec_rows = []; dec_open = {}
    audit = collections.Counter()
    def dec(st_, t):
        if st_[2] is not None and t > st_[2]: f = math.exp(-(t - st_[2]) / (4 * A.tau)); st_[0] *= f; st_[1] *= f
        st_[2] = t if st_[2] is None else max(st_[2], t)
    def rate_(st_, t, prior, kk=20.0): dec(st_, t); return (st_[0] + kk * prior) / (st_[1] + kk)
    def est_all(t):
        """every residence estimator at time t (INF where undefined)."""
        out = {m: (est[m] if est[m] is not None else INF) for m in ("evict", "evict50", "evict1000", "dead")}
        out["rate"] = cap / max(1e-6, adm_rate[0] / (4 * A.tau * (1.0 - math.exp(-max(1e-6, t - T0) / (4 * A.tau))))) if adm_rate[1] is not None else INF
        tail = (next(iter(prob), None) or next(iter(prot), None)) if use_slru else next(iter(lru), None)
        out["tail"] = (t - rmeta[tail][0]) if tail is not None and len(where) >= cap and tail in rmeta else INF
        if ages:
            if med_cache[1] < t - 1.0: s_ = sorted(ages); med_cache[0] = s_[len(s_) // 2]; med_cache[1] = t
            out["median"] = med_cache[0]
        else: out["median"] = INF
        return out
    def residence(t):
        if A.fixed_w > 0: return A.fixed_w
        return est_all(t)[A.res_mode]
    def note_adm(t):
        if adm_rate[1] is not None: adm_rate[0] *= math.exp(-(t - adm_rate[1]) / (4 * A.tau))
        adm_rate[0] += 1.0; adm_rate[1] = t
    def scored(i): ri = acc[i][2]; return LO <= ri < HI and R[ri]["task"] >= 0
    # ---- eviction / admission hooks ----
    def on_evict(h, t):
        where.pop(h, None); lru.pop(h, None); prob.pop(h, None); prot.pop(h, None); nuv.pop(h, None); wacc.pop(h, None)
        m = rmeta.pop(h, None)
        if m is not None and use_ghost and ghost.bloom is None: ghost.put(h, m)
        if base == "lhd":
            if not blk_hit.get(h, False) and t <= FREEZE_T and h in blk_cls: st_ = cls_stat[blk_cls[h]]; dec(st_, t); st_[1] += 1
            blk_hit.pop(h, None); blk_cls.pop(h, None)
        if A.label == "hitbe" and tab is not None and h in hit_lbl: tab.label(hit_lbl.pop(h), t, INF)
        last_state[h] = "evicted"; st["evict"] += 1; st["evict_live"] += (nu[last_idx[h]] < INF)
        if nu[last_idx[h]] == INF: n_dead[0] -= 1
        if h in stored_at:
            age = t - stored_at.pop(h); hit_before = bool(m[3]) if (m is not None and len(m) > 3) else False
            if len(st_res) < 300000: st_res.append(age)
            est["evict"] = age if est["evict"] is None else est["evict"] + (age - est["evict"]) / 200.0
            est["evict50"] = age if est["evict50"] is None else est["evict50"] + (age - est["evict50"]) / 50.0
            est["evict1000"] = age if est["evict1000"] is None else est["evict1000"] + (age - est["evict1000"]) / 1000.0
            ages.append(age)
            if not hit_before:
                est["dead"] = age if est["dead"] is None else est["dead"] + (age - est["dead"]) / 200.0
                if len(st_res_dead) < 300000: st_res_dead.append(age)
                e0 = adm_est.pop(h, None)
                if e0 is not None and age >= 1.0 and len(err["evict"]) < 200000:
                    for mname, v in e0.items():
                        if v < INF: err[mname].append(math.log10(max(1e-3, v) / age))
            else: adm_est.pop(h, None)
            d = dec_open.pop(h, None)
            if d is not None: d[-1] = "dead" if not hit_before else "hit"; d.append(round(age, 1))
    def on_admit(h, t, i, kk):
        where[h] = True; stored_at[h] = t; last_state[h] = None; st["written"] += 1; note_adm(t); win_cnt[0] += 1
        if use_ghost: ghost.pop(h)
        rmeta[h] = [t, min(3, c_ + 1), kk, False]
        if nu[i] == INF: st["admit_never"] += 1; n_dead[0] += 1
        if A.label == "hitbe" and tab is not None: hit_lbl[h] = kk
        if admlog is not None and scored(i) and not reuse: admlog.append(1)
        if A.res_log and len(adm_est) < 400000: adm_est[h] = est_all(t)
    def bypass(h, t, i):
        st["bypass"] += 1; last_state[h] = "bypassed"
        if nu[i] < INF:
            st["bypass_reused"] += 1; d_ = acc[nu[i]][0] - t; st["bypass_reused_60"] += (d_ <= 60); st["bypass_reused_300"] += (d_ <= 300)
        if admlog is not None and scored(i) and not reuse: admlog.append(0)
        if use_ghost:
            if ghost.bloom is None: ghost.put(h, [t, min(3, c_ + 1), k])
            else: ghost.bloom_put(h)
    # ---- LRU-family cache ----
    def wprune(h, t):
        d = wacc.get(h)
        if d is None: return 0
        while d and d[0] < t - WIN: d.popleft()
        return len(d)
    def lru_victim(t):
        if use_slru: return next(iter(prob)) if prob else next(iter(prot))
        if base in ("wslru", "wslru2nd"):                                   # time-expiring protection: a protected block with no access for W seconds is demoted to the probation tail
            while prot:
                tail = next(iter(prot))
                if rmeta[tail][0] < t - WIN: prot.pop(tail); prob[tail] = True; prob.move_to_end(tail, last=False)
                else: break
            return next(iter(prob)) if prob else next(iter(prot))
        if base in ("wlfu", "wlfu2nd"):                                     # among the K least recently used blocks, the one with the fewest accesses in the last W seconds (ties: the least recent)
            K = min(64, max(8, cap // 16)); best = None; bc = INF; k_ = 0
            for b in lru:
                c = wprune(b, t)
                if c < bc: best, bc = b, c
                k_ += 1
                if k_ >= K or bc == 0: break
            return best
        if base == "lhd":
            win_ = min(64, max(4, cap // 16)); best = None; bc = INF; k_ = 0
            for b in lru:
                st_ = cls_stat.get(blk_cls.get(b)); c = rate_(st_, t, 0.3) if st_ and st_[1] >= 20 else 0.3
                if c < bc: best, bc = b, c
                k_ += 1
                if k_ >= win_: break
            return best
        return next(iter(lru))
    def lru_insert(h, t, i, kk):
        if len(where) >= cap: on_evict(lru_victim(t), t)
        on_admit(h, t, i, kk); lru[h] = True
        if use_slru or base in ("wslru", "wslru2nd"): prob[h] = True
        if wbased: wacc[h] = collections.deque([t])
        if base == "oracle": nuv[h] = nu[i]; heapq.heappush(heap, (-nu[i], h))
        if use_ghost and ghost.bloom is not None: ghost.bloom_put(h)
    def w_hit(h, t):
        """window policies on a hit: record the access; wslru promotes a block with >= 2 accesses inside the window to the protected segment."""
        lru.move_to_end(h); wprune(h, t); wacc.setdefault(h, collections.deque()).append(t)
        if base in ("wslru", "wslru2nd"):
            if h in prot: prot.move_to_end(h)
            elif len(wacc[h]) >= 2: prob.pop(h, None); prot[h] = True
            else: prob.move_to_end(h)
    def lru_hit(h, t, i):
        lru.move_to_end(h)
        if use_slru:
            if h in prot: prot.move_to_end(h)
            else:
                prob.pop(h, None); prot[h] = True
                while len(prot) > cap // 3: d_, _ = prot.popitem(last=False); prob[d_] = True
        if base == "oracle": nuv[h] = nu[i]; heapq.heappush(heap, (-nu[i], h))
    # ---- ARC ----
    def arc_replace(h, t):
        if aT1 and (len(aT1) > arc_p[0] or (h in B2 and len(aT1) == arc_p[0])):
            v, _ = aT1.popitem(last=False); on_evict(v, t); B1[v] = True
        else:
            v, _ = aT2.popitem(last=False); on_evict(v, t); B2[v] = True
    def arc_access(h, t, i, kk):
        if h in aT1 or h in aT2:
            (aT1 if h in aT1 else aT2).pop(h); aT2[h] = True; return True
        if h in B1:
            arc_p[0] = min(cap, arc_p[0] + max(len(B2) / max(1, len(B1)), 1.0)); arc_replace(h, t); B1.pop(h); on_admit(h, t, i, kk); aT2[h] = True; return False
        if h in B2:
            arc_p[0] = max(0.0, arc_p[0] - max(len(B1) / max(1, len(B2)), 1.0)); arc_replace(h, t); B2.pop(h); on_admit(h, t, i, kk); aT2[h] = True; return False
        L1 = len(aT1) + len(B1)
        if L1 == cap:
            if len(aT1) < cap: B1.popitem(last=False); arc_replace(h, t)
            else: v, _ = aT1.popitem(last=False); on_evict(v, t)
        elif L1 < cap and L1 + len(aT2) + len(B2) >= cap:
            if L1 + len(aT2) + len(B2) >= 2 * cap: B2.popitem(last=False)
            arc_replace(h, t)
        on_admit(h, t, i, kk); aT1[h] = True; return False
    # ---- 2Q ----
    def q2_reclaim(t):
        if len(A1in) + len(Am) < cap: return
        if len(A1in) > KIN:
            v, _ = A1in.popitem(last=False); on_evict(v, t); A1out[v] = True
            while len(A1out) > KOUT: A1out.popitem(last=False)
        else: v, _ = Am.popitem(last=False); on_evict(v, t)
    def q2_access(h, t, i, kk):
        if h in Am: Am.move_to_end(h); return True
        if h in A1in: return True
        if h in A1out: A1out.pop(h); q2_reclaim(t); on_admit(h, t, i, kk); Am[h] = True; return False
        q2_reclaim(t); on_admit(h, t, i, kk); A1in[h] = True; req_new.append(h); return False
    # ---- TinyLFU ----
    def tl_inc(h):
        if h not in door: door.add(h)
        else: freq[h] = min(15, freq.get(h, 0) + 1)
        incs[0] += 1
        if incs[0] >= SAMPLE:
            for x in list(freq):
                freq[x] //= 2
                if freq[x] == 0: del freq[x]
            door.clear(); incs[0] = 0
    def tl_f(h): return freq.get(h, 0) + (1 if h in door else 0)
    def wtl_access(h, t, i, kk):
        if h in win: win.move_to_end(h); return True
        if h in prot: prot.move_to_end(h); return True
        if h in prob:
            prob.pop(h); prot[h] = True
            while len(prot) > MAIN - PROBC: d_, _ = prot.popitem(last=False); prob[d_] = True
            return True
        on_admit(h, t, i, kk); win[h] = True
        if len(win) > WCAP:
            c0, _ = win.popitem(last=False)
            if len(prob) + len(prot) < MAIN: prob[c0] = True
            else:
                v = next(iter(prob)) if prob else next(iter(prot))
                if tl_f(c0) > tl_f(v): on_evict(v, t); prob[c0] = True
                else: on_evict(c0, t)
        return False
    # ---- classes ----
    def cls_of(c, dt, j, old, root):
        f = []
        for name in feats:
            if name == "c": f.append(min(3, c))
            elif name == "int": f.append(0 if dt is None else 1 if dt < 30 else 2 if dt < 120 else 3 if dt < 480 else 4)
            elif name == "pos": f.append(0 if j < 8 else 1 if j < 32 else 2)
            elif name == "pre": f.append(0 if old < 8 else 1 if old < 16 else 2)
            elif name == "root": f.append(root)
        while len(f) < 4: f.append(0)
        return tuple(f[:4])
    def two_class(t):
        """first-touch vs re-seen aggregates from the touch-count classes: candidate rates and re-lookup CDF samples."""
        kf = (0, 0, 0, 0); lam_f = tab.rate(kf, t); nf, cf = tab.raw(kf, t)
        lam_r = 0.0; nr = 0.0; cr = [0.0] * len(WG)
        for c in (1, 2, 3):
            kk = (c, 0, 0, 0); lam_r += tab.rate(kk, t); n_, c_w = tab.raw(kk, t); nr += n_
            for i in range(len(WG)): cr[i] += c_w[i]
        return lam_f, lam_r, nf, cf, nr, cr
    def Fof(n_, cw, w):
        if n_ <= 0: return 0.0
        return Tables._interp(cw, w) / n_
    def regime_eval(t):
        """2nd_int_auto: decide the candidate regime from online statistics only; switch after --regime-hold s of agreement."""
        info = ()
        if A.regime == "always": want = "normal"
        elif A.regime == "off": want = "filter"
        else:
            lam_f, lam_r, nf, cf, nr, cr = two_class(t)
            if nf < 50 or nr < 50 or lam_f + lam_r <= 0: want = regime[0]
            else:
                R_all = cap / (lam_f + lam_r)
                if A.regime in ("res", "res_ft"):
                    cq, nq = (cf, nf) if A.regime == "res_ft" else (cr, nr)
                    tot = cq[-1] / nq if nq > 0 else 0.0
                    target = A.regime_q * tot; Hq = INF
                    for i, w in enumerate(WG):
                        if cq[i] / nq >= target:
                            if i == 0: Hq = w
                            else:
                                lo, hi = cq[i - 1] / nq, cq[i] / nq; a = (target - lo) / max(1e-9, hi - lo); Hq = math.exp(math.log(WG[i - 1]) + a * (math.log(w) - math.log(WG[i - 1])))
                            break
                    want = "normal" if R_all >= Hq else "filter"; info = (round(R_all, 1), (round(Hq, 1) if Hq < INF else None))
                else:
                    Rf = residence(t); Rf = Rf if Rf < INF else R_all
                    h_all = lam_f * Fof(nf, cf, R_all) + lam_r * Fof(nr, cr, R_all); h_fil = lam_r * Fof(nr, cr, max(Rf, R_all))
                    want = "normal" if h_all >= (1 + A.regime_margin) * h_fil else "filter"; info = (round(h_all, 4), round(h_fil, 4), round(R_all, 1))
                if len(reg_log) < 20000: reg_log.append((round(t - T0, 1), regime[0], want) + info)
        if want != regime[0]:
            if cand_since[0] is None: cand_since[0] = t
            elif t - cand_since[0] >= A.regime_hold: switches.append((round(t - T0, 1), regime[0], want)); regime[0] = want; cand_since[0] = None
        else: cand_since[0] = None
    def replan(t):
        Rn = residence(t)
        if Rn == INF: thr[0] = 0.0; return
        leaves = [(kk, tab.rate(kk, t)) for kk in tab.c if None not in kk]; leaves = [(kk, lam) for kk, lam in leaves if lam > 0]
        if not leaves: thr[0] = 0.0; return
        order = sorted(leaves, key=lambda kl: -tab.F(kl[0], Rn, t)); best = (0.0, 0.0, INF); lam_sum = 0.0
        for j_, (kk, lam) in enumerate(order):
            lam_sum += lam; Rj = cap / lam_sum; H = sum(l2 * tab.F(k2, Rj, t) for k2, l2 in order[:j_ + 1])
            if H > best[0]: best = (H, tab.F(kk, Rn, t), Rj)
        thr[0] = best[1] if A.fixed_th < 0 else A.fixed_th
        if len(plan_log) < 20000:
            tot = sum(l for _, l in leaves); adm = sum(l for kk, l in leaves if tab.F(kk, Rn, t) >= thr[0])
            plan_log.append((round(t - T0, 1), round(Rn, 1), round(thr[0], 3), round(best[0], 3), round(adm / max(1e-9, tot), 3), round(best[2], 1)))
    def end_request():
        if cur[0] < 0: return
        for b in reversed(req_hs):
            if b in lru: lru.move_to_end(b)
            if b in prot: prot.move_to_end(b)
            elif b in prob: prob.move_to_end(b)
            if b in aT1: aT1.move_to_end(b)
            elif b in aT2: aT2.move_to_end(b)
            if b in Am: Am.move_to_end(b)
            if b in win: win.move_to_end(b)
            if GPU and b in gpu: gpu.move_to_end(b)
        for b in reversed(req_new):
            if b in A1in: A1in.move_to_end(b)
    def log_tick(t):
        if not A.res_log or t - win_cnt[3] < A.log_dt: return
        e = est_all(t); row = dict(t=round(t - T0, 1), adm=win_cnt[0], hits=win_cnt[1], miss=win_cnt[2], regime=regime[0] if auto else None, resident=len(where))
        for mname, v in e.items(): row[mname] = round(v, 1) if v < INF else None
        if len(res_series) < 100000: res_series.append(row)
        win_cnt[0] = win_cnt[1] = win_cnt[2] = 0; win_cnt[3] = t
    for i, (t, h, ri) in enumerate(acc):
        if ri != cur[0]:
            end_request(); cur[0] = ri; req_hs.clear(); req_new.clear(); usable[0] = True; prev_ok[0] = True
            req_old[0] = sum(1 for x in R[ri]["hashes"] if x in known)
            if A.cold_start and not cold_done[0] and ri >= LO:
                cold_done[0] = True; ghost.od.clear(); pend.clear(); pend_dl.clear(); hit_lbl.clear(); cls_stat.clear()
                for mm in rmeta.values(): mm[1] = 0
                if tab is not None: tab.c.clear()
                thr[0] = 0.0; plan_t[0] = -INF
            if tab is not None and A.dump_tables and LO <= ri < HI:
                f5 = min(4, int(5 * (ri - LO) / max(1, HI - LO)))
                if f5 > 0 and (f5 - 1) not in tab_dumps: tab_dumps[f5 - 1] = tab.snapshot(t)
            if tab is not None and t > FREEZE_T: tab.frozen = True
            log_tick(t)
        j = len(req_hs); req_hs.append(h)
        test = scored(i); f_ = min(4, int(5 * (ri - LO) / max(1, HI - LO))) if test else 0
        reuse = h in seen_all
        if test:
            acc_f[f_] += 1; st["acc"] += 1; st["reuse"] += reuse
            if last_t[0] is not None and where: dt = t - last_t[0]; occ[0] += dt * len(where); occ[1] += dt * n_dead[0]
        last_t[0] = t
        gpu_hit = False
        if GPU:
            if h in gpu: gpu.move_to_end(h); gpu_hit = True
            else:
                gpu[h] = True
                if len(gpu) > GPU: gpu.popitem(last=False)
        visible = not (gpu_hit and A.ghost_src == "host")
        m = rmeta.get(h) or ((ghost.get(h, t) if ghost.bloom is None else None) if use_ghost else None)
        if use_ghost and ghost.bloom is not None and m is None: c_, dt_ = ((1, None) if ghost.bloom_has(h) else (0, None))
        else: c_, dt_ = ((m[1], t - m[0]) if m else (0, None))
        if use_ghost and visible and m is None and reuse and ghost.bloom is None: st["ghost_forgot"] += 1
        if use_ghost and ghost.bloom is not None and not reuse and c_ == 1: st["bloom_fp"] += 1
        root = R[ri]["hashes"][0]; k = cls_of(c_, dt_, j, req_old[0], root) if tab is not None else None
        if tab is not None and visible:
            while pend_dl and pend_dl[0][0] <= t:
                dl, hb, t0 = heapq.heappop(pend_dl); pb = pend.get(hb)
                if pb is not None and pb[0] == t0: pend.pop(hb); tab.label(pb[1], dl, INF)
            pb = pend.get(h)
            if pb is not None: pend.pop(h); tab.label(pb[1], t, t - pb[0])
            if A.label == "relookup":
                pend[h] = (t, k); heapq.heappush(pend_dl, (t + WMAX, h, t))
                if len(pend) > st["pend_max"]: st["pend_max"] = len(pend)
            if A.label == "hitbe" and h in hit_lbl and h in where: tab.label(hit_lbl.pop(h), t, t - stored_at.get(h, t))
        if base in ("tinylfu", "wtinylfu"): tl_inc(h)
        if hitlog is not None and test: hitlog.append(1 if (h in where or gpu_hit) else (2 if last_state.get(h) == "bypassed" else 3 if last_state.get(h) == "evicted" else 0))
        hit = False
        if not gpu_hit and h in where:
            hit = True
            if base in ("lru", "slru", "2nd", "2nd_int", "2nd_int_auto", "adaptive", "adapt2", "lhd", "tinylfu", "oracle"): lru_hit(h, t, i)
            elif wbased: w_hit(h, t)
            elif base == "arc": arc_access(h, t, i, k)
            elif base == "2q": q2_access(h, t, i, k)
            elif base == "wtinylfu": wtl_access(h, t, i, k)
            if base == "lhd" and not blk_hit.get(h, False) and t <= FREEZE_T and h in blk_cls: blk_hit[h] = True; st_ = cls_stat[blk_cls[h]]; dec(st_, t); st_[0] += 1; st_[1] += 1
            mm = rmeta[h]; mm[0] = t; mm[1] = min(3, mm[1] + 1)
            if not mm[3]:
                mm[3] = True; adm_est.pop(h, None); d = dec_open.pop(h, None)
                if d is not None: d[-1] = "hit"; d.append(round(t - stored_at.get(h, t), 1))
            was_dead = nu[last_idx.get(h, i)] == INF; now_dead = nu[i] == INF
            if was_dead and not now_dead: n_dead[0] -= 1
            if not was_dead and now_dead: n_dead[0] += 1
            if A.audit and test:
                if last_state.get(h) is not None: audit["hit_on_bypassed_or_evicted"] += 1
                if use_ghost and ghost.bloom is None and h in ghost.od: audit["resident_in_ghost"] += 1
        last_idx[h] = i
        served = hit or gpu_hit
        if test:
            if hit: st["hit"] += 1; hits_f[f_] += 1; win_cnt[1] += 1
            if gpu_hit: st["gpu_hit"] += 1
            if served:
                st["served"] += 1; served_f[f_] += 1
                if usable[0]: st["usable"] += 1; st["usable_tok"] += TOK; st["ttft"] += A.l * TOK
                elif A.audit: audit["served_behind_a_hole_not_counted"] += 1
            else:
                st["miss"] += 1; ls_ = last_state.get(h); win_cnt[2] += 1
                st["miss_bypassed" if ls_ == "bypassed" else "miss_evicted" if ls_ == "evicted" else "miss_new"] += 1
                if usable[0]:
                    usable[0] = False; rem = (R[ri]["L"] or len(R[ri]["hashes"]) * TOK) - j * TOK; st["ttft"] += A.r0 * rem + A.r1 * (rem * rem / 2 + j * TOK * rem)
        seen_all.add(h)
        if visible: known.add(h)
        if hit or (gpu_hit and h in where): prev_ok[0] = True; continue
        if tab is not None and visible: tab.cand(k, t)
        if base in ("arc", "2q", "wtinylfu"):
            if base == "arc": arc_access(h, t, i, k)
            elif base == "2q": q2_access(h, t, i, k)
            else: wtl_access(h, t, i, k)
            prev_ok[0] = True; continue
        if base == "oracle":
            if nu[i] == INF: bypass(h, t, i); continue
            if len(where) >= cap:
                while heap:
                    negn, b = heap[0]
                    if b in where and nuv.get(b) == -negn: break
                    heapq.heappop(heap)
                if -heap[0][0] <= nu[i]: bypass(h, t, i); continue
                heapq.heappop(heap); on_evict(b, t)
            on_admit(h, t, i, k); lru[h] = True; nuv[h] = nu[i]; heapq.heappush(heap, (-nu[i], h)); continue
        admit = True; cl = None; Rn = None
        if base == "2nd": admit = (c_ >= 1) or j == 0
        elif base in ("wslru2nd", "wlfu2nd"): admit = (c_ >= 1 and dt_ is not None and dt_ <= WIN) or j == 0   # seen (looked up) within the last W seconds
        elif base in ("2nd_int", "2nd_int_auto"):
            if auto and t - plan_t[0] >= A.replan: regime_eval(t); plan_t[0] = t
            Rn = residence(t)
            if auto and regime[0] == "normal": admit = True
            else: admit = (c_ >= 1 and (dt_ is None or dt_ <= Rn)) or j == 0
            if A.dec_log and test and c_ >= 1 and len(dec_rows) < 400000:
                row = [round(t - T0, 1), c_, round(dt_, 1) if dt_ is not None else None, round(Rn, 1) if Rn < INF else None, int(admit), regime[0] if auto else "filter", round(acc[nu[i]][0] - t, 1) if nu[i] < INF else None, "open"]
                dec_rows.append(row)
                if admit: dec_open[h] = row
        elif base in ("adaptive", "adapt2"):
            if t - plan_t[0] >= A.replan: replan(t); plan_t[0] = t
            Rn = residence(t)
            admit = (Rn == INF) or tab.F(k, Rn, t) >= thr[0] or j == 0
            if admit and not A.no_chain and not prev_ok[0] and j > 0: admit = False
        elif base == "lhd":
            cl = (root, min(3, j // 8), min(2, req_old[0] // 8))
            st_ = cls_stat.get(cl); p_ = rate_(st_, t, 0.3) if st_ and st_[1] >= A.min_samples else 1.0
            if p_ < A.admit_th and j > 0: admit = False
        elif base == "tinylfu":
            if len(where) >= cap: admit = tl_f(h) > tl_f(next(iter(lru)))
        if admit:
            if base == "lhd": blk_cls[h] = cl; blk_hit[h] = False
            lru_insert(h, t, i, k); prev_ok[0] = True
        else:
            bypass(h, t, i); prev_ok[0] = False
    end_request()
    if hitlog is not None: open(f"{A.dump_hits}-{policy}-{cap}.bin", "wb").write(bytes(hitlog))
    if admlog is not None: open(f"{A.dump_admit}-{policy}-{cap}.adm", "wb").write(bytes(admlog))
    if tab is not None and A.dump_tables:
        tab_dumps[4] = tab.snapshot(acc[-1][0]); json.dump({str(kk): v for kk, v in tab_dumps.items()}, open(f"{A.dump_tables}-{policy}-{cap}-tables.json", "w"))
    if A.plan_log and base in ("adaptive", "adapt2"): json.dump(plan_log, open(f"{A.plan_log}-{policy}-{cap}.json", "w"))
    if A.plan_log and auto: json.dump(dict(switches=switches, log=reg_log), open(f"{A.plan_log}-{policy}-{cap}-regime.json", "w"))
    if A.res_log:
        def q(xs, p): xs = sorted(xs); return (xs[min(len(xs) - 1, int(p * len(xs)))] if xs else None)
        errs = {m: dict(n=len(v), bias_log10=(sum(v) / len(v) if v else None), mean_abs_log10=(sum(abs(x) for x in v) / len(v) if v else None), p50_abs_log10=q([abs(x) for x in v], .5), p90_abs_log10=q([abs(x) for x in v], .9), within_2x=(sum(1 for x in v if abs(x) <= math.log10(2)) / len(v) if v else None)) for m, v in err.items()}
        json.dump(dict(series=res_series, errors=errs, switches=switches), open(f"{A.res_log}-{policy}-{cap}-res.json", "w"))
    if A.dec_log and dec_rows:
        with open(f"{A.dec_log}-{policy}-{cap}-dec.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["t", "touches", "gap", "residence_est", "admitted", "regime", "next_gap_future", "outcome", "age"]); w.writerows(dec_rows)
    if A.audit:
        if use_ghost and ghost.bloom is None: audit["ghost_resident_overlap_end"] = sum(1 for x in ghost.od if x in where)
        bad = any(v for kk, v in audit.items() if kk != "served_behind_a_hole_not_counted")
        print(f"  audit {policy} cap {cap}: " + ", ".join(f"{kk}={v}" for kk, v in sorted(audit.items())) + ("" if bad else " (invariants hold)"), flush=True)
    st_res.sort(); st_res_dead.sort(); n_cls = len([kk for kk in (tab.c if tab is not None else {}) if None not in kk])
    return dict(policy=policy, window_s=WIN, cap=cap, cap_GiB=round(cap * BLOCK_MB / 1024, 1), ghost=A.ghost, ghost_ttl=A.ghost_ttl, ghost_bloom=A.ghost_bloom, gpu_blocks=GPU, ghost_src=A.ghost_src, feat=A.feat, label=A.label, fixed_th=A.fixed_th, fixed_w=A.fixed_w, res_mode=A.res_mode, chain=not A.no_chain, tau=A.tau, replan=A.replan, prior=A.prior, freeze_at=A.freeze_at, cold_start=A.cold_start, score_range=A.score_range,
                regime=A.regime if auto else "", regime_q=A.regime_q, regime_margin=A.regime_margin, regime_hold=A.regime_hold, normal_mode=A.normal_mode if auto else "", churn=A.churn, thin=A.thin,
                acc=st["acc"], reuse=st["reuse"], hits=st["hit"], gpu_hits=st["gpu_hit"], served=st["served"], usable=st["usable"], usable_hit_share=st["usable"] / max(1, st["reuse"]), reuse_hit_share=st["hit"] / max(1, st["reuse"]), served_share=st["served"] / max(1, st["reuse"]),
                misses=st["miss"], recomputed_tokens=st["miss"] * TOK, usable_tokens=st["usable_tok"], ttft_s=round(st["ttft"], 2),
                written_chunks=st["written"], written_TB=round(st["written"] * BLOCK_MB / 1e6, 3), bypass_total=st["bypass"], bypass_reused_later=st["bypass_reused"], bypass_reused_60s=st["bypass_reused_60"], bypass_reused_300s=st["bypass_reused_300"],
                admitted_never_reused=st["admit_never"], miss_after_bypass=st["miss_bypassed"], miss_after_eviction=st["miss_evicted"], miss_new=st["miss_new"], evictions=st["evict"], evictions_before_reuse=st["evict_live"],
                residence_p50_s=(st_res[len(st_res) // 2] if st_res else None), residence_dead_p50_s=(st_res_dead[len(st_res_dead) // 2] if st_res_dead else None), residence_est_end_s=(round(residence(acc[-1][0]), 1) if residence(acc[-1][0]) < INF else None), dead_occupancy_share=occ[1] / max(1e-9, occ[0]),
                hits_by_fifth="/".join(map(str, hits_f)), served_by_fifth="/".join(map(str, served_f)), acc_by_fifth="/".join(map(str, acc_f)),
                ghost_entries_max=ghost.max, ghost_bytes=ghost.bytes(), ghost_forgotten_relookups=st["ghost_forgot"], bloom_false_positives=st["bloom_fp"], pending_labels_max=st["pend_max"], classes=n_cls, table_bytes=(len(tab.c) * (len(WG) + 3) * 8 if tab is not None else 0),
                threshold_end=round(thr[0], 3), replans=len(plan_log), regime_end=(regime[0] if auto else ""), regime_switches=len(switches), switch_times="/".join(f"{s_[0]:.0f}:{s_[2][0]}" for s_ in switches[:40]))

os.makedirs(A.out, exist_ok=True); rows = []
for cap in (int(x) for x in A.caps.split(",")):
    for p in A.policies.split(","):
        r = run(p, cap); rows.append(r)
        print(f"cap {cap:6d} ({r['cap_GiB']:6.1f} GiB) {p:12s} usable {r['usable_hit_share']:.3f} served {r['served_share']:.3f} hits {r['hits']:7d} usable_n {r['usable']:7d} written {r['written_chunks']:7d} bypass {r['bypass_total']:7d} res {r['residence_p50_s']} est {r['residence_est_end_s']} ghost {r['ghost_entries_max']} forgot {r['ghost_forgotten_relookups']} fp {r['bloom_false_positives']} thr {r['threshold_end']} regime {r['regime_end']} switches {r['regime_switches']} {r['switch_times']}", flush=True)
with open(f"{A.out}/{A.tag}-replay.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("wrote", f"{A.out}/{A.tag}-replay.csv")
