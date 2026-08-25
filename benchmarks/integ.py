#!/usr/bin/env python3
"""
integ.py — placement-API integration measurements.

Part 1 (embedding, solo, median of 5):
  compare cxl / interleave / skew (manual numa) / skew-hint (obj_alloc_hint)
  for alpha=1.0,hot=10% and alpha=1.5,hot=10%.
  Validates that the obj_alloc_hint path matches manual skew within noise.

Part 2 (bandwidth-sensitive synthetic, median of 5):
  bwbench policies allcxl / interleave / hint, run solo and under an 8-thread
  CXL stream aggressor on disjoint cores. Reports victim slowdown and the
  throughput recovery of hint vs allcxl under the aggressor.

Output: benchmarks/results/<TS>-integ/{embedding.csv, bwbench.csv, summary.txt}
"""
import csv, os, statistics, subprocess, sys, time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMBENCH = os.path.join(ROOT, "benchmarks", "memory", "membench")
EMBBENCH = os.path.join(ROOT, "benchmarks", "embedding", "embbench.py")
BWBENCH = os.path.join(ROOT, "system", "placement", "bwbench")
REPS = 5
ENV1 = {**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"}


def median(xs):
    return statistics.median(xs)


def emb(place, alpha, hf):
    cmd = ["taskset", "-c", "0-15", "python3", EMBBENCH,
           "--rows=2000000", "--row-dim=2048", "--batch=8192", "--steps=30",
           "--dist=zipf", f"--zipf-s={alpha}", f"--place={place}",
           f"--hot-frac={hf}", "--csv", "--tag=r"]
    out = subprocess.run(cmd, capture_output=True, text=True, env=ENV1)
    out.check_returncode()
    row = [r for r in out.stdout.strip().splitlines() if not r.startswith("tag")][-1]
    return float(row.split(",")[9])   # per_step_ms


def bw(policy):
    cmd = [BWBENCH, f"--policy={policy}", "--threads=4", "--hot=1073741824",
           "--cold=2147483648", "--duration=3", "--csv", "--tag=b"]
    out = subprocess.run(cmd, capture_output=True, text=True)
    out.check_returncode()
    return float(out.stdout.strip().split(",")[4])   # GiB/s


def start_cxl_agg(seconds):
    cmd = [MEMBENCH, "--mode=stream-read", "--node=1", "--threads=8",
           "--size=256M", f"--duration={seconds}", "--cpu-offset=64",
           "--csv", "--tag=a"]
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def part1(outdir):
    print("\n===== PART 1: embedding placement (solo, median of 5) =====")
    path = os.path.join(outdir, "embedding.csv")
    results = {}
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["alpha", "hot_frac", "place", "per_step_ms"])
        for alpha, hf in [(1.0, 0.10), (1.5, 0.10)]:
            row = {}
            for place in ("cxl", "interleave", "skew", "skew-hint"):
                v = median([emb(place, alpha, hf) for _ in range(REPS)])
                row[place] = v
                w.writerow([alpha, hf, place, f"{v:.3f}"])
            results[(alpha, hf)] = row
            hint_vs_manual = abs(row["skew-hint"] - row["skew"]) / row["skew"] * 100
            skew_vs_il = (row["interleave"] - row["skew"]) / row["interleave"] * 100
            print(f"  alpha={alpha} hot={hf:.0%}: cxl={row['cxl']:.1f} "
                  f"il={row['interleave']:.1f} skew={row['skew']:.1f} "
                  f"skew-hint={row['skew-hint']:.1f}  "
                  f"|hint-manual|={hint_vs_manual:.1f}%  skew/il=+{skew_vs_il:.1f}%")
    return results


def part2(outdir):
    print("\n===== PART 2: bandwidth-sensitive synthetic (median of 5) =====")
    path = os.path.join(outdir, "bwbench.csv")
    res = {}
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["policy", "solo_gib_s", "loaded_gib_s", "slowdown"])
        for policy in ("allcxl", "interleave", "hint"):
            solo = median([bw(policy) for _ in range(REPS)])
            p = start_cxl_agg(REPS * 4 + 5)
            time.sleep(1.0)
            loaded = median([bw(policy) for _ in range(REPS)])
            p.terminate(); p.wait()
            sd = solo / loaded
            w.writerow([policy, f"{solo:.3f}", f"{loaded:.3f}", f"{sd:.3f}"])
            res[policy] = (solo, loaded)
            print(f"  {policy:<11} solo={solo:6.1f}  under_aggressor={loaded:6.1f}  "
                  f"slowdown={sd:.2f}x GiB/s")
    return res


def main():
    ts = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outdir = os.path.join(ROOT, "benchmarks", "results", f"{ts}-integ")
    os.makedirs(outdir, exist_ok=True)
    print(f"writing to {outdir}")
    p1 = part1(outdir)
    p2 = part2(outdir)

    # Summaries
    with open(os.path.join(outdir, "summary.txt"), "w") as f:
        for (alpha, hf), row in p1.items():
            hvm = abs(row["skew-hint"] - row["skew"]) / row["skew"] * 100
            svi = (row["interleave"] - row["skew"]) / row["interleave"] * 100
            f.write(f"emb alpha={alpha} hot={hf}: skew/il=+{svi:.1f}% "
                    f"hint-vs-manual={hvm:.1f}%\n")
        if "allcxl" in p2 and "hint" in p2:
            recov = (p2["hint"][1] - p2["allcxl"][1]) / p2["allcxl"][1] * 100
            f.write(f"bwbench under aggressor: allcxl={p2['allcxl'][1]:.1f} "
                    f"hint={p2['hint'][1]:.1f} GiB/s  recovery=+{recov:.0f}%\n")
            print(f"\nbwbench recovery (hint vs allcxl, under aggressor): +{recov:.0f}%")
    print(f"DONE -> {outdir}")


if __name__ == "__main__":
    main()
