#!/usr/bin/env python3
"""Summarize the budget-gated admission runs (2026-10-12; kvemu2 via run_exp2b.py) in <dir> -> <dir>/summary.csv, summary.txt.
Per run:
  traffic   offered and achieved rates (stores to DRAM / CXL, loads), DRAM write mean, 20 ms peak and 1 s peak; DRAM
            moves (borrowmig); backlog and lateness, max and per minute; achieved / offered bytes.
  budget    mean budget, utilization = DRAM writes / budget over all time and over the 20 ms bins with store activity.
  cache     hit share of reuse accesses (a block still being written is a miss), DRAM / CXL hits, pending misses,
            occupancy, capacity utilization.
  neighbour quiet = its BEFORE window (no KV traffic); during = the traffic window (with --phases: only Adam steps that lie
            entirely inside an "on" phase). Adam: step time; reader: seconds per GiB in 100 ms samples (64 MiB progress).
            slow_med = median during / quiet median - 1; slow_p99 = p99 during / quiet p99 - 1 (THE SLO, <= 7%);
            slow_p99m = p99 during / quiet median - 1 (includes the workload's own tail); reader also mean bandwidth loss.
            Per minute: p99 during that minute / quiet p99 - 1.
usage: analyze_bga.py <dir>"""
import glob, gzip, os, re, statistics as st, sys

