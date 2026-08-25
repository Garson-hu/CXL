#!/usr/bin/env python3
"""
confirm.py — Phase 2.2 confirmation runs (median of 5).

Conf 1: reproduce strongest interference signal.
  CXL + DRAM, stream-read victim threads {2,4}, stream-read aggressor (8 threads),
  disjoint cores (victim cpu 0+, aggressor cpu 64+). Report victim slowdown,
  aggressor bandwidth, total bandwidth.

Conf 2: reproduce strongest skew-placement signal.
  embedding, alpha {1.0,1.2,1.5} x hot {5%,10%}, policies {interleave, cxl, skew}.
  Report improvement of skew over interleave and over cxl-only.

Output: benchmarks/results/<TS>-confirm/{conf1.csv, conf2.csv, summary.txt}
"""
import csv, os, statistics, subprocess, sys, time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMBENCH = os.path.join(ROOT, "benchmarks", "memory", "membench")
EMBBENCH = os.path.join(ROOT, "benchmarks", "embedding", "embbench.py")
AGG_OFFSET, DUR, REPS = 64, 3.0, 5
ENV1 = {**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"}


def mb_total_bw(text):
    row = [r for r in text.strip().splitlines() if r and not r.startswith("tag")][-1]
    return float(row.split(",")[12])


def run_victim(node, threads):
    cmd = [MEMBENCH, "--mode=stream-read", f"--node={node}", f"--threads={threads}",
           "--size=256M", f"--duration={DUR}", "--cpu-offset=0", "--csv", "--tag=v"]
    out = subprocess.run(cmd, capture_output=True, text=True)
    out.check_returncode()
    return mb_total_bw(out.stdout)


def start_agg(node, seconds):
    cmd = [MEMBENCH, "--mode=stream-read", f"--node={node}", "--threads=8",
           "--size=256M", f"--duration={seconds}", f"--cpu-offset={AGG_OFFSET}",
           "--csv", "--tag=a"]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            text=True)


def emb(place, alpha, hf):
    cmd = ["taskset", "-c", "0-15", "python3", EMBBENCH,
           "--rows=2000000", "--row-dim=2048", "--batch=8192", "--steps=30",
           "--dist=zipf", f"--zipf-s={alpha}", f"--place={place}",
           f"--hot-frac={hf}", "--csv", "--tag=r"]
    out = subprocess.run(cmd, capture_output=True, text=True, env=ENV1)
    out.check_returncode()
    row = [r for r in out.stdout.strip().splitlines() if not r.startswith("tag")][-1]
    return float(row.split(",")[9])   # per_step_ms


def median(xs):
    return statistics.median(xs)


def conf1(outdir):
    print("\n===== CONF 1: interference (median of 5) =====")
    path = os.path.join(outdir, "conf1.csv")
    rows = []
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["node", "victim_threads", "baseline_bw", "loaded_victim_bw",
                    "slowdown", "aggressor_bw", "total_bw"])
        for node in (0, 1):
            for vth in (2, 4):
                base = median([run_victim(node, vth) for _ in range(REPS)])
                p = start_agg(node, DUR * (REPS + 3))
                time.sleep(1.0)
                vbws, abws = [], []
                for _ in range(REPS):
                    vbws.append(run_victim(node, vth))
                p.terminate()
                out, _ = p.communicate()
                try:
                    abw = mb_total_bw(out)
                except Exception:
                    abw = float("nan")
                vbw = median(vbws)
                sd = base / vbw
                total = vbw + abw
                w.writerow([node, vth, f"{base:.3f}", f"{vbw:.3f}", f"{sd:.3f}",
                            f"{abw:.3f}", f"{total:.3f}"])
                rows.append((node, vth, base, vbw, sd, abw, total))
                lbl = "DRAM" if node == 0 else "CXL"
                print(f"  {lbl} vth={vth}: baseline={base:.1f} loaded={vbw:.1f} "
                      f"slowdown={sd:.2f}x agg_bw={abw:.1f} total={total:.1f} GiB/s")
    return rows


def conf2(outdir):
    print("\n===== CONF 2: skew placement (median of 5) =====")
    path = os.path.join(outdir, "conf2.csv")
    rows = []
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["alpha", "hot_frac", "interleave_ms", "cxl_ms", "skew_ms",
                    "skew_vs_interleave_pct", "skew_vs_cxl_pct"])
        for alpha in (1.0, 1.2, 1.5):
            for hf in (0.05, 0.10):
                il = median([emb("interleave", alpha, hf) for _ in range(REPS)])
                cx = median([emb("cxl", alpha, hf) for _ in range(REPS)])
                sk = median([emb("skew", alpha, hf) for _ in range(REPS)])
                vi = (il - sk) / il * 100.0
                vc = (cx - sk) / cx * 100.0
                w.writerow([alpha, hf, f"{il:.3f}", f"{cx:.3f}", f"{sk:.3f}",
                            f"{vi:.1f}", f"{vc:.1f}"])
                rows.append((alpha, hf, il, cx, sk, vi, vc))
                print(f"  alpha={alpha} hot={hf:.0%}: il={il:.1f} cxl={cx:.1f} "
                      f"skew={sk:.1f}  skew/il={vi:+.1f}%  skew/cxl={vc:+.1f}%")
    return rows


def main():
    ts = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outdir = os.path.join(ROOT, "benchmarks", "results", f"{ts}-confirm")
    os.makedirs(outdir, exist_ok=True)
    print(f"writing to {outdir}")
    c1 = conf1(outdir)
    c2 = conf2(outdir)

    # Hold criteria
    cxl_sd = [sd for (node, vth, b, v, sd, a, t) in c1 if node == 1]
    dram_sd = [sd for (node, vth, b, v, sd, a, t) in c1 if node == 0]
    conf1_hold = all(sd >= 1.5 for sd in cxl_sd) and all(sd <= 1.15 for sd in dram_sd)
    strong = [vi for (al, hf, il, cx, sk, vi, vc) in c2 if vi >= 15]
    conf2_hold = len(strong) >= 1

    with open(os.path.join(outdir, "summary.txt"), "w") as f:
        f.write(f"conf1 CXL slowdowns: {[round(x,2) for x in cxl_sd]} "
                f"(all>=1.5: {all(s>=1.5 for s in cxl_sd)})\n")
        f.write(f"conf1 DRAM slowdowns: {[round(x,2) for x in dram_sd]} "
                f"(all<=1.15: {all(s<=1.15 for s in dram_sd)})\n")
        f.write(f"conf1 HOLD: {conf1_hold}\n")
        f.write(f"conf2 settings >=15% skew/il: {len(strong)} of {len(c2)}\n")
        f.write(f"conf2 HOLD: {conf2_hold}\n")
        f.write(f"BOTH HOLD: {conf1_hold and conf2_hold}\n")
    print(f"\nCONF1 HOLD: {conf1_hold}   CONF2 HOLD: {conf2_hold}   "
          f"BOTH: {conf1_hold and conf2_hold}")
    print(f"DONE -> {outdir}")


if __name__ == "__main__":
    main()
