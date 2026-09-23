#!/usr/bin/env python3
"""Trace-driven simulation of the simplest KV promotion rule for cxlpath: every new block is written to CXL;
a block is marked for promotion at its FIRST hit; the copy to DRAM lands after a delay d (0 = immediately,
larger = the copy waited for a calm DRAM); the CXL original always stays, so evicting a DRAM copy costs
nothing. Three tiers, lookup order DRAM copy -> CXL -> NVMe; the pool below (CXL 512 GiB, NVMe 3.2 TiB,
both LRU, every CXL eviction drained to NVMe) is the model of 2026-09-18; prefix matching as there: the
first block found nowhere ends the match. Block = 512 tokens = 64 MiB for Llama-3.1-8B.
Variants: promote at the k-th hit (k=1 first hit, k=2 second hit); eviction lru | lfu (fewest hits since promotion,
ties oldest) | oracle (Belady: evict the block whose next occurrence is farthest, and promote only blocks that occur
again — an upper bound, uses the future).
usage: kv_first_hit_promotion.py <trace.jsonl> <dram_GiB|inf> <promote_delay_s> [block_MiB=64] [k=1] [lru|lfu|oracle]"""
import json, sys, statistics as st, heapq
from collections import OrderedDict
path, cap_arg, delay_s = sys.argv[1], sys.argv[2], float(sys.argv[3]); BLK = int(sys.argv[4]) if len(sys.argv) > 4 else 64
K = int(sys.argv[5]) if len(sys.argv) > 5 else 1; EV = sys.argv[6] if len(sys.argv) > 6 else "lru"
CXL_BLOCKS, NVME_BLOCKS = (512 << 10) // BLK, (3200 << 10) // BLK
dram_cap = None if cap_arg == "inf" else int(float(cap_arg) * 1024 / BLK)
reqs = [(r["timestamp"] / 1000.0, r["hash_ids"]) for r in map(json.loads, open(path))]
span = reqs[-1][0] - reqs[0][0]
occ = {}                                                            # block -> occurrence positions (for the oracle)
pos = 0
for _, hs in reqs:
    for h in hs: occ.setdefault(h, []).append(pos); pos += 1
nxt_ptr = {h: 0 for h in occ}
def next_occ(h, cur):                                               # first occurrence strictly after cur
    lst = occ[h]; i = nxt_ptr[h]
    while i < len(lst) and lst[i] <= cur: i += 1
    nxt_ptr[h] = i; return lst[i] if i < len(lst) else 10**12
heap = []                                                           # oracle: (-next_occ, block)
hitcount = {}                                                       # block -> hits so far (for k and lfu)
cur = 0
cxl, nvme, dram = OrderedDict(), OrderedDict(), OrderedDict()      # block -> True (LRU order); dram: block -> last-hit time
pending = []                                                        # (land_time, block) promotions waiting for the calm copy
first_hit_t, last_hit_t = {}, {}                                    # per block
promoted_at, hits_after_promo, copies = {}, {}, 0                   # per block (current or last promotion)
wasted_evicted, gap_first_to_next = 0, []
S = dict(blocks=0, hit_dram=0, hit_cxl=0, hit_nvme=0, miss=0, promos=0, repromos=0, evicted_dram=0)
def land_pending(now):
    global copies
    while pending and pending[0][0] <= now:
        _, h = pending.pop(0)
        if h in dram: continue
        if h not in cxl and h not in nvme: continue                 # gone from the pool before the copy landed
        dram[h] = now; copies += 1; S["promos"] += 1
        if h in promoted_at: S["repromos"] += 1
        promoted_at[h] = now; hits_after_promo[h] = 0
        if EV == "oracle": heapq.heappush(heap, (-next_occ(h, cur), h))
        while dram_cap is not None and len(dram) > dram_cap:
            if EV == "lru": old, _ = dram.popitem(last=False)
            elif EV == "lfu": old = min(dram, key=lambda b: (hits_after_promo[b], dram[b])); del dram[old]
            else:
                while True:
                    negn, old = heapq.heappop(heap)
                    if old in dram and -negn == next_occ(old, cur): break
                    if old in dram: heapq.heappush(heap, (-next_occ(old, cur), old))
                del dram[old]
            S["evicted_dram"] += 1