D = sys.argv[1]
def rd(p): return open(p).read() if os.path.exists(p) else gzip.open(p + ".gz", "rt").read() if os.path.exists(p + ".gz") else ""
def q(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else float("nan")
rows = []
for meta in sorted(glob.glob(os.path.join(D, "*-meta.txt"))):
    tag = os.path.basename(meta)[:-9]; M, cfg, phases = {}, {}, []
    for l in open(meta):
        f = l.split()
        if f[1] == "phase": phases.append((int(f[2]), f[3])); continue
        M[f[1]] = int(f[2])
        if f[1] == "config": cfg = dict(x.split("=", 1) for x in f[3:] if "=" in x)
    if "done" not in M: continue
    emu = rd(f"{D}/{tag}-emu.txt"); start = int(re.search(r"^START (\d+)", emu, re.M)[1])
    W = [[float(x) for x in l.split()[1:]] for l in emu.splitlines() if l.startswith("W ")]
    last = max(i for i, w in enumerate(W) if w[1] or w[2] or w[3] or w[4]); W = W[: last + 1]; end = int(W[-1][0])
    S1 = dict(re.findall(r"(\w+) ([\d.]+)", re.search(r"^S requests.*", emu, re.M)[0])); S2 = dict(re.findall(r"(\w+) ([\d.]+)", re.search(r"^S wall_s.*", emu, re.M)[0]))
    hd = re.search(r"hits \d+ \(dram (\d+) cxl (\d+)\)", emu)
    col = lambda k: [w[k] for w in W]
    off, sd, sc, ld, bl, lt = col(1), col(2), col(3), col(4), col(5), col(6)
    bud = col(10) if len(W[0]) > 10 else [0.0] * len(W)
    sec = lambda v: [sum(v[i:i + 50]) / 50 for i in range(0, len(v) - 49, 50)] or [max(v)]
    act = [i for i in range(len(W)) if sd[i] + sc[i] > 0]
    moved = float(re.search(r"moved_GB ([\d.]+)", emu)[1]) if "moved_GB" in emu else 0.0
    r = dict(tag=tag, neighbor=cfg.get("neighbor"), policy=cfg.get("policy"), share=cfg.get("KV2_SPLIT_SHARE", ""), budget_set=cfg.get("KV2_BUDGET_GBPS", cfg.get("phase_budgets", "")),
             window=f"{cfg.get('t0')}-{cfg.get('t1')}@{cfg.get('speed')}", block_KiB=cfg.get("block_KiB"), phases=cfg.get("phases"),
             span_s=len(W) * 0.02, offered=st.mean(off), store_dram=st.mean(sd), store_cxl=st.mean(sc), load=st.mean(ld), moved_GB=moved,
             achieved_frac=(sum(sd) + sum(sc) + sum(ld)) / max(1e-9, sum(off)),
             dram_peak20=max(sd), dram_peak1s=max(sec(sd)), backlog_max=max(bl), late_max_ms=max(lt),
             budget_mean=st.mean(bud), budget_util=st.mean(sd) / st.mean(bud) if st.mean(bud) > 0 else float("nan"),
             budget_util_active=(st.mean(sd[i] for i in act) / st.mean(bud[i] for i in act)) if act and st.mean(bud[i] for i in act) > 0 else float("nan"),
             hit_share=float(S1["hit_share_of_reuse"]), hits_dram=int(hd[1]) if hd else 0, hits_cxl=int(hd[2]) if hd else 0, pending=int(S1["pending_misses"]),
             util=float(S2["utilization"]), occ_dram=float(S2["occupancy_mean_dram_GiB"]), gave_up=int(S2["gave_up"]))
    # per minute: backlog max, achieved store rate, offered
    PM = []
    for m in range(0, len(W), 3000):
        seg = W[m:m + 3000]; PM.append((max(w[5] for w in seg), st.mean(w[2] + w[3] for w in seg), st.mean(w[1] for w in seg)))
    r["per_min_backlog"] = " ".join(f"{x[0]:.0f}" for x in PM); r["per_min_store"] = " ".join(f"{x[1]:.1f}" for x in PM); r["per_min_offered"] = " ".join(f"{x[2]:.1f}" for x in PM)
    # neighbour
    for k in ("q_med", "q_p99", "d_med", "d_p99", "slow_med", "slow_p99", "slow_p99m", "bw_loss", "n_quiet", "n_during"): r[k] = float("nan")
    r["per_min_p99"] = ""
    txt = rd(f"{D}/{tag}-neighbor.txt")
    if txt and "before_start" in M:
        b0, b1 = M["before_start"], M["before_end"]
        if "[STEP]" in txt: s = [(int(t) - int(float(v) * 1e9), int(t), float(v)) for v, t in re.findall(r"\[STEP\] \d+ ([\d.]+) (\d+)", txt)]   # (begin, end, seconds)
        else: s = [(int(t) - 100000000, int(t), 1.0 / float(v)) for t, v in re.findall(r"^T (\d+) ([\d.]+)$", txt, re.M) if float(v) > 0]   # seconds per GiB
        quiet = [v for a, b, v in s if b0 <= a and b < b1]
        if phases:   # on-intervals: [start, first off), [on, next off), ...
            edges = [start] + [t for t, _ in phases] + [end]; states = ["on"] + [p for _, p in phases]
            ons = [(edges[i], edges[i + 1]) for i in range(len(states)) if states[i] == "on"]
            dur = [(a, b, v) for a, b, v in s if any(lo <= a and b <= hi for lo, hi in ons)]
        else: dur = [(a, b, v) for a, b, v in s if start <= a and b <= end]
        dv = [v for _, _, v in dur]
        if quiet and dv:
            r.update(q_med=st.median(quiet), q_p99=q(quiet, .99), d_med=st.median(dv), d_p99=q(dv, .99), n_quiet=len(quiet), n_during=len(dv))
            r["slow_med"] = 100 * (r["d_med"] / r["q_med"] - 1); r["slow_p99"] = 100 * (r["d_p99"] / r["q_p99"] - 1); r["slow_p99m"] = 100 * (r["d_p99"] / r["q_med"] - 1)
            if "[STEP]" not in txt: r["bw_loss"] = 100 * (1 - st.mean(1 / v for v in dv) / st.mean(1 / v for v in quiet))
            pm = []
            for m0 in range(start, end, 60_000_000_000):
                v = [x for a, b, x in dur if m0 <= a < m0 + 60_000_000_000]
                pm.append(f"{100 * (q(v, .99) / r['q_p99'] - 1):+.1f}" if len(v) >= 20 else "-")
            r["per_min_p99"] = " ".join(pm)
    rows.append(r)
if not rows: sys.exit("no finished runs")
keys = list(rows[0].keys())
with open(f"{D}/summary.csv", "w") as f:
    f.write(",".join(keys) + "\n")
    for r in rows: f.write(",".join(f"{r[k]:.4f}" if isinstance(r[k], float) else str(r[k]) for k in keys) + "\n")
out = open(f"{D}/summary.txt", "w")
def say(s=""): print(s); out.write(s + "\n")
say(f"{'tag':34s} {'offer':>5s} {'DRAM':>5s} {'pk20':>5s} {'pk1s':>5s} {'CXL':>5s} {'mvGB':>4s} {'ach':>5s} {'bud':>5s} {'util':>4s} {'uAct':>4s} {'bklg':>6s} {'late':>6s} {'hit':>6s} {'hD':>5s} {'pend':>5s} {'occD':>5s} | "
    f"{'med%':>6s} {'p99%':>6s} {'p99m%':>6s} {'bw%':>5s} n_q/n_d | per-min backlog GB / p99%")
for r in rows:
    say(f"{r['tag']:34s} {r['offered']:5.1f} {r['store_dram']:5.2f} {r['dram_peak20']:5.1f} {r['dram_peak1s']:5.1f} {r['store_cxl']:5.1f} {r['moved_GB']:4.0f} {r['achieved_frac']:5.3f} {r['budget_mean']:5.1f} "
        f"{r['budget_util']:4.2f} {r['budget_util_active']:4.2f} {r['backlog_max']:6.1f} {r['late_max_ms']:6.0f} {r['hit_share']:6.3f} {r['hits_dram']:5d} {r['pending']:5d} {r['occ_dram']:5.1f} | "
        f"{r['slow_med']:+6.1f} {r['slow_p99']:+6.1f} {r['slow_p99m']:+6.1f} {r['bw_loss']:+5.1f} {r['n_quiet']:.0f}/{r['n_during']:.0f} | {r['per_min_backlog']} / {r['per_min_p99']}")
out.close()
