#!/usr/bin/env python3
"""Phase 1, Steps 2–4 of the research charter (2026-10-17): the value of FUTURE reuse information for a unified DRAM/CXL
KV cache, and how much of it simple ONLINE predictors recover. TRACE SIMULATION over the Mooncake traces (512-token
hash blocks); hits are counted when a block is resident at access time; no hardware speed enters the capacity-only
model. Effective capacity 200 GiB (DRAM 64 + CXL 136 GiB), 8B blocks of 64 MiB (70B: 160 MiB) unless changed.

Protocol: the trace's requests are split in two halves by count. Every policy runs over the whole trace (the first half
is its warm-up); metrics are counted on the SECOND half only (test segment). Online predictors are fitted on the first
half only — a block created in the first half is labelled "reused" only if its next use also lies in the first half —
and never see the test segment's future. Oracles use the full future by definition.

Policies (capacity-only unless --dram-budget is given):
  cxlfirst     Baseline A: every new block into CXL, LRU over CXL; DRAM unused (no migration)
  split        Baseline B: a fixed share of new blocks (by hash; default = DRAM's share of capacity) into DRAM; LRU per tier
  global_lru   Baseline C: one LRU over both tiers; a new block takes the slot the globally least-recently-used block
               frees (DRAM-first while slots are free) — no cross-tier relocation is ever needed
  reactive_mig Baseline D: CXL-first admission; a block hit in CXL is moved to DRAM (DRAM's LRU block is dropped, as in
               kvemu2's borrowmig), per-tier LRU; the move is unconstrained here (upper bound of reactive migration)
  oracle_min   Oracle E: Belady's MIN with bypass over the whole capacity — a new block with no future use is not
               stored; on a full cache the resident block with the farthest next use is evicted unless the new block's
               next use is farther still (then the new block is not stored). Optimal for hits at this capacity.
  oracle_h<H>  Oracle E with a horizon: a next use more than H seconds away counts as "never" (how far the oracle must see)
  oracle_mig   Oracle F: the decisions of E, plus tier assignment that keeps the blocks with the soonest next use in
               DRAM (on a CXL hit, swap with DRAM's farthest block). Hits are identical to E by construction (a hit is a
               hit in either tier); it reports the move volume and the DRAM-hit share such a policy would need.
  pred_admit   Step 4: admission filter — a new block is stored only if P(reused | continuation depth × position), fitted
               on the first half, is >= theta; LRU per tier with the split's share
  pred_evict   Step 4: eviction by past reuse count — classes by reuses so far (0, 1, 2, 3–4, 5+), LRU inside a class,
               evict from the lowest class first (one LRU over both tiers like global_lru)
  pred_both    both
  slru<p>      Step 4: segmented LRU over all slots using only past information — new blocks enter a probation segment,
               a block hit while in probation moves to a protected segment holding the share p of all slots (default 0.5;
               the protected LRU block is demoted to probation when the segment is full); eviction takes probation's LRU
               first. Segments are logical: no block moves between tiers (new blocks are placed CXL-first)
  slru_tier<p> the same, but the protected segment is DRAM physically: a promotion moves the block from CXL into DRAM
               and demotes DRAM's LRU protected block into CXL (both counted as moves) — the move volume a "DRAM holds
               the proven-reused blocks" policy would need
With --dram-budget B (GB/s) and --cxl-rate R (GB/s) the model becomes BANDWIDTH-CONSTRAINED: each store occupies its
tier's write pipe for bytes/rate seconds (FIFO); a block whose store has not completed is a miss (recomputed, not stored
again); DRAM is written only up to the budget (split/pred: a token bucket of <depth> blocks, else the block goes to CXL;
oracle_min: the same bucket). --speed scales the trace clock (4 = 4× faster arrivals), as in the emulation campaigns.

Metrics on the test segment: accesses, reuse accesses (the block was seen before, anywhere in the trace), hits (DRAM /
CXL), reuse-hit share, overall hit rate, compulsory and non-compulsory misses, recomputed tokens (misses × 512),
stores (GB to DRAM / CXL, bypassed count), evictions and premature evictions (evicted with a future use), moves (GB),
useful occupancy (share of resident blocks with a future use, sampled), pending misses (constrained model), estimated
prefill time per request (EST: recomputed tokens / 7300 tok/s + loads × 64 MiB / 9.5 GB/s, the real-run calibration).
usage: kv_oracle_study.py [--traces a,b] [--model 8b|70b] [--dram 64] [--cxl 136] [--policies ...] [--split-share 0.32]
                          [--theta 0.35] [--horizons 60,300,900,1800,3600] [--dram-budget GBps] [--cxl-rate 46] [--speed 1]
                          [--depth 4] [--out dir] [--tag name]"""
