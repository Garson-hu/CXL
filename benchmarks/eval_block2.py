#!/usr/bin/env python3
"""
eval_block2.py — ObjPlace evaluation block 2:
  (1) pressure sweep   — sensbench, aggressor threads 0/1/2/4/8
  (2) DRAM budget sweep — mixbench, budget 5/10/20/40/60% under CXL aggressor
  (3) GNN workload      — gnnbench, uniform + skewed, policies + objplace==manual
  (4) overhead          — obench

Output: benchmarks/results/<TS>-block2/{pressure.csv, budget.csv, gnn.csv,
        overhead.txt, summary.txt}
"""
import csv, os, statistics, subprocess, sys, time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMBENCH = os.path.join(ROOT, "benchmarks", "memory", "membench")
PL = os.path.join(ROOT, "system", "placement")
SENS, MIX, GNN, OB = (os.path.join(PL, x) for x in ("sensbench", "mixbench", "gnnbench", "obench"))
REPS = 5


def med(xs): return statistics.median(xs)


def start_agg(threads, seconds):
    if threads == 0:
        return None
    return subprocess.Popen([MEMBENCH, "--mode=stream-read", "--node=1",
                             f"--threads={threads}", "--size=256M",
                             f"--duration={seconds}", "--cpu-offset=64",
                             "--csv", "--tag=a"], stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True)


def agg_bw(p):
    if p is None: return 0.0
    out, _ = p.communicate()
    try:
        return float([r for r in out.strip().splitlines() if not r.startswith("tag")][-1].split(",")[12])
    except Exception:
        return float("nan")


def sens(policy):
    o = subprocess.run([SENS, f"--policy={policy}", "--size=1073741824",
                        "--duration=3", "--csv", "--tag=s"],
                       capture_output=True, text=True); o.check_returncode()
    return float(o.stdout.strip().split(",")[3])


def mix(planner, bf):
    o = subprocess.run([MIX, f"--planner={planner}", f"--budget-frac={bf}",
                        "--duration=3", "--csv", "--tag=m"],
                       capture_output=True, text=True); o.check_returncode()
    parts = o.stdout.strip().split(",")
    return float(parts[3])    # score


def gnn(policy, alpha):
    o = subprocess.run([GNN, f"--policy={policy}", "--nodes=2000000", "--feat=256",
                        "--batch=8192", "--steps=40", f"--alpha={alpha}",
                        "--hot-frac=0.1", "--csv", "--tag=g"],
                       capture_output=True, text=True); o.check_returncode()
    return float(o.stdout.strip().split(",")[3])   # per_step_ms


def run_under_agg(fn, arg, threads, n=REPS):
    p = start_agg(threads, n * 4 + 6)
    if p is not None: time.sleep(1.0)
    try: v = med([fn(*arg) for _ in range(n)])
    finally:
        if p is not None: p.terminate()
    bw = agg_bw(p)
    return v, bw


def main():
    ts = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    out = os.path.join(ROOT, "benchmarks", "results", f"{ts}-block2"); os.makedirs(out, exist_ok=True)
    print(f"writing to {out}")
    S = []

    # (1) pressure sweep
    print("\n[pressure sweep — sensbench, bandwidth-object throughput GiB/s]")
    pol = ["cxl", "interleave", "hotness", "manual", "objplace"]
    with open(os.path.join(out, "pressure.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["agg_threads", "policy", "victim_gib_s", "aggressor_gib_s"])
        base = {}
        for th in (0, 1, 2, 4, 8):
            row = {}
            for p in pol:
                v, bw = run_under_agg(sens, (p,), th)
                row[p] = v
                w.writerow([th, p, f"{v:.3f}", f"{bw:.3f}"])
            if th == 0: base = dict(row)
            imp_h = (row["objplace"] - row["hotness"]) / row["hotness"] * 100
            imp_i = (row["objplace"] - row["interleave"]) / row["interleave"] * 100
            print(f"  agg={th}: cxl={row['cxl']:.1f} il={row['interleave']:.1f} "
                  f"hot={row['hotness']:.1f} obj={row['objplace']:.1f} man={row['manual']:.1f} "
                  f"| obj vs hot +{imp_h:.0f}%  obj vs il +{imp_i:.0f}%")
            if th == 8:
                S.append(f"Pressure@agg8: objplace {row['objplace']:.1f} vs hotness {row['hotness']:.1f} GiB/s (+{imp_h:.0f}%), vs interleave +{imp_i:.0f}%")

    # (2) DRAM budget sweep (under aggressor)
    print("\n[DRAM budget sweep — mixbench score under CXL aggressor]")
    planners = ["hotness", "sensitivity", "objplace", "manual"]
    with open(os.path.join(out, "budget.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["budget_frac", "planner", "score"])
        for bf in (0.05, 0.10, 0.20, 0.40, 0.60):
            row = {}
            for pl_ in planners:
                v, _ = run_under_agg(mix, (pl_, bf), 8)
                row[pl_] = v
                w.writerow([bf, pl_, f"{v:.3f}"])
            imp = (row["objplace"] - row["hotness"]) / row["hotness"] * 100 if row["hotness"] else 0
            print(f"  budget={bf:.0%}: hot={row['hotness']:.1f} sens={row['sensitivity']:.1f} "
                  f"obj={row['objplace']:.1f} man={row['manual']:.1f} | obj vs hot +{imp:.0f}%")
            if abs(bf - 0.40) < 1e-9:
                S.append(f"Budget@40%: objplace {row['objplace']:.1f} vs hotness {row['hotness']:.1f} (+{imp:.0f}%), manual {row['manual']:.1f}")

    # (3) GNN workload
    print("\n[GNN workload — gnnbench per-step ms]")
    with open(os.path.join(out, "gnn.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["access", "policy", "per_step_ms"])
        for label, alpha in (("uniform", 0.0), ("skewed", 1.2)):
            row = {}
            for p in ("cxl", "interleave", "hotness", "objplace"):
                row[p] = med([gnn(p, alpha) for _ in range(REPS)])
                w.writerow([label, p, f"{row[p]:.3f}"])
            man = med([gnn("skew", alpha) for _ in range(REPS)])
            w.writerow([label, "manual(skew)", f"{man:.3f}"])
            imp_i = (row["interleave"] - row["objplace"]) / row["interleave"] * 100
            obj_vs_man = (row["objplace"] - man) / man * 100
            print(f"  {label}: cxl={row['cxl']:.2f} il={row['interleave']:.2f} "
                  f"hot={row['hotness']:.2f} obj={row['objplace']:.2f} man={man:.2f} "
                  f"| obj vs il +{imp_i:.0f}%  obj vs manual {obj_vs_man:+.1f}%")
            S.append(f"GNN {label}: objplace vs interleave +{imp_i:.0f}%, vs manual {obj_vs_man:+.1f}%")

    # (4) overhead
    print("\n[overhead — obench]")
    o = subprocess.run([OB], capture_output=True, text=True, env={**os.environ, "OBENCH_CSV": "1"})
    print(o.stdout)
    open(os.path.join(out, "overhead.txt"), "w").write(o.stdout)

    open(os.path.join(out, "summary.txt"), "w").write("\n".join(S) + "\n")
    print("\n=== SUMMARY ===\n" + "\n".join(S))
    print(f"\nDONE -> {out}")


if __name__ == "__main__":
    main()
