#!/usr/bin/env python3
"""Summarize the hardware co-runs of the 2026-10-21 validation (run_kvreplay.py; kvreplay + the Adam step) in <dir> ->
<dir>/summary.csv and a markdown table on stdout.
Neighbour: quiet = Adam steps that END inside the BEFORE window; during = steps that end between the replayer's START and
its last completed store (or the alone window). slow_p99 = p99 during / p99 quiet - 1 (THE SLO of 2026-10-12, <= 7%);
also slow_med, slow_p95, slow_p99m (= p99 during / quiet median - 1), per-minute p99 slowdown.
Replay: DRAM write rate from the per-store start/end records (bytes spread over each store's transfer) — mean / p95 / p99 / max at 10 ms, 100 ms and 1 s; share of 10 ms bins above
8 GB/s; CXL-targeted bytes issued or skipped (not issued); backlog max; start delay (start - due) p99 / max and completion
after due; stores issued; live-bucket decisions; replayer CPU seconds.
usage: analyze_kvreplay.py <dir> [tag-prefix]"""
import gzip
import csv, glob, os, re, statistics as st, sys
def rd(p):   # raw text files may be gzip-compressed in place after the campaign
    if os.path.exists(p): return open(p).read()
    if os.path.exists(p + ".gz"): return gzip.open(p + ".gz", "rt").read()
    return ""
