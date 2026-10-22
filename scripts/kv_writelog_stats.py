#!/usr/bin/env python3
"""Task A of the 2026-10-21 hardware validation: statistics of the Phase 3 write streams from the per-store write logs of
kv_joint_sim.py --write-log (<dir>/<trace>-<model>-<speed>x-<policy>.txt).
For every log: the scored window in wall seconds (from the header; its end = the last offer of a scored-half store), the
consistency checks (bytes in the window vs the Phase 3 CSV's written blocks; whole-trace vs scored-window totals = the
earlier "TB written" correction), and three views of the stream binned at 10 ms / 100 ms / 1 s:
  offered  = bytes at their offer instants (the demand as the trace + the 7,300 tok/s prefill spacing place it in time);
  paced    = each store spread over its DMA-link time at 9.5 GB/s (what the hardware replayer issues for a store);
  served   = the simulator's completion model (DRAM at 150 GB/s from the offer; CXL from the C records, FIFO at 46 GB/s).
Per view and tier: mean, p50, p95, p99, max of the per-bin rate (GB/s), share of bins above the safe DRAM budget (8 GB/s)
and above the CXL path (46 GB/s), the longest run of 10 ms bins above each. Resolution caveat: the trace stamps requests
in ms; within a request the block spacing is the prefill model, so 10 ms figures depend on that model, not on measured data.
usage: kv_writelog_stats.py <writelog dir> [sim csv dir] -> prints markdown tables, writes <dir>/windows.json"""
import csv, glob, json, os, sys
D = sys.argv[1]; SIM = sys.argv[2] if len(sys.argv) > 2 else None
BLOCK = {"8b": 67100000, "70b": 167800000}
def q(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else 0.0
def runs(flags):
    best = cur = 0
    for f in flags: cur = cur + 1 if f else 0; best = max(best, cur)
    return best
def bins(events, lo, hi, dt):
    """events: (start, end, bytes) spread uniformly over [start, end) -> rate per bin of length dt over [lo, hi)"""
    n = int((hi - lo) / dt) + 1; v = [0.0] * n
    for s, e, b in events:
        if e <= s: e = s + 1e-9
        a, z = max(s, lo), min(e, hi)
        if z <= a: continue
        i0, i1 = int((a - lo) / dt), int((z - lo) / dt)
        for i in range(i0, min(i1, n - 1) + 1):
            x0, x1 = max(a, lo + i * dt), min(z, lo + (i + 1) * dt)
            if x1 > x0: v[i] += b * (x1 - x0) / (e - s)
    return [x / dt / 1e9 for x in v]
windows = {}; print("| log | window (wall s) | stores D / C | GB D / C (window) | CSV blocks D / C | whole-trace GB D / C | view | tier | 10 ms: mean / p50 / p95 / p99 / max | 100 ms: mean / p95 / p99 / max | 1 s: mean / p95 / p99 / max | 10 ms bins > 8 GB/s (DRAM) or > 46 (CXL) | longest run (10 ms bins) |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for f in sorted(glob.glob(f"{D}/*.txt")):
    name = os.path.basename(f)[:-4]; parts = name.split("-"); pol = parts[-1]; cfg = "-".join(parts[:-1]); model = parts[1]
    hdr = open(f).readline().split(); H = dict(zip(hdr[1::2], hdr[2::2])) if False else {}
    for i, t in enumerate(hdr):
        if t in ("scored_wall_start", "scored_wall_end", "speed", "block_bytes"): H[t] = float(hdr[i + 1])
    S = []; C = {}; whole = [0, 0]
    for l in open(f):
        if l[0] == "S":
            x = l.split(); ws = float(x[1]); tier = 0 if x[2] == "D" else 1; b = float(x[3]); sc = x[4] == "1"; h = x[5]
            whole[tier] += b; S.append((ws, tier, b, sc, h))
        elif l[0] == "C": x = l.split(); C[x[1]] = float(x[2])
    lo = H["scored_wall_start"]; hi = max(ws for ws, _, _, sc, _ in S if sc) + 0.001
    win = [(ws, t, b, h) for ws, t, b, sc, h in S if lo <= ws < hi]
    nD = sum(1 for _, t, _, _ in win if t == 0); nC = len(win) - nD; gD = sum(b for _, t, b, _ in win if t == 0) / 1e9; gC = sum(b for _, t, b, _ in win if t == 1) / 1e9
    windows[name] = dict(t0=lo, t1=hi, stores_dram=nD, stores_cxl=nC, GB_dram=round(gD, 2), GB_cxl=round(gC, 2))
    csvD = csvC = "–"
    if SIM:
        for r in csv.DictReader(open(f"{SIM}/sim-{cfg}-adam-joint.csv")):
            if r["policy"] == pol: csvD, csvC = r["written_dram_blocks"], r["written_cxl_blocks"]
    link = 9.5e9
    views = {"offered": {0: [(ws, ws, b) for ws, t, b, _ in win if t == 0], 1: [(ws, ws, b) for ws, t, b, _ in win if t == 1]},
             "paced": {0: [(ws, ws + b / link, b) for ws, t, b, _ in win if t == 0], 1: [(ws, ws + b / link, b) for ws, t, b, _ in win if t == 1]},
             "served": {0: [(ws, ws + b / 150e9, b) for ws, t, b, _ in win if t == 0], 1: [(C[h] - b / 46e9, C[h], b) for ws, t, b, h in win if t == 1 and h in C]}}
    first = True
    for view, tiers in views.items():
        for tier in (0, 1):
            ev = tiers[tier]
            if not ev: continue
            r10 = bins(ev, lo, hi, 0.01); r100 = bins(ev, lo, hi, 0.1); r1 = bins(ev, lo, hi, 1.0); thr = 8.0 if tier == 0 else 46.0
            over = [x > thr for x in r10]
            print(f"| {name if first else ''} | {f'{lo:.1f}–{hi:.1f} ({hi - lo:.0f} s)' if first else ''} | {f'{nD} / {nC}' if first else ''} | {f'{gD:.1f} / {gC:.1f}' if first else ''} | {f'{csvD} / {csvC}' if first else ''} | {f'{whole[0] / 1e9:.0f} / {whole[1] / 1e9:.0f}' if first else ''} | {view} | {'DRAM' if tier == 0 else 'CXL'} | "
                  f"{sum(r10) / len(r10):.2f} / {q(r10, .5):.2f} / {q(r10, .95):.2f} / {q(r10, .99):.2f} / {max(r10):.1f} | {sum(r100) / len(r100):.2f} / {q(r100, .95):.2f} / {q(r100, .99):.2f} / {max(r100):.1f} | "
                  f"{sum(r1) / len(r1):.2f} / {q(r1, .95):.2f} / {q(r1, .99):.2f} / {max(r1):.1f} | {100 * sum(over) / len(over):.1f}% | {runs(over)} |")
            first = False
json.dump(windows, open(f"{D}/windows.json", "w"), indent=1)
