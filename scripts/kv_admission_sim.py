#!/usr/bin/env python3
"""Admission simulator for the RQ1-B practical and adaptive admission study (2026-10-21).

Same cache semantics as scripts/kv_agent_replay.py (reproduced exactly for lru / slru / 2nd / lhd / oracle, see the
report, Task G): one host KV cache of `cap` blocks; LMCache / vLLM order (a request's blocks are touched tail-first at
request end, so the tail is evicted first); prefix-aware scoring (a hit is usable only while every earlier block of
the request hit); scored accesses = the requests in --score-range (default the second half; the first half warms the
cache and the online statistics); writes = admissions in the scored range; residence = write -> eviction.
New here:
  * a BOUNDED ghost history (exact LRU of N entries, TTL, or a double-buffered Bloom filter) feeding the second-touch
    rules and the adaptive policy; the ghost stores past lookups only, never data, and a ghost hit is an admission
    signal, never a KV hit;
  * the classic policies 2Q (Johnson & Shasha), ARC (Megiddo & Modha), TinyLFU admission (adapted: no window cache,
    exact 4-bit counts with periodic halving and a doorkeeper) and W-TinyLFU (1% window + SLRU 20/80 main);
  * the simple adaptive rules 2nd_int (admit a re-seen block only if its last gap fits the online residence estimate)
    and adapt2 (first-touch admission switched on when the predicted hit rate with it exceeds the one without);
  * `adaptive`: class tables (touch count, last gap, position, existing prefix) of POLICY-INDEPENDENT labels "looked up
    again within w" for a grid of windows w, an online residence estimate, and a replanned admission threshold on
    P(re-lookup within the residence) that maximizes the predicted hit rate under the capacity (no hand threshold);
  * an optional GPU front cache (vLLM's own prefix cache) and the choice whether the ghost sees GPU-served lookups;
  * walk-forward scoring ranges, cold start and freezing of the online statistics.
Policies: lru slru 2q arc tinylfu wtinylfu 2nd 2nd_int adapt2 adaptive lhd oracle
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
ap.add_argument("--replan", type=float, default=10.0, help="adaptive: seconds between re-plans of the admission threshold")
ap.add_argument("--freeze-at", type=float, default=0.0, help="stop updating the online statistics after this fraction of the trace span (0 = never)")
ap.add_argument("--cold-start", action="store_true", help="clear the ghost and the online statistics at the first scored request (the cache content stays)")
ap.add_argument("--wgrid", default="15,30,60,120,240,480,960", help="adaptive: windows w (s) of the re-lookup labels")
ap.add_argument("--feat", default="c,int,pos,pre", help="adaptive: class features among c (touch count), int (last gap bucket), pos (position bucket), pre (existing-prefix bucket), root")
ap.add_argument("--label", default="relookup", choices=["relookup", "hitbe"], help="adaptive: relookup = policy-independent 'looked up again within w'; hitbe = the cache's own 'hit before eviction' (policy-dependent, admitted blocks only)")
ap.add_argument("--fixed-th", type=float, default=-1.0, help="adaptive ablation: a constant threshold on P(re-lookup within residence) instead of the replanned one")
ap.add_argument("--fixed-w", type=float, default=0.0, help="adaptive ablation: a constant window (s) instead of the online residence estimate")
ap.add_argument("--res-mode", default="evict", choices=["evict", "rate"], help="online residence estimate: mean age of evicted blocks (evict) or capacity / admission rate (rate)")
ap.add_argument("--no-chain", action="store_true", help="adaptive ablation: do not refuse a block whose predecessor in the request was just refused")
ap.add_argument("--prior", type=float, default=10.0, help="adaptive: strength of the hierarchical prior (pseudo-samples)")
ap.add_argument("--window", type=float, default=0.01, help="W-TinyLFU window share of the capacity")
ap.add_argument("--tlfu-sample", type=float, default=10.0, help="TinyLFU: counters are halved after this many × capacity increments")
ap.add_argument("--kin", type=float, default=0.25); ap.add_argument("--kout", type=float, default=0.5)
ap.add_argument("--admit-th", type=float, default=0.15); ap.add_argument("--min-samples", type=float, default=50.0)
ap.add_argument("--dump-hits", default=""); ap.add_argument("--dump-admit", default="")
ap.add_argument("--dump-tables", default="", help="adaptive / shadow: write the class tables at the end of each scored fifth to <path>-<policy>-<cap>-tables.json")
ap.add_argument("--shadow", action="store_true", help="maintain the adaptive tables under any policy (selection-bias check), without using them")
ap.add_argument("--plan-log", default="", help="adaptive: write the re-plan time series (t, residence, threshold, predicted hits/s, admitted share) to <path>-<policy>-<cap>.json")
A = ap.parse_args(); INF = float("inf"); TOK = A.tok

def load():
    out = []
    if A.mooncake:
        for i, l in enumerate(open(A.trace)):
            r = json.loads(l); out.append(dict(t=r["timestamp"] / 1000.0, hashes=[str(h) for h in r["hash_ids"]], task=i, L=r.get("input_length")))
    else:
        for l in open(A.trace):
            r = json.loads(l); out.append(dict(t=r["t_lookup"], hashes=list(r["hashes"]), task=r.get("task", 0), L=r.get("input_length")))
    out.sort(key=lambda r: r["t"]); return out
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
        if s.bn >= s.breset: s.bf = [bytearray(s.bm // 8 + 1), s.bf[0]]; s.bn = 0           # the previous filter stays queryable for one more period
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
    def bytes(s): return (s.bm // 8 * 2) if s.bloom else s.max * 32                        # exact entry: 8 B hash + 4 B time + 1 B count + ~19 B list / dict overhead

class Tables:
    """online class statistics with a hierarchical prior. Policy-independent labels: for a touch of class k at t0, whether the
    same hash is looked up again within w (each w of the grid), resolved at the next lookup or at t0 + WMAX. Also the
    decayed rate of admission candidates (host misses) per class."""
    def __init__(s): s.tau4 = 4 * A.tau; s.c = {}; s.frozen = False
    @staticmethod
    def parents(k): return [k, k[:3] + (None,), k[:2] + (None, None), k[:1] + (None, None, None), (None, None, None, None)]
    def _e(s, k, t):
        e = s.c.get(k)
        if e is None: e = s.c[k] = [t, 0.0, [0.0] * len(WG), 0.0]                       # [last t, labelled touches, re-looked-up within w_i, candidate rate count]
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
        """P(next lookup within w | class k): leaf estimate shrunk toward its ancestors (prior strength A.prior pseudo-samples)."""
        p = 0.0
        for kk in reversed(s.parents(k)):
            e = s.c.get(kk)
            if e is None: continue
            if t > e[0]: s._e(kk, t)
            p = (s._interp(e[2], w) + A.prior * p) / (e[1] + A.prior)
        return p
    def n(s, k): e = s.c.get(k); return e[1] if e else 0.0
    def rate(s, k): e = s.c.get(k); return (e[3] / s.tau4) if e else 0.0
    def snapshot(s, t):
        out = {}
        for k, e in s.c.items():
            s._e(k, t); out["/".join("-" if x is None else str(x) for x in k)] = dict(n=round(e[1], 1), rate=round(e[3] / s.tau4, 4), F=[round(x / max(1e-9, e[1]), 3) for x in e[2]])
        return out

def run(policy, cap):
    base = policy.split("+")[0]
    use_ghost = base in ("2nd", "2nd_int", "adaptive", "adapt2") or A.shadow
    feats = ["c"] if base == "adapt2" else FEAT
    ghost = Ghost(cap); tab = Tables() if (base in ("adaptive", "adapt2", "2nd_int") or A.shadow) else None
    # ---- resident structures ----
    lru = OD(); where = {}                                                               # where[h] = True for every resident block (all policies)
    prob = OD(); prot = OD()                                                             # slru / wtinylfu main
    aT1 = OD(); aT2 = OD(); B1 = OD(); B2 = OD(); arc_p = [0.0]                            # arc
    A1in = OD(); A1out = OD(); Am = OD(); KIN = max(1, int(A.kin * cap)); KOUT = max(1, int(A.kout * cap))   # 2q
    win = OD(); WCAP = max(1, int(A.window * cap)); MAIN = cap - WCAP; PROBC = max(1, int(0.2 * MAIN))        # wtinylfu
    freq = {}; door = set(); incs = [0]; SAMPLE = int(A.tlfu_sample * cap)              # tinylfu sketch (exact 4-bit counts)
    heap = []; nuv = {}                                                                  # oracle
    rmeta = {}                                                                           # resident block -> [last touch t, touches so far, class]
    pend = {}; pend_dl = []                                                              # policy-independent labels in flight: hash -> (t0, class); deadlines
    hit_lbl = {}                                                                         # hitbe labels: resident block -> class (unlabelled yet)
    cls_stat = collections.defaultdict(lambda: [0.0, 0.0, None]); blk_cls = {}; blk_hit = {}   # lhd (previous round's learned class policy)
    seen_all = set(); known = set()                                                      # truth: every hash ever looked up; known: hashes the host side has seen
    res_ew = [None]; adm_rate = [0.0, None]; thr = [0.0]; plan_t = [-INF]; plan_log = []
    st = collections.Counter(); st_res = []; hits_f = [0] * 5; acc_f = [0] * 5; served_f = [0] * 5
    stored_at = {}; last_state = {}; last_idx = {}; n_dead = [0]; occ = [0.0, 0.0]; last_t = [None]
    hitlog = bytearray() if A.dump_hits else None; admlog = bytearray() if A.dump_admit else None; tab_dumps = {}
    gpu = OD(); GPU = A.gpu_blocks
    cur = [-1]; req_hs = []; req_new = []; usable = [True]; req_old = [0]; prev_ok = [True]; cold_done = [False]
    reuse = False; c_ = 0; dt_ = None; k = None
    def dec(st_, t):
        if st_[2] is not None and t > st_[2]: f = math.exp(-(t - st_[2]) / (4 * A.tau)); st_[0] *= f; st_[1] *= f
        st_[2] = t if st_[2] is None else max(st_[2], t)
    def rate_(st_, t, prior, kk=20.0): dec(st_, t); return (st_[0] + kk * prior) / (st_[1] + kk)
    def residence(t):
        if A.fixed_w > 0: return A.fixed_w
        if A.res_mode == "rate": return cap / max(1e-6, adm_rate[0] / (4 * A.tau)) if adm_rate[1] is not None else INF
        return res_ew[0] if res_ew[0] is not None else INF
    def note_adm(t):
        if adm_rate[1] is not None: adm_rate[0] *= math.exp(-(t - adm_rate[1]) / (4 * A.tau))
        adm_rate[0] += 1.0; adm_rate[1] = t
    def scored(i): ri = acc[i][2]; return LO <= ri < HI and R[ri]["task"] >= 0
    # ---- eviction / admission hooks (accounting) ----
    def on_evict(h, t):
        where.pop(h, None); lru.pop(h, None); prob.pop(h, None); prot.pop(h, None); nuv.pop(h, None)
        m = rmeta.pop(h, None)
        if m is not None and use_ghost and ghost.bloom is None: ghost.put(h, m)
        if base == "lhd":
            if not blk_hit.get(h, False) and t <= FREEZE_T and h in blk_cls: st_ = cls_stat[blk_cls[h]]; dec(st_, t); st_[1] += 1
            blk_hit.pop(h, None); blk_cls.pop(h, None)
        if A.label == "hitbe" and tab is not None and h in hit_lbl: tab.label(hit_lbl.pop(h), t, INF)
        last_state[h] = "evicted"; st["evict"] += 1; st["evict_live"] += (nu[last_idx[h]] < INF)
        if nu[last_idx[h]] == INF: n_dead[0] -= 1
        if h in stored_at:
            age = t - stored_at.pop(h)
            if len(st_res) < 300000: st_res.append(age)
            res_ew[0] = age if res_ew[0] is None else res_ew[0] + (age - res_ew[0]) / 200.0
    def on_admit(h, t, i, kk):
        where[h] = True; stored_at[h] = t; last_state[h] = None; st["written"] += 1; note_adm(t)
        if use_ghost: ghost.pop(h)
        rmeta[h] = [t, min(3, c_ + 1), kk]
        if nu[i] == INF: st["admit_never"] += 1; n_dead[0] += 1
        if A.label == "hitbe" and tab is not None: hit_lbl[h] = kk
        if admlog is not None and scored(i) and not reuse: admlog.append(1)
    def bypass(h, t, i):
        st["bypass"] += 1; last_state[h] = "bypassed"
        if nu[i] < INF:
            st["bypass_reused"] += 1; d_ = acc[nu[i]][0] - t; st["bypass_reused_60"] += (d_ <= 60); st["bypass_reused_300"] += (d_ <= 300)
        if admlog is not None and scored(i) and not reuse: admlog.append(0)
        if use_ghost:
            if ghost.bloom is None: ghost.put(h, [t, min(3, c_ + 1), k])
            else: ghost.bloom_put(h)
    # ---- the LRU-family cache (lru, slru, 2nd*, adaptive, lhd, tinylfu, oracle) ----
    def lru_victim(t):
        if base == "slru": return next(iter(prob)) if prob else next(iter(prot))
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
        if base == "slru": prob[h] = True
        if base == "oracle": nuv[h] = nu[i]; heapq.heappush(heap, (-nu[i], h))
        if use_ghost and ghost.bloom is not None: ghost.bloom_put(h)
    def lru_hit(h, t, i):
        lru.move_to_end(h)
        if base == "slru":
            if h in prot: prot.move_to_end(h)
            else:
                prob.pop(h, None); prot[h] = True
                while len(prot) > cap // 3: d_, _ = prot.popitem(last=False); prob[d_] = True
        if base == "oracle": nuv[h] = nu[i]; heapq.heappush(heap, (-nu[i], h))
    # ---- ARC (Megiddo & Modha 2003) ----
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
    # ---- 2Q (Johnson & Shasha 1994; Kin = 25%, Kout = 50% of the capacity) ----
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
    # ---- TinyLFU sketch (Einziger & Friedman): 4-bit counts, halved every `sample` increments, doorkeeper for first occurrences ----
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
    # ---- class features (adaptive) ----
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
    def replan(t):
        """threshold on P(re-lookup within the residence) that maximizes the predicted hit rate: order the classes by that
        probability at the current residence, evaluate the nested admitted sets with the residence they would produce
        (capacity / their candidate rate), keep the best (adapt2: the same with the two classes first touch / re-seen)."""
        Rn = residence(t)
        if Rn == INF: thr[0] = 0.0; return
        leaves = [(kk, tab.rate(kk)) for kk in tab.c if None not in kk]; leaves = [(kk, lam) for kk, lam in leaves if lam > 0]
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
        for b in reversed(req_hs):                                                       # LMCache / vLLM order: the tail is evicted first
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
        j = len(req_hs); req_hs.append(h)
        test = scored(i); f_ = min(4, int(5 * (ri - LO) / max(1, HI - LO))) if test else 0
        reuse = h in seen_all
        if test:
            acc_f[f_] += 1; st["acc"] += 1; st["reuse"] += reuse
            if last_t[0] is not None and where: dt = t - last_t[0]; occ[0] += dt * len(where); occ[1] += dt * n_dead[0]
        last_t[0] = t
        # ---- GPU front cache (vLLM's prefix cache): a block served there never reaches the host cache ----
        gpu_hit = False
        if GPU:
            if h in gpu: gpu.move_to_end(h); gpu_hit = True
            else:
                gpu[h] = True
                if len(gpu) > GPU: gpu.popitem(last=False)
        visible = not (gpu_hit and A.ghost_src == "host")
        # ---- history features of this touch (before the update) ----
        m = rmeta.get(h) or ((ghost.get(h, t) if ghost.bloom is None else None) if use_ghost else None)
        if use_ghost and ghost.bloom is not None and m is None: c_, dt_ = ((1, None) if ghost.bloom_has(h) else (0, None))
        else: c_, dt_ = ((m[1], t - m[0]) if m else (0, None))
        if use_ghost and visible and m is None and reuse and ghost.bloom is None: st["ghost_forgot"] += 1   # a re-lookup the bounded ghost no longer recognizes
        if use_ghost and ghost.bloom is not None and not reuse and c_ == 1: st["bloom_fp"] += 1
        root = R[ri]["hashes"][0]; k = cls_of(c_, dt_, j, req_old[0], root) if tab is not None else None
        # ---- policy-independent labels: was this hash looked up again within w? ----
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
        # ---- lookup ----
        if hitlog is not None and test: hitlog.append(1 if (h in where or gpu_hit) else (2 if last_state.get(h) == "bypassed" else 3 if last_state.get(h) == "evicted" else 0))
        hit = False
        if not gpu_hit and h in where:
            hit = True
            if base in ("lru", "slru", "2nd", "2nd_int", "adaptive", "adapt2", "lhd", "tinylfu", "oracle"): lru_hit(h, t, i)
            elif base == "arc": arc_access(h, t, i, k)
            elif base == "2q": q2_access(h, t, i, k)
            elif base == "wtinylfu": wtl_access(h, t, i, k)
            if base == "lhd" and not blk_hit.get(h, False) and t <= FREEZE_T and h in blk_cls: blk_hit[h] = True; st_ = cls_stat[blk_cls[h]]; dec(st_, t); st_[0] += 1; st_[1] += 1
            mm = rmeta[h]; mm[0] = t; mm[1] = min(3, mm[1] + 1)
            was_dead = nu[last_idx.get(h, i)] == INF; now_dead = nu[i] == INF
            if was_dead and not now_dead: n_dead[0] -= 1
            if not was_dead and now_dead: n_dead[0] += 1
        last_idx[h] = i
        served = hit or gpu_hit
        if test:
            if hit: st["hit"] += 1; hits_f[f_] += 1
            if gpu_hit: st["gpu_hit"] += 1
            if served:
                st["served"] += 1; served_f[f_] += 1
                if usable[0]: st["usable"] += 1; st["usable_tok"] += TOK; st["ttft"] += A.l * TOK
            else:
                st["miss"] += 1; ls_ = last_state.get(h)
                st["miss_bypassed" if ls_ == "bypassed" else "miss_evicted" if ls_ == "evicted" else "miss_new"] += 1
                if usable[0]:
                    usable[0] = False; rem = (R[ri]["L"] or len(R[ri]["hashes"]) * TOK) - j * TOK; st["ttft"] += A.r0 * rem + A.r1 * (rem * rem / 2 + j * TOK * rem)
        seen_all.add(h)
        if visible: known.add(h)
        if hit or (gpu_hit and h in where): prev_ok[0] = True; continue
        if tab is not None and visible: tab.cand(k, t)
        # ---- admission (the block is not in the host cache; LMCache's store path offers it) ----
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
        admit = True; cl = None
        if base == "2nd": admit = (c_ >= 1) or j == 0
        elif base == "2nd_int":
            Rn = residence(t); admit = (c_ >= 1 and (dt_ is None or dt_ <= Rn)) or j == 0
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
    st_res.sort(); n_cls = len([kk for kk in (tab.c if tab is not None else {}) if None not in kk])
    return dict(policy=policy, cap=cap, cap_GiB=round(cap * BLOCK_MB / 1024, 1), ghost=A.ghost, ghost_ttl=A.ghost_ttl, ghost_bloom=A.ghost_bloom, gpu_blocks=GPU, ghost_src=A.ghost_src, feat=A.feat, label=A.label, fixed_th=A.fixed_th, fixed_w=A.fixed_w, res_mode=A.res_mode, chain=not A.no_chain, tau=A.tau, replan=A.replan, prior=A.prior, freeze_at=A.freeze_at, cold_start=A.cold_start, score_range=A.score_range,
                acc=st["acc"], reuse=st["reuse"], hits=st["hit"], gpu_hits=st["gpu_hit"], served=st["served"], usable=st["usable"], usable_hit_share=st["usable"] / max(1, st["reuse"]), reuse_hit_share=st["hit"] / max(1, st["reuse"]), served_share=st["served"] / max(1, st["reuse"]),
                misses=st["miss"], recomputed_tokens=st["miss"] * TOK, usable_tokens=st["usable_tok"], ttft_s=round(st["ttft"], 2),
                written_chunks=st["written"], written_TB=round(st["written"] * BLOCK_MB / 1e6, 3), bypass_total=st["bypass"], bypass_reused_later=st["bypass_reused"], bypass_reused_60s=st["bypass_reused_60"], bypass_reused_300s=st["bypass_reused_300"],
                admitted_never_reused=st["admit_never"], miss_after_bypass=st["miss_bypassed"], miss_after_eviction=st["miss_evicted"], miss_new=st["miss_new"], evictions=st["evict"], evictions_before_reuse=st["evict_live"],
                residence_p50_s=(st_res[len(st_res) // 2] if st_res else None), residence_est_end_s=(round(residence(acc[-1][0]), 1) if residence(acc[-1][0]) < INF else None), dead_occupancy_share=occ[1] / max(1e-9, occ[0]),
                hits_by_fifth="/".join(map(str, hits_f)), served_by_fifth="/".join(map(str, served_f)), acc_by_fifth="/".join(map(str, acc_f)),
                ghost_entries_max=ghost.max, ghost_bytes=ghost.bytes(), ghost_forgotten_relookups=st["ghost_forgot"], bloom_false_positives=st["bloom_fp"], pending_labels_max=st["pend_max"], classes=n_cls, table_bytes=(len(tab.c) * (len(WG) + 3) * 8 if tab is not None else 0),
                threshold_end=round(thr[0], 3), replans=len(plan_log))

os.makedirs(A.out, exist_ok=True); rows = []
for cap in (int(x) for x in A.caps.split(",")):
    for p in A.policies.split(","):
        r = run(p, cap); rows.append(r)
        print(f"cap {cap:6d} ({r['cap_GiB']:6.1f} GiB) {p:12s} usable {r['usable_hit_share']:.3f} served {r['served_share']:.3f} hits {r['hits']:7d} usable_n {r['usable']:7d} written {r['written_chunks']:7d} bypass {r['bypass_total']:7d} res {r['residence_p50_s']} est {r['residence_est_end_s']} ghost {r['ghost_entries_max']} forgot {r['ghost_forgotten_relookups']} fp {r['bloom_false_positives']} thr {r['threshold_end']}", flush=True)
with open(f"{A.out}/{A.tag}-replay.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("wrote", f"{A.out}/{A.tag}-replay.csv")