def ex(p): return os.path.exists(p) or os.path.exists(p + ".gz")
D = sys.argv[1]; PFX = sys.argv[2] if len(sys.argv) > 2 else ""
def q(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else float("nan")
def agg(v, k): return [sum(v[i:i + k]) / k for i in range(0, len(v) - k + 1, k)] or [max(v) if v else 0.0]
def binrates(ev, dt, T):
    """per-store records (start s, end s, bytes), each spread uniformly over [start, end) -> GB/s per bin of dt over [0, T)"""
    n = int(T / dt) + 1; v = [0.0] * n
    for s_, e, b in ev:
        if e <= s_: e = s_ + 1e-6
        i0, i1 = int(s_ / dt), min(int(e / dt), n - 1)
        for i in range(i0, i1 + 1):
            x0, x1 = max(s_, i * dt), min(e, (i + 1) * dt)
            if x1 > x0: v[i] += b * (x1 - x0) / (e - s_)
    return [x / dt / 1e9 for x in v]
rows = []
for meta in sorted(glob.glob(f"{D}/{PFX}*-meta.txt")):
    tag = os.path.basename(meta)[:-9]; M = {}; cfg = {}
    for l in open(meta):
        f = l.split(); M[f[1]] = int(f[2])
        if f[1] == "config": cfg = dict(x.split("=", 1) for x in f[3:] if "=" in x)
    if "done" not in M: continue
    r = dict(tag=tag, writelog=os.path.basename(cfg.get("writelog", "none")), neighbor=cfg.get("neighbor"), replay_opts=cfg.get("replay", ""), window=f"{cfg.get('t0')}-{cfg.get('t1')}")
    # ---- replay ----
    rf = f"{D}/{tag}-replay.txt"; d0 = d1 = None
    if ex(rf) and cfg.get("writelog", "none") != "none":
        txt = rd(rf); m = re.search(r"^START (\d+)", txt, re.M)
        if m:
            d0 = int(m[1]); W = [[float(x) for x in l.split()[1:]] for l in txt.splitlines() if l.startswith("W ")]
            S = " ".join(l for l in txt.splitlines() if l.startswith("S ")); nums = dict(re.findall(r"([a-z_0-9]+) ([\d.]+)", S))
            act = float(nums.get("active_s", 0)); d1 = d0 + int(act * 1e9)
            W = [w for w in W if w[0] <= d1 + 1e7] or W
            bl = [w[5] for w in W]; off = [w[1] for w in W]
            # rates from the per-store records (exact start / end stamps); the W lines' rates can be distorted by a stalled logger sample (one 10 ms bin of 1,116 GB/s in fid-conversation-70b-4x-admitall = an NFS flush)
            Rr = [l.split() for l in txt.splitlines() if l.startswith("R ")]
            evD = [(float(x[3]) / 1e3, float(x[4]) / 1e3, float(x[5])) for x in Rr if x[6] == "D" and x[7] == "1"]
            byC = sum(float(x[5]) for x in Rr if x[6] == "C" and x[7] == "1"); bySk = sum(float(x[5]) for x in Rr if x[7] == "0")
            T = max(act, 1e-3); r10 = binrates(evD, 0.01, T) if evD else [0.0]; r100 = binrates(evD, 0.1, T) if evD else [0.0]; r1 = binrates(evD, 1.0, T) if evD else [0.0]
            r.update(span_s=round(act, 1), offered_mean=round(st.mean(off), 3), dram_mean=round(sum(b for _, _, b in evD) / T / 1e9, 3), dram_p95_10ms=round(q(r10, .95), 2), dram_p99_10ms=round(q(r10, .99), 2), dram_max_10ms=round(max(r10), 2),
                     dram_p99_100ms=round(q(r100, .99), 2), dram_max_100ms=round(max(r100), 2), dram_p99_1s=round(q(r1, .99), 2), dram_max_1s=round(max(r1), 2),
                     dram_over8_10ms_pct=round(100 * sum(1 for x in r10 if x > 8) / len(r10), 2), cxl_issued_mean=round(byC / T / 1e9, 3), cxl_skipped_mean=round(bySk / T / 1e9, 3), backlog_max_GB=round(max(bl), 2),
                     stores=int(nums.get("stores", 0)), issued_dram=int(nums.get("issued_dram", 0)), issued_cxl=int(nums.get("issued_cxl", 0)), skipped=int(nums.get("skipped", 0)),
                     bytes_dram_GB=float(nums.get("bytes_dram_GB", 0)), bytes_skipped_GB=float(nums.get("bytes_skipped_GB", 0)),
                     cand=int(nums.get("cand", 0)), granted=int(nums.get("granted", 0)), refused=int(nums.get("refused", 0)), cpu_s=round(float(nums.get("cpu_user_s", 0)) + float(nums.get("cpu_sys_s", 0)), 1), stopped_early=int(nums.get("stopped_early", 0)))
            m2 = re.search(r"start_delay_ms p50 ([\d.]+) p90 ([\d.]+) p99 ([\d.]+) max ([\d.]+) \| completion_after_due_ms p50 ([\d.]+) p90 ([\d.]+) p99 ([\d.]+) max ([\d.]+)", txt)
            if m2: r.update(delay_p50_ms=float(m2[1]), delay_p99_ms=float(m2[3]), delay_max_ms=float(m2[4]), compl_p99_ms=float(m2[7]), compl_max_ms=float(m2[8]))
    elif "during_start" in M: d0, d1 = M["during_start"], M["during_end"]
    # ---- neighbour ----
    nf = f"{D}/{tag}-neighbor.txt"
    if ex(nf) and "before_start" in M and d0:
        steps = [(int(t), float(v)) for v, t in re.findall(r"\[STEP\] \d+ ([\d.]+) (\d+)", rd(nf))]
        qs = [v for t, v in steps if M["before_start"] <= t < M["before_end"]]; ds = [v for t, v in steps if d0 <= t < d1]
        if qs and ds:
            r.update(n_quiet=len(qs), n_during=len(ds), q_med=round(st.median(qs), 4), q_p99=round(q(qs, .99), 4), d_med=round(st.median(ds), 4), d_p95=round(q(ds, .95), 4), d_p99=round(q(ds, .99), 4),
                     slow_med=round(100 * (st.median(ds) / st.median(qs) - 1), 2), slow_p95=round(100 * (q(ds, .95) / q(qs, .95) - 1), 2), slow_p99=round(100 * (q(ds, .99) / q(qs, .99) - 1), 2),
                     slow_p99m=round(100 * (q(ds, .99) / st.median(qs) - 1), 2))
            pm = []
            for k in range(int((d1 - d0) / 60e9) + 1):
                v = [x for t, x in steps if d0 + k * 60e9 <= t < min(d1, d0 + (k + 1) * 60e9)]
                if len(v) >= 20: pm.append(100 * (q(v, .99) / q(qs, .99) - 1))
            r["per_min_p99"] = " ".join(f"{x:+.1f}" for x in pm)
    rows.append(r)
keys = []
for r in rows:
    for k in r:
        if k not in keys: keys.append(k)
with open(f"{D}/summary.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); [w.writerow(r) for r in rows]
print("| tag | log | neighbour | Adam steps quiet / during | quiet p99 s | during p99 s | slow med / p95 / p99 (%) | per-minute p99 (%) | DRAM GB/s mean / p99 10 ms / max 10 ms / max 100 ms / max 1 s | 10 ms > 8 GB/s | CXL skipped GB/s | backlog max GB | start delay p99 / max ms | stores issued D / C / skipped | bucket cand / granted / refused | CPU s |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for r in rows:
    g = lambda k, f="{}": f.format(r[k]) if k in r else "–"
    print(f"| {r['tag']} | {r['writelog']} | {r['neighbor']} | {g('n_quiet')} / {g('n_during')} | {g('q_p99')} | {g('d_p99')} | {g('slow_med')} / {g('slow_p95')} / {g('slow_p99')} | {g('per_min_p99')} | "
          f"{g('dram_mean')} / {g('dram_p99_10ms')} / {g('dram_max_10ms')} / {g('dram_max_100ms')} / {g('dram_max_1s')} | {g('dram_over8_10ms_pct')}% | {g('cxl_skipped_mean')} | {g('backlog_max_GB')} | {g('delay_p99_ms')} / {g('delay_max_ms')} | "
          f"{g('issued_dram')} / {g('issued_cxl')} / {g('skipped')} | {g('cand')} / {g('granted')} / {g('refused')} | {g('cpu_s')} |")
