#!/usr/bin/env python3
"""
phase21.py — Phase 2.1 interference characterization.

Refines Phase 2 by:
  * including pointer-chase (latency), KV-cache, and embedding-gather as victims
  * sweeping aggressor thread count 1,2,4,8
  * running victim and aggressor on DISJOINT cores (victim cpu 0-7, aggressor
    cpu 64+) so we measure MEMORY contention, not CPU contention
  * computing a cross-workload asymmetry matrix that, unlike Phase 2, includes
    a low-bandwidth latency workload as an *aggressor*

Aggressor for the sweep = membench stream-read (clean, controllable bandwidth
saturator). Victims for the sweep = membench latency, membench random-read,
the real kvbench.py, and the real embbench.py.

Asymmetry matrix = membench {latency, random-read, stream-read} as both victim
and aggressor at a fixed 8-thread aggressor load.

Output: benchmarks/results/<TS>-phase21/{sweep.csv, asym.csv, summary.txt}
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

VICTIM_CPUS = "0-7"
AGG_CPU_OFFSET = 64
VICTIM_DUR = 3.0
AGG_MARGIN = 3.0          # aggressor runs this many extra seconds
SINGLE_THREAD_ENV = {
    **os.environ,
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}


def parse_membench_csv(text):
    """Return the last data row of a membench --csv output as a dict."""
    rows = [r for r in text.strip().splitlines() if r and not r.startswith("tag")]
    last = rows[-1].split(",")
    return {
        "bandwidth_gib_s": float(last[8]),
        "avg_latency_ns": float(last[9]),
        "victim_latency_ns": float(last[10]),
        "total_bandwidth_gib_s": float(last[12]),
    }


def run_membench(mode, node, threads, size, dur, cpu_offset=0):
    cmd = [MEMBENCH, f"--mode={mode}", f"--node={node}", f"--threads={threads}",
           f"--size={size}", f"--duration={dur}", "--csv",
           f"--cpu-offset={cpu_offset}", "--tag=run"]
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        sys.stderr.write(out.stderr)
        raise RuntimeError(f"membench failed: {' '.join(cmd)}")
    return parse_membench_csv(out.stdout)


def start_aggressor(mode, node, threads, dur):
    """Launch a background membench aggressor; return Popen handle."""
    cmd = [MEMBENCH, f"--mode={mode}", f"--node={node}", f"--threads={threads}",
           "--size=256M", f"--duration={dur}", "--csv",
           f"--cpu-offset={AGG_CPU_OFFSET}", "--tag=agg"]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            text=True)


def finish_aggressor(p):
    out, _ = p.communicate()
    try:
        return parse_membench_csv(out)["total_bandwidth_gib_s"]
    except Exception:
        return float("nan")


def run_victim_membench(mode, node):
    # Victim pinned to low cores via cpu-offset 0; 1 thread.
    return run_membench(mode, node, 1, "512M", VICTIM_DUR, cpu_offset=0)


def run_victim_kv(node):
    place = "dram" if node == 0 else "cxl"
    cmd = ["taskset", "-c", VICTIM_CPUS, "python3", KVBENCH,
           "--layers=32", "--heads=32", "--head-dim=128", "--seq-len=2048",
           "--batch=1", "--tokens=32", "--warmup=4", f"--place={place}",
           "--csv", "--tag=run"]
    out = subprocess.run(cmd, capture_output=True, text=True, env=SINGLE_THREAD_ENV)
    if out.returncode != 0:
        sys.stderr.write(out.stderr)
        raise RuntimeError("kvbench failed")
    row = [r for r in out.stdout.strip().splitlines() if not r.startswith("tag")][-1]
    parts = row.split(",")
    return {"per_token_ms": float(parts[10]), "bandwidth_gib_s": float(parts[11])}


def run_victim_emb(node):
    place = "dram" if node == 0 else "cxl"
    cmd = ["taskset", "-c", VICTIM_CPUS, "python3", EMBBENCH,
           "--rows=20000000", "--row-dim=128", "--batch=4096", "--steps=100",
           "--dist=zipf", f"--place={place}", "--csv", "--tag=run"]
    out = subprocess.run(cmd, capture_output=True, text=True, env=SINGLE_THREAD_ENV)
    if out.returncode != 0:
        sys.stderr.write(out.stderr)
        raise RuntimeError("embbench failed")
    row = [r for r in out.stdout.strip().splitlines() if not r.startswith("tag")][-1]
    parts = row.split(",")
    return {"per_step_ms": float(parts[9]), "bandwidth_gib_s": float(parts[10])}


# Victim metric helpers: (run_fn, metric_key, lower_is_better)
VICTIMS = {
    "latency":      (lambda n: run_victim_membench("latency", n), "victim_latency_ns", True),
    "random-read":  (lambda n: run_victim_membench("random-read", n), "total_bandwidth_gib_s", False),
    "kvcache":      (run_victim_kv, "per_token_ms", True),
    "embedding":    (run_victim_emb, "per_step_ms", True),
}


def victim_value(name, result):
    _, key, _ = VICTIMS[name]
    return result[key]


def slowdown(name, base, loaded):
    _, _, lower_is_better = VICTIMS[name]
    b = victim_value(name, base)
    l = victim_value(name, loaded)
    if lower_is_better:
        return l / b      # bigger metric = worse
    else:
        return b / l      # smaller bw = worse


# Membench-only slowdown for the asymmetry matrix (modes not in VICTIMS).
_MB_METRIC = {
    "latency":     ("victim_latency_ns", True),
    "random-read": ("total_bandwidth_gib_s", False),
    "stream-read": ("total_bandwidth_gib_s", False),
}


def mb_slowdown(mode, base, loaded):
    key, lower_is_better = _MB_METRIC[mode]
    b, l = base[key], loaded[key]
    return (l / b) if lower_is_better else (b / l)


def main():
    ts = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outdir = os.path.join(ROOT, "benchmarks", "results", f"{ts}-phase21")
    os.makedirs(outdir, exist_ok=True)
    print(f"writing to {outdir}")

    # ---- Part A: aggressor thread sweep ----
    sweep_path = os.path.join(outdir, "sweep.csv")
    with open(sweep_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["node", "victim", "agg_threads", "victim_metric",
                    "victim_value", "slowdown", "aggressor_bw_gib_s"])
        for node in (0, 1):
            for vname in VICTIMS:
                run_fn = VICTIMS[vname][0]
                base = run_fn(node)
                base_val = victim_value(vname, base)
                metric = VICTIMS[vname][1]
                w.writerow([node, vname, 0, metric, f"{base_val:.4f}", "1.000", "0.000"])
                print(f"[node {node}] {vname:<12} baseline {metric}={base_val:.4f}")
                for t in (1, 2, 4, 8):
                    p = start_aggressor("stream-read", node, t, VICTIM_DUR + AGG_MARGIN)
                    time.sleep(1.0)   # let aggressor ramp
                    loaded = run_fn(node)
                    agg_bw = finish_aggressor(p)
                    sd = slowdown(vname, base, loaded)
                    lv = victim_value(vname, loaded)
                    w.writerow([node, vname, t, metric, f"{lv:.4f}",
                                f"{sd:.3f}", f"{agg_bw:.3f}"])
                    print(f"[node {node}] {vname:<12} agg_t={t} "
                          f"slowdown={sd:.2f}x agg_bw={agg_bw:.1f} GiB/s")

    # ---- Part B: cross-workload asymmetry (membench only, 8-thread aggressor) ----
    asym_path = os.path.join(outdir, "asym.csv")
    modes = ["latency", "random-read", "stream-read"]
    # baselines
    base_cache = {}
    with open(asym_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["node", "victim", "aggressor", "victim_metric",
                    "baseline_value", "loaded_value", "slowdown", "aggressor_bw_gib_s"])
        for node in (0, 1):
            for vm in modes:
                base_cache[(node, vm)] = run_victim_membench(vm, node)
            for vm in modes:
                for am in modes:
                    p = start_aggressor(am, node, 8, VICTIM_DUR + AGG_MARGIN)
                    time.sleep(1.0)
                    loaded = run_victim_membench(vm, node)
                    agg_bw = finish_aggressor(p)
                    base = base_cache[(node, vm)]
                    sd = mb_slowdown(vm, base, loaded)
                    metric = _MB_METRIC[vm][0]
                    w.writerow([node, vm, am, metric,
                                f"{base[metric]:.4f}",
                                f"{loaded[metric]:.4f}",
                                f"{sd:.3f}", f"{agg_bw:.3f}"])
                    print(f"[node {node}] victim={vm:<12} agg={am:<12} "
                          f"slowdown={sd:.2f}x agg_bw={agg_bw:.1f}")

    print(f"\nDONE. sweep -> {sweep_path}\n      asym  -> {asym_path}")


if __name__ == "__main__":
    main()
