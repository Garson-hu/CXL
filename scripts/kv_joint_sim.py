#!/usr/bin/env python3
"""Joint benefit simulator: reuse value × DRAM/CXL movement cost (Phase 3, 2026-10-21).

A host KV cache of two tiers (DRAM D blocks + CXL X blocks, single copy, per-tier LRU or SLRU, tail-first order,
prefix-aware usable hits on the second half of the requests) fed by a Mooncake trace replayed at `--speed` (1x / 4x /
8x time compression; 8B 67.1 MB or 70B 167.8 MB blocks). Resource model from the c28 measurements (see the experiment
file's Model section): the CXL path is one FIFO server of --cxl-gbps (46 GB/s measured for the two cards); a store is
a hit only after it completed (pending miss, as kvemu2); DRAM stores drain at --dram-gbps (150, never binding) and are
gated by a token bucket (refill --budget GB/s, depth --depth blocks); the neighbour's p99 slowdown is interpolated
from the 2026-10-12 calibration as a function of the mean DRAM write rate (hash-placed "bursty" writes vs
budget-smoothed writes; beside the Adam step or the DRAM reader); an optional checkpoint stream shares the CXL path.
Online reuse information (RQ1 only, no future): seen before / touches / last gap (ghost), residence (EWMA of dead
eviction ages), class rate P(re-lookup within residence | touches, gap bucket) from policy-independent labels, the
first-touch-horizon regime rule. Oracles use the future and are marked.
Policies: split_lru split_slru value_split cost_budget indep indep_nodrop joint joint_hash joint_nodrop joint_2nd oracle_cost oracle_joint oracle_free
usage: kv_joint_sim.py <trace.jsonl> <out_dir> <tag> --mooncake [--speed 4] [--block-mb 67.1] [--policies ...] [options]"""
import zlib
import argparse, collections, csv, heapq, json, math, os
OD = collections.OrderedDict
ap = argparse.ArgumentParser()
ap.add_argument("trace"); ap.add_argument("out"); ap.add_argument("tag"); ap.add_argument("--mooncake", action="store_true")
ap.add_argument("--speed", type=float, default=1.0, help="time compression (1, 4, 8): wall time = trace time / speed")
ap.add_argument("--block-mb", type=float, default=67.1, help="67.1 (8B) or 167.8 (70B) MB per 512-token block"); ap.add_argument("--tok", type=int, default=512)
ap.add_argument("--dram-gib", type=float, default=64.0); ap.add_argument("--cxl-gib", type=float, default=136.0)
ap.add_argument("--cxl-gbps", type=float, default=46.0, help="CXL store capacity, GB/s (measured ~46 for the two cards)")
ap.add_argument("--dram-gbps", type=float, default=150.0, help="DRAM store drain rate, GB/s (emulator ceiling; never binding)")
ap.add_argument("--budget", type=float, default=32.0, help="DRAM write budget: token-bucket refill, GB/s")
ap.add_argument("--depth", type=float, default=1.0, help="DRAM write budget: bucket depth in blocks")
ap.add_argument("--budget-off", type=float, default=32.0, help="budget while the neighbour is paused (--phases)")
ap.add_argument("--phases", default="", help="neighbour on/off phases, wall seconds 'on,off' (e.g. 30,30); p99 is evaluated over on phases only")
ap.add_argument("--neighbour", default="adam", choices=["adam", "reader", "none"])
ap.add_argument("--split-share", type=float, default=0.32, help="hash share of admitted blocks that go to DRAM under split placement")
ap.add_argument("--qmax", type=float, default=2.0, help="CXL backlog (seconds of work) above which stores are dropped (congestion control)")
ap.add_argument("--qpri", type=float, default=0.5, help="joint: CXL backlog above which the DRAM budget is reserved for high-value blocks")
ap.add_argument("--vth", type=float, default=0.5, help="joint: high-value threshold on P(re-lookup within residence)")
ap.add_argument("--qhard-mult", type=float, default=4.0, help="joint: high-value stores are dropped only above qmax × this")
ap.add_argument("--ckpt", default="", help="checkpoint stream 'GiB,period_s,mode' with mode fifo | kvprio | joint (joint: KV-priority for high-value stores, low-value stores dropped during the burst)")
ap.add_argument("--policies", default="split_lru,value_split,cost_budget,indep,joint,oracle_cost")
ap.add_argument("--score-range", default="0.5,1.0"); ap.add_argument("--tau", type=float, default=300.0, help="decay of the online statistics (trace seconds, applied as 4 tau)")
ap.add_argument("--replan", type=float, default=10.0, help="regime re-evaluation interval (trace seconds)"); ap.add_argument("--regime-q", type=float, default=0.5); ap.add_argument("--regime-hold", type=float, default=30.0)
ap.add_argument("--r0", type=float, default=0.000134); ap.add_argument("--r1", type=float, default=9.4e-9); ap.add_argument("--l", type=float, default=0.000005)
ap.add_argument("--migrate", action="store_true", help="variant: promote a CXL block to DRAM on its first CXL hit when the DRAM budget has credit (counted as a DRAM write and a CXL read)")
ap.add_argument("--prefill-tps", type=float, default=7300.0, help="per-request prefill rate (tokens/s): the j-th block of a request is offered to the host cache j × tok / prefill_tps s after the request (physical, not scaled by --speed), as in kvemu2")
ap.add_argument("--dump-hits", default=""); ap.add_argument("--series", default="", help="write per-wall-second series (DRAM/CXL GB written, backlog GB, drops, hits) to <path>-<policy>.json")
A = ap.parse_args(); INF = float("inf"); TOK = A.tok; BYTES = A.block_mb * 1e6