import argparse, collections, csv, heapq, json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); INF = float("inf"); TOK = 512
ap = argparse.ArgumentParser()
ap.add_argument("--traces", default="conversation,toolagent,synthetic"); ap.add_argument("--model", default="8b"); ap.add_argument("--dram", type=float, default=64); ap.add_argument("--cxl", type=float, default=136)
ap.add_argument("--policies", default="cxlfirst,split,global_lru,reactive_mig,oracle_min,oracle_h,oracle_mig,pred_admit,pred_evict,pred_both")
ap.add_argument("--split-share", type=float, default=-1); ap.add_argument("--theta", type=float, default=0.35); ap.add_argument("--slru-shares", default="0.5"); ap.add_argument("--horizons", default="60,300,900,1800,3600")
ap.add_argument("--dram-budget", type=float, default=0); ap.add_argument("--cxl-rate", type=float, default=46); ap.add_argument("--speed", type=float, default=1); ap.add_argument("--depth", type=int, default=4)
ap.add_argument("--out", default=os.path.join(REPO, "experimental_results", "2026-10-17-kv-reuse-oracle-study")); ap.add_argument("--tag", default="")
A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
BLOCK = (64 if A.model == "8b" else 160) * 2**20; NSLOT = {0: int(A.dram * 2**30 // BLOCK), 1: int(A.cxl * 2**30 // BLOCK)}
SHARE = A.split_share if A.split_share >= 0 else NSLOT[0] / (NSLOT[0] + NSLOT[1])
HORIZONS = [float(h) for h in A.horizons.split(",")] if A.horizons else []
CONSTRAINED = A.dram_budget > 0

# ---------------------------------------------------------------- trace
def load(trace):
    reqs = []
    for l in open(os.path.join(REPO, "workloads", f"mooncake_{trace}_trace.jsonl")):
        r = json.loads(l); reqs.append((r["timestamp"] / 1000.0 / A.speed, r["hash_ids"]))
    acc = []; seen = set(); nxt = {}; pos_of = []; dep_of = []
    for ri, (t, hs) in enumerate(reqs):
        d = 0
        for h in hs:
            if h in seen: d += 1
            else: break
        for pos, h in enumerate(hs):
            acc.append([t, h, ri, pos, d]); seen.add(h)
    last = {}
    next_use = [INF] * len(acc)
    for i in range(len(acc) - 1, -1, -1):
        h = acc[i][1]; next_use[i] = last.get(h, INF); last[h] = i
    T = [a[0] for a in acc]
    return reqs, acc, next_use, T

# ---------------------------------------------------------------- policies
class Cache:
    """slots per tier; residency map block -> tier; per-tier or global order (OrderedDict as LRU); write pipes."""
    def __init__(self, pol, fit=None):
        self.pol = pol; self.fit = fit or {}
        self.where = {}                                   # block -> tier
        self.lru = {0: collections.OrderedDict(), 1: collections.OrderedDict()}   # per-tier LRU (also used by global via tier -1)
        self.glru = collections.OrderedDict()             # global LRU (block -> tier)
        self.cls = [collections.OrderedDict() for _ in range(5)]   # pred_evict classes
        self.prob = collections.OrderedDict(); self.prot = collections.OrderedDict(); self.pshare = 0.5   # slru segments (block -> True)
        self.kcount = collections.defaultdict(int)        # past reuse count of a block (uses so far - 1)
        self.heap = []                                    # oracle: (-next_use, block)
        self.nu = {}                                      # oracle: block -> its current next use
        self.pipe = {0: 0.0, 1: 0.0}; self.ready = {}     # constrained: pipe free time, block -> store completion time
        self.tokens = float(A.depth) * BLOCK; self.tok_t = None
        self.st = dict(hits=[0, 0], miss=0, comp=0, reuse=0, acc=0, st_bytes=[0, 0], bypass=0, evict=0, premature=0, moves=0, pending=0, occ_samples=0, occ_useful=0)
    def n(self, t): return len([b for b, tt in self.where.items() if tt == t]) if False else self._n[t]
    def tier_of(self, h): return self.where.get(h)
    # -- helpers
    def _touch(self, h, i, nu_i):
        t = self.where[h]
        if self.pol.startswith("slru"):
            if h in self.prot: self.prot.move_to_end(h)
            else:
                self.prob.pop(h); self.prot[h] = True
                cap = int(self.pshare * (NSLOT[0] + NSLOT[1]))
                if self.pol.startswith("slru_tier") and t == 1 and (self._free_slots(0) > 0 or any(tt == 0 for tt in self.where.values())):
                    # physical promotion into DRAM; demote DRAM's LRU protected block (or a DRAM probation block) into this block's CXL slot
                    victim = None
                    if self._free_slots(0) == 0:
                        for b in self.prot:
                            if self.where[b] == 0: victim = b; break
                        if victim is None:
                            for b in self.prob:
                                if self.where[b] == 0: victim = b; break
                    if victim is not None:
                        self.where[victim] = 1; self.st["moves"] += BLOCK; self.st["st_bytes"][1] += BLOCK
                    else: self._n[0] += 1; self._n[1] -= 1
                    self.where[h] = 0; self.st["moves"] += BLOCK; self.st["st_bytes"][0] += BLOCK
                while len(self.prot) > cap:
                    d, _ = self.prot.popitem(last=False); self.prob[d] = True; self.prob.move_to_end(d)
            return
        if self.pol in ("global_lru", "pred_evict", "pred_both"):
            if self.pol == "global_lru": self.glru.move_to_end(h)
            else:
                k = self.kcount[h]; c = self.cls[kclass(k)]; c.pop(h, None); self.kcount[h] = k + 1; self.cls[kclass(k + 1)][h] = t
        elif self.pol.startswith("oracle"): self.nu[h] = nu_i; heapq.heappush(self.heap, (-nu_i, h))
        else: self.lru[t].move_to_end(h)
    def _free_slots(self, t): return NSLOT[t] - self._n[t]
    def _place(self, h, t, i, nu_i, now, count=True):
        self.where[h] = t; self._n[t] += 1
        if self.pol in ("global_lru",): self.glru[h] = t
        elif self.pol.startswith("slru"): self.prob[h] = True
        elif self.pol in ("pred_evict", "pred_both"): self.cls[kclass(self.kcount[h])][h] = t
        elif self.pol.startswith("oracle"): self.nu[h] = nu_i; heapq.heappush(self.heap, (-nu_i, h))
        else: self.lru[t][h] = True
        if count: self.st["st_bytes"][t] += BLOCK
        if CONSTRAINED:
            rate = (A.dram_budget if t == 0 else A.cxl_rate) * 1e9
            start = max(now, self.pipe[t]); self.pipe[t] = start + BLOCK / rate; self.ready[h] = self.pipe[t]
    def _remove(self, h, i_next):
        t = self.where.pop(h); self._n[t] -= 1
        self.glru.pop(h, None); self.lru[t].pop(h, None); self.cls[kclass(self.kcount[h])].pop(h, None); self.nu.pop(h, None); self.ready.pop(h, None); self.prob.pop(h, None); self.prot.pop(h, None)
        self.st["evict"] += 1
        if i_next < INF: self.st["premature"] += 1
        return t
    def _evict_tier_lru(self, t, nu):
        h, _ = self.lru[t].popitem(last=False); self.lru[t][h] = True; self._remove(h, nu[self.last_idx[h]])
    def _evict_global(self, nu):
        if self.pol == "global_lru":
            h = next(iter(self.glru))
        elif self.pol.startswith("slru"):
            h = next(iter(self.prob)) if self.prob else next(iter(self.prot))
        else:
            for c in self.cls:
                if c: h = next(iter(c)); break
        return self._remove(h, nu[self.last_idx[h]])
    def _budget_ok(self, now):
        if not CONSTRAINED: return True
        if self.tok_t is not None: self.tokens = min(float(A.depth) * BLOCK, self.tokens + (now - self.tok_t) * A.dram_budget * 1e9)
        self.tok_t = now
        if self.tokens >= BLOCK: self.tokens -= BLOCK; return True
        return False

def kclass(k): return 0 if k == 0 else 1 if k == 1 else 2 if k == 2 else 3 if k <= 4 else 4

def run(pol, trace_data, fit, horizon=None):
    reqs, acc, next_use, T = trace_data; N = len(acc); half = len(reqs) // 2
    base_pol = "slru_tier" if pol.startswith("slru_tier") else "slru" if pol.startswith("slru") else pol
    c = Cache(base_pol, fit); c._n = {0: 0, 1: 0}; c.last_idx = {}
    if base_pol.startswith("slru"): c.pshare = float(pol[len(base_pol):] or 0.5)
    pol = base_pol
    nu = next_use
    if horizon is not None:                                # oracle with limited horizon: next use beyond H seconds = never
        nu = [n if (n < INF and T[n] - T[i] <= horizon) else INF for i, n in enumerate(next_use)]
    seen = set(); st = c.st; test = False; loads = 0; req_misses = collections.defaultdict(int); req_loads = collections.defaultdict(int)
    for i, (t, h, ri, pos, dep) in enumerate(acc):
        if not test and ri >= half: test = True
        c.last_idx[h] = i
        reuse = h in seen; seen.add(h)
        if test:
            st["acc"] += 1; st["reuse"] += reuse
            if i % 1000 == 0 and c.where:
                st["occ_samples"] += 1; st["occ_useful"] += sum(1 for b in c.where if nu[c.last_idx[b]] < INF) / len(c.where)
        tier = c.tier_of(h)
        if tier is not None and (not CONSTRAINED or c.ready.get(h, 0) <= t):
            if test: st["hits"][tier] += 1; loads += 1; req_loads[ri] += 1
            c._touch(h, i, nu[i])
            if pol == "reactive_mig" and tier == 1:                       # move to DRAM, drop DRAM's LRU block
                if c._free_slots(0) == 0: c._evict_tier_lru(0, nu)
                c._remove(h, INF); st["evict"] -= 1; c._place(h, 0, i, nu[i], t, count=False); st["moves"] += BLOCK; st["st_bytes"][0] += BLOCK
            if pol == "oracle_mig" and tier == 1:                         # keep the soonest next uses in DRAM: swap with DRAM's farthest
                far = max(((nu[c.last_idx[b]], b) for b, tt in c.where.items() if tt == 0), default=None) if c._free_slots(0) == 0 else None
                if c._free_slots(0) > 0 or (far and far[0] > nu[i]):
                    if far and c._free_slots(0) == 0:
                        c._remove(far[1], INF); st["evict"] -= 1; c._place(far[1], 1, i, far[0], t, count=False); st["moves"] += BLOCK; st["st_bytes"][1] += BLOCK
                    c._remove(h, INF); st["evict"] -= 1; c._place(h, 0, i, nu[i], t, count=False); st["moves"] += BLOCK; st["st_bytes"][0] += BLOCK
            continue
        # miss
        if tier is not None:                                               # resident but its store is still pending (constrained)
            if test: st["miss"] += 1; st["pending"] += 1; req_misses[ri] += 1
            c._touch(h, i, nu[i]); continue
        if test:
            st["miss"] += 1; st["comp"] += (not reuse); req_misses[ri] += 1
        # admission
        if pol.startswith("oracle"):
            if nu[i] == INF: st["bypass"] += test; continue
            if c._n[0] + c._n[1] >= NSLOT[0] + NSLOT[1]:
                while c.heap:
                    negn, b = c.heap[0]
                    if b in c.where and c.nu[b] == -negn: break
                    heapq.heappop(c.heap)
                if -c.heap[0][0] <= nu[i]: st["bypass"] += test; continue          # the new block's next use is farther than every resident's
                heapq.heappop(c.heap); c._remove(b, -negn)
            tgt = 0 if c._free_slots(0) > 0 else 1
            if CONSTRAINED and tgt == 0 and not c._budget_ok(t): tgt = 1
            c._place(h, tgt, i, nu[i], t); continue
        if pol in ("pred_admit", "pred_both"):
            p = fit["admit"].get((min(dep, 32) if dep < 32 else 32, min(pos, 64)), fit["base"])
            if p < A.theta: st["bypass"] += test; continue
        if pol in ("global_lru", "pred_evict", "pred_both") or pol.startswith("slru"):
            if c._n[0] + c._n[1] >= NSLOT[0] + NSLOT[1]: tgt = c._evict_global(nu)
            else: tgt = (0 if c._free_slots(0) > 0 else 1) if not pol.startswith("slru") else (1 if c._free_slots(1) > 0 else 0)
            if CONSTRAINED and tgt == 0 and not c._budget_ok(t):
                tgt = 1
                if c._free_slots(1) == 0: c._evict_tier_lru(1, nu) if False else None
            c._place(h, tgt, i, nu[i], t); continue
        if pol == "cxlfirst": tgt = 1
        elif pol in ("split", "pred_admit"): tgt = 0 if ((h * 0xD6E8FEB86659FD93) >> 40) % 1000 < SHARE * 1000 else 1
        elif pol == "reactive_mig": tgt = 1
        if CONSTRAINED and tgt == 0 and not c._budget_ok(t): tgt = 1
        if c._free_slots(tgt) == 0: c._evict_tier_lru(tgt, nu)
        c._place(h, tgt, i, nu[i], t)
    # per-request prefill estimate on the test segment
    test_reqs = range(half, len(reqs))
    est = [req_misses[r] * TOK / 7300.0 + req_loads[r] * BLOCK / 9.5e9 for r in test_reqs]
    st["prefill_est_s_mean"] = sum(est) / len(est); st["loads"] = loads
    return st

def fit_predictor(trace_data):
    """fitted on the first half only: P(reused within the first half | continuation depth, position) and the base rate."""
    reqs, acc, next_use, T = trace_data; half = len(reqs) // 2
    tab = collections.defaultdict(lambda: [0, 0]); seen = set(); base = [0, 0]
    for i, (t, h, ri, pos, dep) in enumerate(acc):
        if ri >= half: break
        if h in seen: continue
        seen.add(h); n = next_use[i]; reused = n < INF and acc[n][2] < half
        key = (min(dep, 32) if dep < 32 else 32, min(pos, 64)); tab[key][0] += 1; tab[key][1] += reused; base[0] += 1; base[1] += reused
    # smooth sparse cells toward the depth-only estimate
    dep_tab = collections.defaultdict(lambda: [0, 0])
    for (d, p), v in tab.items(): dep_tab[d][0] += v[0]; dep_tab[d][1] += v[1]
    admit = {}
    for (d, p), v in tab.items():
        prior = dep_tab[d][1] / dep_tab[d][0]; admit[(d, p)] = (v[1] + 5 * prior) / (v[0] + 5)
    return dict(admit=admit, base=base[1] / base[0])

# ---------------------------------------------------------------- main
rows = []
for trace in A.traces.split(","):
    data = load(trace); fit = fit_predictor(data)
    for pol in A.policies.split(","):
        variants = [(pol, None)] if pol != "oracle_h" else [(f"oracle_h{int(H)}", H) for H in HORIZONS]
        if pol in ("slru", "slru_tier"): variants = [(f"{pol}{sh}", None) for sh in A.slru_shares.split(",")]
        for name, H in variants:
            st = run("oracle_min" if H is not None else name, data, fit, horizon=H)
            r = dict(trace=trace, model=A.model, policy=name, speed=A.speed, dram_budget=A.dram_budget, acc=st["acc"], reuse=st["reuse"], hits=st["hits"][0] + st["hits"][1], hits_dram=st["hits"][0], hits_cxl=st["hits"][1],
                     reuse_hit_share=(st["hits"][0] + st["hits"][1]) / max(1, st["reuse"]), overall_hit_rate=(st["hits"][0] + st["hits"][1]) / max(1, st["acc"]), misses=st["miss"], compulsory=st["comp"], pending=st["pending"],
                     recomputed_tokens=st["miss"] * TOK, dram_GB=st["st_bytes"][0] / 1e9, cxl_GB=st["st_bytes"][1] / 1e9, bypassed=st["bypass"], evictions=st["evict"], premature=st["premature"],
                     premature_share=st["premature"] / max(1, st["evict"]), moves_GB=st["moves"] / 1e9, useful_occupancy=st["occ_useful"] / max(1, st["occ_samples"]), prefill_est_s=st["prefill_est_s_mean"], theta=A.theta, base_rate=fit["base"])
            rows.append(r)
            print(f"{trace:12s} {name:14s} reuse-hit {r['reuse_hit_share']:.3f} overall {r['overall_hit_rate']:.3f} recompute {r['recomputed_tokens'] / 1e6:6.1f} Mtok  writes DRAM {r['dram_GB']:7.0f} CXL {r['cxl_GB']:7.0f} GB bypass {r['bypassed']:6d} premature {r['premature_share']:.2f} useful-occ {r['useful_occupancy']:.2f} moves {r['moves_GB']:6.0f} GB pending {r['pending']} prefill {r['prefill_est_s']:.3f} s", flush=True)
tag = A.tag or (f"{A.model}-{'budget%g-speed%g' % (A.dram_budget, A.speed) if CONSTRAINED else 'capacity'}")
with open(os.path.join(A.out, f"oracle-{tag}.csv"), "w") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("wrote", os.path.join(A.out, f"oracle-{tag}.csv"))
