#!/usr/bin/env python3
"""
phase3.py — Phase 3 placement-policy test.

Question: does a simple split / skew-aware placement beat naive interleave for
memory-intensive workloads when a co-tenant saturates CXL bandwidth?

Policies compared:
  dram        whole working set on DRAM (node 0) — baseline / "fits in DRAM"
  cxl         whole working set on CXL (node 1)
  interleave  pages striped 50/50 across DRAM + CXL
  split/skew  hot subset on DRAM, cold subset on CXL (exploits access skew)

Each policy is run twice:
  (a) solo (no aggressor)
  (b) under a streaming aggressor saturating CXL (membench stream-read, 8 threads,
      pinned to disjoint cores 64+)

Workloads:
  embedding  embbench.py, Zipfian gather, memory-bound config (row_dim=2048)
  kvcache    kvbench.py, decode access

Lock rule (caller decides): split must beat interleave by >= 15% on BOTH
workloads under the aggressor.

Output: benchmarks/results/<TS>-phase3/{embedding.csv, kvcache.csv, summary.txt}
"""
import csv
import os
import subprocess
import sys
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMBENCH = os.path.join(ROOT, "benchmarks", "memory", "membench")
KVBENCH = os.path.join(ROOT, "benchmarks", "kvcache", "kvbench.py")
EMBBENCH = os.path.join(ROOT, "benchmarks", "embedding", "embbench.py")

VICTIM_CPUS = "0-15"
AGG_CPU_OFFSET = 64
AGG_THREADS = 8
SINGLE_THREAD_ENV = {
    **os.environ,
    "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1",
}


def start_cxl_aggressor(seconds):
    cmd = [MEMBENCH, "--mode=stream-read", "--node=1", f"--threads={AGG_THREADS}",
           "--size=256M", f"--duration={seconds}", f"--cpu-offset={AGG_CPU_OFFSET}",
           "--csv", "--tag=agg"]
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)


def run_emb(place, dist="zipf"):
    # zipf-s=1.05 keeps the hot set larger than LLC (so it stays memory-resident
    # and placement actually matters) while still skewed toward low indices,
    # which is where embbench's skew policy puts the DRAM-resident hot rows.
    cmd = ["taskset", "-c", VICTIM_CPUS, "python3", EMBBENCH,
           "--rows=2000000", "--row-dim=2048", "--batch=8192", "--steps=40",
           f"--dist={dist}", "--zipf-s=1.05", f"--place={place}", "--hot-frac=0.1",
           "--csv", "--tag=run"]
    out = subprocess.run(cmd, capture_output=True, text=True, env=SINGLE_THREAD_ENV)
    if out.returncode != 0:
        sys.stderr.write(out.stderr); raise RuntimeError("embbench failed")
    row = [r for r in out.stdout.strip().splitlines() if not r.startswith("tag")][-1]
    return float(row.split(",")[9])    # per_step_ms


def run_kv(place):
    cmd = ["taskset", "-c", VICTIM_CPUS, "python3", KVBENCH,
           "--layers=32", "--heads=32", "--head-dim=128", "--seq-len=4096",
           "--batch=1", "--tokens=24", "--warmup=4", "--split-at=16",
           f"--place={place}", "--csv", "--tag=run"]
    out = subprocess.run(cmd, capture_output=True, text=True, env=SINGLE_THREAD_ENV)
    if out.returncode != 0:
        sys.stderr.write(out.stderr); raise RuntimeError("kvbench failed")
    row = [r for r in out.stdout.strip().splitlines() if not r.startswith("tag")][-1]
    return float(row.split(",")[10])   # per_token_ms


def measure(run_fn, place, with_agg, reps=3):
    """Median of `reps` runs. Each run is a fresh process, so pages start cold;
    we take the median to damp first-touch / frequency noise rather than letting
    a single cold run bias the comparison."""
    vals = []
    if not with_agg:
        for _ in range(reps):
            vals.append(run_fn(place))
    else:
        p = start_cxl_aggressor(120)
        time.sleep(1.0)
        try:
            for _ in range(reps):
                vals.append(run_fn(place))
        finally:
            p.terminate(); p.wait()
    vals.sort()
    return vals[len(vals) // 2]


def sweep(name, run_fn, places, outpath):
    print(f"\n===== {name} =====")
    rows = []
    with open(outpath, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["workload", "place", "solo_metric", "loaded_metric",
                    "loaded_slowdown"])
        for place in places:
            solo = measure(run_fn, place, False)
            loaded = measure(run_fn, place, True)
            sd = loaded / solo
            w.writerow([name, place, f"{solo:.3f}", f"{loaded:.3f}", f"{sd:.3f}"])
            rows.append((place, solo, loaded))
            print(f"  {place:<11} solo={solo:8.3f}  under_aggressor={loaded:8.3f}  "
                  f"slowdown={sd:.2f}x")
    return dict((p, (s, l)) for p, s, l in rows)


def report_split_vs_interleave(name, res, split_key):
    """Compute split-vs-interleave improvement under aggressor."""
    if "interleave" not in res or split_key not in res:
        print(f"  [{name}] missing interleave or {split_key}")
        return None
    il = res["interleave"][1]       # loaded
    sp = res[split_key][1]
    impr = (il - sp) / il * 100.0
    print(f"  [{name}] under aggressor: interleave={il:.3f}  {split_key}={sp:.3f}  "
          f"improvement={impr:+.1f}%  ({'>=15% PASS' if impr >= 15 else '<15% FAIL'})")
    return impr


def main():
    ts = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outdir = os.path.join(ROOT, "benchmarks", "results", f"{ts}-phase3")
    os.makedirs(outdir, exist_ok=True)
    print(f"writing to {outdir}")

    emb_res = sweep("embedding", run_emb,
                    ["dram", "cxl", "interleave", "skew"],
                    os.path.join(outdir, "embedding.csv"))
    kv_res = sweep("kvcache", run_kv,
                   ["dram", "cxl", "interleave", "split"],
                   os.path.join(outdir, "kvcache.csv"))

    print("\n===== SPLIT vs INTERLEAVE (under CXL aggressor) =====")
    emb_impr = report_split_vs_interleave("embedding", emb_res, "skew")
    kv_impr = report_split_vs_interleave("kvcache", kv_res, "split")

    with open(os.path.join(outdir, "summary.txt"), "w") as f:
        f.write(f"embedding skew-vs-interleave improvement: {emb_impr:+.1f}%\n")
        f.write(f"kvcache split-vs-interleave improvement: {kv_impr:+.1f}%\n")
        both = (emb_impr is not None and kv_impr is not None
                and emb_impr >= 15 and kv_impr >= 15)
        f.write(f"both >= 15%: {both}\n")
    print(f"\nDONE -> {outdir}")


if __name__ == "__main__":
    main()