def hfrac(h):   # hash share in [0, 1): hex ids (Mooncake) as before; non-hex ids (constructed traces: 'c0', 't0', ...) via crc32 (added 2026-10-21 after the mix runs crashed)
    try: return (int(h[-12:], 16) % 1000) / 1000.0
    except ValueError: return (zlib.crc32(h.encode()) % 1000) / 1000.0
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
T0, T1 = R[0]["t"], R[-1]["t"]
D_BLOCKS = int(A.dram_gib * 2 ** 30 / BYTES); X_BLOCKS = int(A.cxl_gib * 2 ** 30 / BYTES); CAP = D_BLOCKS + X_BLOCKS
WG = [15.0, 30.0, 60.0, 120.0, 240.0, 480.0, 960.0]; WMAX = WG[-1]
# ---- interference model: neighbour p99 slowdown (%) vs mean DRAM write rate (GB/s), measured 2026-10-12 beside Adam (split = hash-placed, budget = token-bucket) and the DRAM reader ----
CURVE = {("adam", "bursty"): [(0, 0), (1.3, 1.2), (2.8, 2.6), (4.4, 4.1), (6.1, 5.6), (7.7, 6.4), (9.3, 7.7), (11.7, 9.2), (12.3, 9.3), (15.7, 13.5), (18.9, 14.7), (23.7, 21.7)],
         ("adam", "smooth"): [(0, 0), (1.6, 1.3), (2.5, 2.1), (3.9, 2.9), (4.6, 3.1), (5.4, 3.5), (6.6, 4.5), (7.5, 5.4), (8.4, 6.6), (8.9, 6.8), (9.8, 7.3), (11.0, 8.9), (11.2, 7.7), (13.1, 9.1), (14.8, 10.7)],
         ("reader", "bursty"): [(0, 0), (1.3, 0.7), (2.8, 1.9), (6.1, 1.4), (9.3, 2.6), (12.3, 3.9), (15.7, 4.0), (18.9, 5.3), (23.7, 8.3)],
         ("reader", "smooth"): [(0, 0), (2.5, 1.3), (4.6, 2.0), (6.6, 2.6), (8.9, 2.6), (9.8, 2.0), (14.8, 3.5), (24.0, 6.0)]}
def p99_of(rate, kind):
    if A.neighbour == "none": return 0.0, False
    pts = sorted(CURVE[(A.neighbour, kind)]); extrap = rate > pts[-1][0]
    if extrap: (x0, y0), (x1, y1) = pts[-2], pts[-1]; return y1 + (rate - x1) * (y1 - y0) / max(1e-9, x1 - x0), True
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if rate <= x1: return y0 + (rate - x0) * (y1 - y0) / max(1e-9, x1 - x0), False
    return pts[-1][1], False