def put_cxl(h):
    cxl[h] = True
    while len(cxl) > CXL_BLOCKS:
        old, _ = cxl.popitem(last=False)
        nvme[old] = True
        if len(nvme) > NVME_BLOCKS: nvme.popitem(last=False)
for t, hs in reqs:
    land_pending(t); matching = True
    for h in hs:
        S["blocks"] += 1; cur += 1
        present = h in dram or h in cxl or h in nvme
        if matching and present:
            hitcount[h] = hitcount.get(h, 0) + 1
            if h in dram:
                S["hit_dram"] += 1; dram[h] = t; dram.move_to_end(h); hits_after_promo[h] += 1
                if EV == "oracle": heapq.heappush(heap, (-next_occ(h, cur), h))
            elif h in cxl: S["hit_cxl"] += 1; cxl.move_to_end(h)
            else: S["hit_nvme"] += 1; nvme.move_to_end(h); put_cxl(h)   # reloaded into CXL
            if h in first_hit_t:
                if h in last_hit_t and last_hit_t[h] == first_hit_t[h]: gap_first_to_next.append(t - first_hit_t[h])
            else: first_hit_t[h] = t
            if hitcount[h] == K and h not in dram and (EV != "oracle" or next_occ(h, cur) < 10**12):
                pending.append((t + delay_s, h)); pending.sort()
            last_hit_t[h] = t
        else:
            matching = False; S["miss"] += 1
            if h in cxl: cxl.move_to_end(h)
            elif h not in dram and h not in nvme: put_cxl(h)
land_pending(1e18)
hits = S["hit_dram"] + S["hit_cxl"] + S["hit_nvme"]
never_again = sum(1 for h, n in hits_after_promo.items() if n == 0)
per = [n for n in hits_after_promo.values()]
useful = sum(1 for n in per if n > 0)
print(f"trace={path.split('/')[-1].replace('mooncake_','').replace('_trace.jsonl','')} dram={cap_arg}GiB delay={delay_s:.0f}s k={K} evict={EV} | requests {len(reqs)} blocks {S['blocks']} written {S['miss']} hits {hits} "
      f"(DRAM {100*S['hit_dram']/hits:.1f}% CXL {100*S['hit_cxl']/hits:.1f}% NVMe {100*S['hit_nvme']/hits:.1f}%) | "
      f"promotions {S['promos']} (re-promotions {S['repromos']}, DRAM evictions {S['evicted_dram']}) = {S['promos']*BLK/1024:.1f} GiB copied = {S['promos']*BLK/1024/span:.3f} GiB/s; "
      f"DRAM hits {S['hit_dram']*BLK/1024:.1f} GiB -> {S['hit_dram']/max(1,S['promos']):.2f} DRAM hits per copy | promoted-never-hit-again {100*never_again/max(1,len(per)):.0f}% "
      f"| hits after promotion per promoted block: mean {st.mean(per) if per else 0:.2f} median {st.median(per) if per else 0:.0f} p90 {sorted(per)[int(0.9*len(per))] if per else 0} max {max(per) if per else 0} | "
      f"gap first->second hit s: p50 {st.median(gap_first_to_next) if gap_first_to_next else 0:.0f} p90 {sorted(gap_first_to_next)[int(0.9*len(gap_first_to_next))] if gap_first_to_next else 0:.0f} p99 {sorted(gap_first_to_next)[int(0.99*len(gap_first_to_next))] if gap_first_to_next else 0:.0f} (n={len(gap_first_to_next)})")
