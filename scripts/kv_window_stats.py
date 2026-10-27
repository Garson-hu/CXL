#!/usr/bin/env python3
"""Historical-window statistics of KV block reuse (C1 of the 2026-10-27 exploratory study): does the number of accesses a block had in
the PAST W seconds predict whether it is accessed again in the NEXT H seconds? Offline analysis of the trace alone (no cache): for every
block access in the scored half (second half of the requests), the count of the block's accesses in (t - W, t) for W in the grid, the
gap since the previous access, and the future: the next access gap (from the trace, used for evaluation only).
Prints, per W: the share of accesses in each past-count class (0 / 1 / 2 / >= 3), P(next access within H | class) for H = 60 / 300 /
900 s, the share of all future reuses (within 300 s) that fall on blocks of each class, and the same split by the recency gap; also
the 'capture' of a keep-rule: keeping only blocks with count >= c inside W captures what fraction of the reuses within 300 s.
usage: kv_window_stats.py <trace.jsonl> [--mooncake] [--out csv] [--windows 10,30,50,100,200,300] [--score-range 0.5,1.0]"""
import argparse, bisect, collections, csv, json, sys
ap = argparse.ArgumentParser(); ap.add_argument("trace"); ap.add_argument("--mooncake", action="store_true"); ap.add_argument("--out", default="")
ap.add_argument("--windows", default="10,30,50,100,200,300"); ap.add_argument("--score-range", default="0.5,1.0"); ap.add_argument("--horizons", default="60,300,900")
A = ap.parse_args(); WS = [float(x) for x in A.windows.split(",")]; HS = [float(x) for x in A.horizons.split(",")]
R = []
for l in open(A.trace):
    r = json.loads(l)
    if A.mooncake: R.append((r["timestamp"] / 1000.0, [str(h) for h in r["hash_ids"]]))
    else: R.append((r["t_lookup"], list(r["hashes"])))
R.sort(key=lambda x: x[0]); NR = len(R); s0, s1 = (float(x) for x in A.score_range.split(",")); LO, HI = int(s0 * NR), int(s1 * NR)
times = collections.defaultdict(list)                          # block -> sorted access times (whole trace)
acc = []                                                        # (t, h, scored)
for ri, (t, hs) in enumerate(R):
    for h in hs: times[h].append(t); acc.append((t, h, LO <= ri < HI))
print(f"{NR} requests, {len(acc)} block accesses, {len(times)} distinct blocks; scored accesses {sum(1 for a in acc if a[2])}")
# per scored access: past counts per W, gap, next gap
cls = lambda c: 0 if c == 0 else 1 if c == 1 else 2 if c == 2 else 3
stats = {W: collections.defaultdict(lambda: [0, [0] * len(HS)]) for W in WS}     # W -> class -> [n, [n with next <= H]]
gapcls = collections.defaultdict(lambda: [0, [0] * len(HS)])                      # recency gap bucket -> same
reuse300 = {W: collections.Counter() for W in WS}; reuse300_tot = 0
GB = [(0, 10), (10, 30), (30, 60), (60, 120), (120, 300), (300, 900), (900, 1e18)]
for t, h, sc in acc:
    if not sc: continue
    ts = times[h]; i = bisect.bisect_left(ts, t)                 # index of this access (first with time >= t; duplicates in the same request share t)
    nxt = ts[i + 1] - t if i + 1 < len(ts) else float("inf")
    prev_gap = t - ts[i - 1] if i > 0 else None
    within = [nxt <= H for H in HS]
    for W in WS:
        c = i - bisect.bisect_left(ts, t - W)                   # accesses in [t - W, t) (excludes this one)
        k = cls(c); st = stats[W][k]; st[0] += 1
        for j, w in enumerate(within): st[1][j] += w
        if nxt <= 300: reuse300[W][k] += 1
    if nxt <= 300: reuse300_tot += 1
    gk = "first" if prev_gap is None else next(f"{a}-{b}s" if b < 1e17 else f">{a}s" for a, b in GB if a <= prev_gap < b)
    st = gapcls[gk]; st[0] += 1
    for j, w in enumerate(within): st[1][j] += w
rows = []
print("\n| past window W | past-count class | share of accesses | P(next access <= 60 s) | <= 300 s | <= 900 s | share of the reuses within 300 s on this class |")
print("|---|---|---|---|---|---|---|")
tot = sum(v[0] for v in stats[WS[0]].values())
for W in WS:
    for k in range(4):
        n, w = stats[W][k]
        if n == 0: continue
        lab = {0: "0 (unseen in W)", 1: "1", 2: "2", 3: ">= 3"}[k]
        print(f"| {W:g} s | {lab} | {100 * n / tot:.1f}% | {100 * w[0] / n:.1f}% | {100 * w[1] / n:.1f}% | {100 * w[2] / n:.1f}% | {100 * reuse300[W][k] / max(1, reuse300_tot):.1f}% |")
        rows.append(dict(window_s=W, past_count_class=lab, n=n, share=n / tot, **{f"p_next_le_{int(H)}s": w[j] / n for j, H in enumerate(HS)}, share_of_reuse300=reuse300[W][k] / max(1, reuse300_tot)))
print("\n| recency gap since the previous access | share of accesses | P(next <= 60 s) | <= 300 s | <= 900 s |"); print("|---|---|---|---|---|")
order = ["first"] + [f"{a}-{b}s" if b < 1e17 else f">{a}s" for a, b in GB]
for gk in order:
    if gk in gapcls:
        n, w = gapcls[gk]; print(f"| {gk} | {100 * n / tot:.1f}% | {100 * w[0] / n:.1f}% | {100 * w[1] / n:.1f}% | {100 * w[2] / n:.1f}% |")
        rows.append(dict(window_s=None, past_count_class=f"gap {gk}", n=n, share=n / tot, **{f"p_next_le_{int(H)}s": w[j] / n for j, H in enumerate(HS)}, share_of_reuse300=None))
if A.out:
    with open(A.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