class Tables:
    """policy-independent re-lookup labels per class (touches 0..3, gap bucket), decayed; candidate rates."""
    def __init__(s): s.tau4 = 4 * A.tau; s.c = {}
    @staticmethod
    def parents(k): return [k, (k[0], None), (None, None)]
    def _e(s, k, t):
        e = s.c.get(k)
        if e is None: e = s.c[k] = [t, 0.0, [0.0] * len(WG), 0.0]
        elif t > e[0]:
            f = math.exp(-(t - e[0]) / s.tau4); e[1] *= f; e[3] *= f
            for i in range(len(WG)): e[2][i] *= f
            e[0] = t
        return e
    def cand(s, k, t):
        for kk in s.parents(k): s._e(kk, t)[3] += 1.0
    def label(s, k, t, dt):
        for kk in s.parents(k):
            e = s._e(kk, t); e[1] += 1.0
            for i, w in enumerate(WG):
                if dt <= w: e[2][i] += 1.0
    @staticmethod
    def interp(cw, w):
        if w <= WG[0]: return cw[0] * w / WG[0]
        if w >= WG[-1]: return cw[-1]
        for i in range(1, len(WG)):
            if w <= WG[i]:
                a = (math.log(w) - math.log(WG[i - 1])) / (math.log(WG[i]) - math.log(WG[i - 1])); return cw[i - 1] + a * (cw[i] - cw[i - 1])
        return cw[-1]
    def F(s, k, w, t, prior=10.0):
        p = 0.0
        for kk in reversed(s.parents(k)):
            e = s.c.get(kk)
            if e is None: continue
            if t > e[0]: s._e(kk, t)
            p = (s.interp(e[2], w) + prior * p) / (e[1] + prior)
        return p
    def raw(s, k, t):
        e = s.c.get(k)
        if e is None: return 0.0, [0.0] * len(WG)
        if t > e[0]: s._e(k, t)
        return e[1], list(e[2])
    def rate(s, k, t):
        e = s.c.get(k)
        if not e: return 0.0
        return e[3] / max(1e-9, s.tau4 * (1.0 - math.exp(-max(1e-6, t - T0) / s.tau4)))

def run(policy):
    P = policy
    adm = {"split_lru": "all", "split_slru": "all", "value_split": "value", "cost_budget": "all", "indep": "value", "indep_nodrop": "value", "joint": "value", "joint_hash": "value", "joint_nodrop": "value", "joint_2nd": "2nd", "oracle_cost": "oracle", "oracle_joint": "oracle", "oracle_free": "oracle"}[P]
    plc = {"split_lru": "split", "split_slru": "split", "value_split": "split", "oracle_free": "split"}.get(P, "budget")
    struct = "lru" if P == "split_lru" else "slru"
    joint = P.startswith("joint") or P == "oracle_joint"; vplace = joint and P != "joint_hash"; drop = P not in ("joint_nodrop", "indep_nodrop", "oracle_free") and plc == "budget"
    cxl_gbps = INF if P == "oracle_free" else A.cxl_gbps
    # ---- tiers ----
    where = {}; lists = [OD(), OD()]; prob = [OD(), OD()]; prot = [OD(), OD()]; nslot = [D_BLOCKS, X_BLOCKS]; n = [0, 0]
    rmeta = {}; ghost = {}; stored_at = {}; writing = {}                                   # writing[h] = wall completion time of a store in flight
    last_state = {}; last_idx = {}; tab = Tables() if adm in ("value", "2nd") or joint else None
    pend = {}; pend_dl = []; est_dead = [None]; regime = ["filter"]; cand_since = [None]; plan_t = [-INF]; switches = []
    heap = []; nuv = {}                                                                     # oracle
    # ---- write path ----
    srv_free = [0.0]; kvq = []; ckq = []; seqn = [0]; q_bytes = [0.0]; pend_st = []; announced = set()   # heaps of (offer time, seq, bytes, hash|None); pending stores
    credit = [A.depth * BYTES]; credit_t = [0.0]; vq = collections.deque(maxlen=2000); vth_dyn = [0.0]; vcount = [0]
    st = collections.Counter(); st_f = collections.Counter(); st_res = []; ser = collections.defaultdict(lambda: [0.0, 0.0, 0.0, 0, 0])   # per wall second: dram GB, cxl GB, backlog max, drops, hits
    hitlog = bytearray() if A.dump_hits else None
    ck_log = []; ck_next = [A_ck[1] if A_ck else INF]
    ph_on, ph_off = ((float(x) for x in A.phases.split(",")) if A.phases else (INF, 0.0)); ph_on = float(ph_on); ph_off = float(ph_off)
    def wall(t): return (t - T0) / A.speed
    def neigh_on(w): return A.phases == "" or (w % (ph_on + ph_off)) < ph_on
    def budget_now(w): return A.budget if neigh_on(w) else A.budget_off
    # ---- CXL server (event driven, lazily advanced) ----
    def push(q, we, b, h): seqn[0] += 1; heapq.heappush(q, (we, seqn[0], b, h)); q_bytes[0] += b
    def advance(now):
        """serve pieces in offer order, never before their offer time, until the server is busy past `now`; KV first when the checkpoint mode gives it priority."""
        while srv_free[0] <= now:
            kv_ok = bool(kvq) and kvq[0][0] <= now; ck_ok = bool(ckq) and ckq[0][0] <= now
            if not kv_ok and not ck_ok: break
            use_kv = kv_ok if not (kv_ok and ck_ok) else (ck_mode in ("kvprio", "joint") or kvq[0][0] <= ckq[0][0])
            we, _, b, h = heapq.heappop(kvq if use_kv else ckq); q_bytes[0] -= b
            start = max(srv_free[0], we); done = start + b / (cxl_gbps * 1e9); srv_free[0] = done
            if h is not None: writing[h] = done
            else:
                for e in ck_log:
                    if e[2] < e[1]:
                        e[2] += 1
                        if e[2] == e[1]: e[3] = done
                        break
    def backlog_s(now): return max(0.0, srv_free[0] - now) + q_bytes[0] / (cxl_gbps * 1e9)
    def dead_evict_age(age):
        est_dead[0] = age if est_dead[0] is None else est_dead[0] + (age - est_dead[0]) / 200.0
    def residence(): return est_dead[0] if est_dead[0] is not None else INF
    # ---- eviction / placement ----
    oheap = [[], []]
    def victim(tier):
        if P.startswith("oracle"):
            while oheap[tier]:
                negn, b = oheap[tier][0]
                if where.get(b) == tier and nuv.get(b) == -negn: heapq.heappop(oheap[tier]); return b
                heapq.heappop(oheap[tier])
            return next(iter(lists[tier]))
        if struct == "slru": return next(iter(prob[tier])) if prob[tier] else next(iter(prot[tier]))
        return next(iter(lists[tier]))
    def evict(h, t):
        tier = where.pop(h); n[tier] -= 1; lists[tier].pop(h, None); prob[tier].pop(h, None); prot[tier].pop(h, None); nuv.pop(h, None); writing.pop(h, None)
        m = rmeta.pop(h, None)
        if m is not None: ghost[h] = m
        last_state[h] = "evicted"; st["evict"] += 1
        if h in stored_at:
            age = t - stored_at.pop(h)
            if m is not None and not m[3]: dead_evict_age(age)
            if len(st_res) < 300000: st_res.append(age)
    def place(h, tier, t, w, i, c_, k, pending_done):
        if n[tier] >= nslot[tier]: evict(victim(tier), t)
        where[h] = tier; n[tier] += 1; lists[tier][h] = True
        if struct == "slru": prob[tier][h] = True
        rmeta[h] = [t, min(3, c_ + 1), k, False]; stored_at[h] = t; last_state[h] = None; ghost.pop(h, None)
        if pending_done is not None: writing[h] = pending_done
        if nu[i] == INF: st["admit_never"] += 1
        if scored(i): st["written_" + ("dram" if tier == 0 else "cxl")] += 1; ser[int(w)][tier] += BYTES / 1e9
        if P.startswith("oracle"): nuv[h] = nu[i]; heapq.heappush(heap, (-nu[i], h)); heapq.heappush(oheap[tier], (-nu[i], h))
    def hit_touch(h, tier):
        lists[tier].move_to_end(h)
        if struct == "slru":
            if h in prot[tier]: prot[tier].move_to_end(h)
            else:
                prob[tier].pop(h, None); prot[tier][h] = True
                while len(prot[tier]) > nslot[tier] // 3: d_, _ = prot[tier].popitem(last=False); prob[tier][d_] = True
    def scored(i): ri = acc[i][2]; return LO <= ri < HI and R[ri]["task"] >= 0
    def bypass(h, t, i, c_, k, why, ws=None):
        st["bypass"] += 1; st["bypass_" + why] += 1; last_state[h] = "bypassed"; ghost[h] = [t, min(3, c_ + 1), k, False]
        if nu[i] < INF: st["bypass_reused"] += 1
        if why == "drop" and scored(i): ser[int(ws)][3] += 1
    def process_stores(now):
        """stores whose offer time has come: placement (bucket / queue / drop) at the offer time, in offer order."""
        while pend_st and pend_st[0][0] <= now:
            ws, _, h, i, c_, k, hv, t = heapq.heappop(pend_st); announced.discard(h)
            if h in where: continue
            advance(ws); bl = backlog_s(ws) if cxl_gbps < INF else 0.0
            hsel = hfrac(h) < A.split_share                                                   # hash share: value-blind DRAM candidates
            if plc == "split": tier_to = 0 if nslot[0] > 0 and hsel else 1
            else:
                credit[0] = min(A.depth * BYTES, credit[0] + budget_now(ws) * 1e9 * max(0.0, ws - credit_t[0])); credit_t[0] = max(credit_t[0], ws)
                if vplace:                                                                  # joint: the top split_share fraction by value are the DRAM candidates (online quantile)
                    vq.append(hv); vcount[0] += 1
                    if vcount[0] % 100 == 0 and len(vq) >= 200: srt = sorted(vq); vth_dyn[0] = srt[max(0, len(srt) - 1 - int(A.split_share * len(srt)))]
                    cand = hv >= vth_dyn[0] and vth_dyn[0] > 0
                else: cand = hsel
                want_dram = cand and credit[0] >= BYTES and nslot[0] > 0
                high = hv >= max(A.vth, vth_dyn[0]) if P != "oracle_joint" else hv >= vth_dyn[0]
                if joint and want_dram and bl > A.qpri and not high: want_dram = False
                tier_to = 0 if want_dram else 1
                if tier_to == 0: credit[0] -= BYTES
            if tier_to == 1 and cxl_gbps < INF:
                if drop:
                    high = hv >= max(A.vth, vth_dyn[0]) if P != "oracle_joint" else hv >= vth_dyn[0]
                    lim = A.qmax * (A.qhard_mult if (joint and high) else 1.0)
                    if A_ck and ck_mode == "joint" and ckq and not high: lim = 0.0
                    if bl > lim: bypass(h, t, i, c_, k, "drop", ws); continue
                push(kvq, ws, BYTES, h); advance(ws); place(h, 1, t, ws, i, c_, k, writing.get(h, INF))
            elif tier_to == 1: place(h, 1, t, ws, i, c_, k, ws)
            else: place(h, 0, t, ws, i, c_, k, ws + BYTES / (A.dram_gbps * 1e9))
            if cxl_gbps < INF: ser[int(ws)][2] = max(ser[int(ws)][2], bl * A.cxl_gbps)
    def two_class(t):
        lam_f = tab.rate((0, None), t); nf, cf = tab.raw((0, None), t); lam_r = 0.0; nr = 0.0; cr = [0.0] * len(WG)
        for c in (1, 2, 3):
            lam_r += tab.rate((c, None), t); n_, cw = tab.raw((c, None), t); nr += n_
            for j in range(len(WG)): cr[j] += cw[j]
        return lam_f, lam_r, nf, cf, nr, cr
    def regime_eval(t):
        lam_f, lam_r, nf, cf, nr, cr = two_class(t)
        if nf < 50 or nr < 50 or lam_f + lam_r <= 0: return
        R_all = CAP / (lam_f + lam_r); tot = cf[-1] / nf if nf > 0 else 0.0; target = A.regime_q * tot; Hq = INF
        for j, w_ in enumerate(WG):
            if cf[j] / nf >= target:
                if j == 0: Hq = w_
                else:
                    lo, hi = cf[j - 1] / nf, cf[j] / nf; a = (target - lo) / max(1e-9, hi - lo); Hq = math.exp(math.log(WG[j - 1]) + a * (math.log(w_) - math.log(WG[j - 1])))
                break
        want = "normal" if R_all >= Hq else "filter"
        if joint and want == "normal":                                                       # cost-aware regime: normal admission only if the path carries the full stream
            offered = (lam_f + lam_r) * A.speed * BYTES / 1e9
            if offered > A.cxl_gbps + budget_now(wall(t)): want = "filter"; st["regime_cost_veto"] += 1
        if want != regime[0]:
            if cand_since[0] is None: cand_since[0] = t
            elif t - cand_since[0] >= A.regime_hold: switches.append((round(wall(t), 1), want)); regime[0] = want; cand_since[0] = None
        else: cand_since[0] = None
    def end_request(req_hs):
        for b in reversed(req_hs):
            tier = where.get(b)
            if tier is None: continue
            lists[tier].move_to_end(b)
            if struct == "slru":
                if b in prot[tier]: prot[tier].move_to_end(b)
                elif b in prob[tier]: prob[tier].move_to_end(b)
    cur = -1; req_hs = []; usable = True; req_old = 0; known = set(); seen_all = set()
    for i, (t, h, ri) in enumerate(acc):
        w = wall(t)
        # ---- checkpoint stream ----
        if A_ck and w >= ck_next[0]:
            while w >= ck_next[0]:
                pieces = int(A_ck[0] * 2 ** 30 / (64 * 2 ** 20)); t_ck = ck_next[0]
                for _ in range(pieces): push(ckq, t_ck, 64 * 2 ** 20, None)
                ck_log.append([t_ck, pieces, 0, None]); ck_next[0] += A_ck[1]
        process_stores(w); advance(w)
        if ri != cur:
            end_request(req_hs); cur = ri; req_hs = []; usable = True; req_old = sum(1 for x in R[ri]["hashes"] if x in known)
            if tab is not None and adm == "value" and t - plan_t[0] >= A.replan: regime_eval(t); plan_t[0] = t
        j = len(req_hs); req_hs.append(h); test = scored(i); reuse = h in seen_all
        if test: st["acc"] += 1; st["reuse"] += reuse
        m = rmeta.get(h) or ghost.get(h)
        c_, dt_ = ((m[1], t - m[0]) if m else (0, None))
        k = (min(3, c_), (0 if dt_ is None else 1 if dt_ < 30 else 2 if dt_ < 120 else 3 if dt_ < 480 else 4))
        if tab is not None:
            while pend_dl and pend_dl[0][0] <= t:
                dl, hb, t0 = heapq.heappop(pend_dl); pb = pend.get(hb)
                if pb is not None and pb[0] == t0: pend.pop(hb); tab.label(pb[1], dl, INF)
            pb = pend.get(h)
            if pb is not None: pend.pop(h); tab.label(pb[1], t, t - pb[0])
            pend[h] = (t, k); heapq.heappush(pend_dl, (t + WMAX, h, t))
        # ---- lookup: resident and store completed ----
        tier = where.get(h); pending = h in announced; hit = tier is not None and writing.get(h, -INF) <= w
        if hitlog is not None and test: hitlog.append(1 if hit else (4 if (tier is not None or pending) else 2 if last_state.get(h) == "bypassed" else 3 if last_state.get(h) == "evicted" else 0))
        if hit:
            hit_touch(h, tier); mm = rmeta[h]; mm[0] = t; mm[1] = min(3, mm[1] + 1); mm[3] = True
            if P.startswith("oracle"): nuv[h] = nu[i]; heapq.heappush(heap, (-nu[i], h)); heapq.heappush(oheap[tier], (-nu[i], h))
            if A.migrate and tier == 1 and plc == "budget":                                 # variant: promote on the first CXL hit if the budget allows
                credit[0] = min(A.depth * BYTES, credit[0] + budget_now(w) * 1e9 * max(0.0, w - credit_t[0])); credit_t[0] = max(credit_t[0], w)
                if credit[0] >= BYTES and nslot[0] > 0:
                    credit[0] -= BYTES; where.pop(h); lists[1].pop(h, None); prob[1].pop(h, None); prot[1].pop(h, None); n[1] -= 1
                    if n[0] >= nslot[0]: evict(victim(0), t)
                    where[h] = 0; n[0] += 1; lists[0][h] = True
                    if struct == "slru": prot[0][h] = True
                    st["moves"] += 1
                    if test: st["written_dram"] += 1; st["cxl_read_moves"] += 1; ser[int(w)][0] += BYTES / 1e9
        if test:
            if hit: st["hit"] += 1; ser[int(w)][4] += 1
            else:
                st["miss"] += 1; st["miss_pending" if (tier is not None or pending) else "miss_bypassed" if last_state.get(h) == "bypassed" else "miss_evicted" if last_state.get(h) == "evicted" else "miss_new"] += 1
            if hit and usable: st["usable"] += 1; st["ttft"] += A.l * TOK
            elif not hit and usable: usable = False; rem = (R[ri]["L"] or len(R[ri]["hashes"]) * TOK) - j * TOK; st["ttft"] += A.r0 * rem + A.r1 * (rem * rem / 2 + j * TOK * rem)
        seen_all.add(h); known.add(h); last_idx[h] = i
        if tier is not None or pending: continue                                            # resident, being written or announced: nothing to admit
        if tab is not None: tab.cand(k, t)
        # ---- admission (whether) ----
        Rn = residence(); hv = 0.0
        if tab is not None: hv = tab.F(k, Rn if Rn < INF else WMAX, t)
        if P == "oracle_joint": hv = (1.0 / (1.0 + (acc[nu[i]][0] - t))) if nu[i] < INF else 0.0
        if adm == "all": admit = True
        elif adm == "2nd": admit = c_ >= 1 or j == 0
        elif adm == "value":
            if regime[0] == "normal": admit = True
            else: admit = (c_ >= 1 and (dt_ is None or dt_ <= Rn)) or j == 0
        else:                                                                               # oracle (future): admit only if reused before it would be evicted
            if nu[i] == INF: admit = False
            elif n[0] + n[1] + len(pend_st) >= CAP:
                while heap:
                    negn, b = heap[0]
                    if b in where and nuv.get(b) == -negn: break
                    heapq.heappop(heap)
                admit = not heap or -heap[0][0] > nu[i]
            else: admit = True
        if not admit: bypass(h, t, i, c_, k, "value"); continue
        seqn[0] += 1; heapq.heappush(pend_st, (w + j * TOK / A.prefill_tps, seqn[0], h, i, c_, k, hv, t)); announced.add(h); last_state[h] = "pending"
    end_request(req_hs); process_stores(INF); advance(INF)
    if hitlog is not None: open(f"{A.dump_hits}-{policy}.bin", "wb").write(bytes(hitlog))
    # ---- interference and summary ----
    w_lo, w_hi = wall(R[LO]["t"]), wall(R[min(HI, NR) - 1]["t"]); span = max(1e-9, w_hi - w_lo)
    dram_gb = sum(v[0] for s_, v in ser.items() if w_lo <= s_ < w_hi); cxl_gb = sum(v[1] for s_, v in ser.items() if w_lo <= s_ < w_hi)
    on_secs = [s_ for s_ in range(int(w_lo), int(w_hi)) if neigh_on(s_)]; on_span = max(1e-9, len(on_secs))
    dram_on = sum(ser[s_][0] for s_ in on_secs if s_ in ser); rate_on = dram_on / on_span
    kind = "bursty" if plc == "split" else "smooth"; p99, ex = p99_of(rate_on, kind)
    # worst minute (on phases)
    mins = collections.defaultdict(float)
    for s_ in on_secs:
        if s_ in ser: mins[s_ // 60] += ser[s_][0]
    worst_min = max(mins.values()) / 60.0 if mins else 0.0
    backlog_max = max((v[2] for s_, v in ser.items() if w_lo <= s_ < w_hi), default=0.0); drops = sum(v[3] for s_, v in ser.items() if w_lo <= s_ < w_hi)
    st_res.sort()
    ck_done = [e[3] - e[0] for e in ck_log if e[3] is not None and e[0] >= w_lo]; ck_unfinished = sum(1 for e in ck_log if e[3] is None)
    if A.series:
        json.dump([dict(s=s_, dram_gb=round(v[0], 3), cxl_gb=round(v[1], 3), backlog_gb=round(v[2], 2), drops=v[3], hits=v[4]) for s_, v in sorted(ser.items())], open(f"{A.series}-{policy}.json", "w"))
    return dict(policy=policy, speed=A.speed, block_mb=A.block_mb, dram_blocks=D_BLOCKS, cxl_blocks=X_BLOCKS, cxl_gbps=A.cxl_gbps, budget=A.budget, depth=A.depth, neighbour=A.neighbour, phases=A.phases, qmax=A.qmax, qpri=A.qpri, vth=A.vth, ckpt=A.ckpt, migrate=A.migrate, score_range=A.score_range,
                acc=st["acc"], reuse=st["reuse"], hits=st["hit"], usable=st["usable"], usable_hit_share=st["usable"] / max(1, st["reuse"]), misses=st["miss"], miss_pending=st["miss_pending"], miss_bypassed=st["miss_bypassed"], miss_evicted=st["miss_evicted"], miss_new=st["miss_new"],
                recomputed_tokens=st["miss"] * TOK, ttft_s=round(st["ttft"], 1),
                written_dram_blocks=st["written_dram"], written_cxl_blocks=st["written_cxl"], dram_GB=round(dram_gb, 1), cxl_GB=round(cxl_gb, 1), dram_rate_GBps=round(dram_gb / span, 3), dram_rate_on_GBps=round(rate_on, 3), dram_worst_minute_GBps=round(worst_min, 2), cxl_rate_GBps=round(cxl_gb / span, 3),
                neighbour_p99_pct=round(p99, 2), p99_extrapolated=ex, slo_ok=(p99 <= 7.0), curve=kind,
                cxl_backlog_max_GB=round(backlog_max, 2), bypass_value=st["bypass_value"], bypass_drop=drops, bypass_reused_later=st["bypass_reused"], admitted_never_reused=st["admit_never"], moves=st["moves"],
                regime_end=regime[0], regime_switches=len(switches), regime_cost_veto=st["regime_cost_veto"], residence_p50_s=(st_res[len(st_res) // 2] if st_res else None), residence_est_end_s=(round(residence(), 1) if residence() < INF else None),
                ckpt_n=len(ck_done), ckpt_unfinished=ck_unfinished, ckpt_completion_max_s=(round(max(ck_done), 2) if ck_done else None), ckpt_completion_mean_s=(round(sum(ck_done) / len(ck_done), 2) if ck_done else None), wall_span_s=round(span, 1))

A_ck = None; ck_mode = "fifo"
if A.ckpt:
    gib, per, ck_mode = A.ckpt.split(","); A_ck = (float(gib), float(per))
os.makedirs(A.out, exist_ok=True); rows = []
for p in A.policies.split(","):
    r = run(p); rows.append(r)
    print(f"{p:13s} usable {r['usable_hit_share']:.3f} hits {r['hits']:7d} pend {r['miss_pending']:6d} dram {r['dram_GB']:8.1f} GB ({r['dram_rate_on_GBps']:5.2f} GB/s on, worst min {r['dram_worst_minute_GBps']:5.2f}) cxl {r['cxl_GB']:8.1f} GB ({r['cxl_rate_GBps']:5.2f}) p99 {r['neighbour_p99_pct']:5.2f}%{'*' if r['p99_extrapolated'] else ''} backlog {r['cxl_backlog_max_GB']:7.1f} GB drops {r['bypass_drop']:6d} bypass {r['bypass_value']:7d} regime {r['regime_end']} ({r['regime_switches']} sw, veto {r['regime_cost_veto']}) ckpt {r['ckpt_completion_max_s']}", flush=True)
with open(f"{A.out}/{A.tag}-joint.csv", "w", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
print("wrote", f"{A.out}/{A.tag}-joint.csv")
