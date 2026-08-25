#!/usr/bin/env python3
"""
eval_objplace.py — ObjPlace evaluation against baselines (median of 5).

Targets:
  T1 ObjPlace matches manual (embedding + gnn)
  T2 ObjPlace beats interleave ~15% on skewed embedding
  T3 ObjPlace protects bandwidth-sensitive objects under CXL aggressor (bwbench)
  T4 hotness-only weaker than ObjPlace when ignoring sensitivity (sensbench)
  T5 overhead small (objplace vs manual)

Output: benchmarks/results/<TS>-eval/{embedding.csv, gnn.csv, bwbench.csv,
        sensbench.csv, summary.txt}
"""
import csv, os, statistics, subprocess, sys, time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMBENCH = os.path.join(ROOT, "benchmarks", "memory", "membench")
EMBBENCH = os.path.join(ROOT, "benchmarks", "embedding", "embbench.py")
PL = os.path.join(ROOT, "system", "placement")
BW, GNN, SENS = (os.path.join(PL, x) for x in ("bwbench", "gnnbench", "sensbench"))
REPS = 5
ENV1 = {**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"}


def med(xs): return statistics.median(xs)


def emb(place, alpha=1.0, hf=0.10):
    cmd = ["taskset", "-c", "0-15", "python3", EMBBENCH,
           "--rows=2000000", "--row-dim=2048", "--batch=8192", "--steps=30",
           "--dist=zipf", f"--zipf-s={alpha}", f"--place={place}",
           f"--hot-frac={hf}", "--csv", "--tag=r"]
    o = subprocess.run(cmd, capture_output=True, text=True, env=ENV1); o.check_returncode()
    return float([r for r in o.stdout.strip().splitlines() if not r.startswith("tag")][-1].split(",")[9])


def gnn(policy):
    o = subprocess.run([GNN, f"--policy={policy}", "--nodes=2000000", "--feat=256",
                        "--batch=8192", "--steps=40", "--alpha=1.0", "--hot-frac=0.1",
                        "--csv", "--tag=r"], capture_output=True, text=True); o.check_returncode()
    return float(o.stdout.strip().split(",")[3])   # per_step_ms


def bwb(policy):
    o = subprocess.run([BW, f"--policy={policy}", "--threads=4", "--hot=1073741824",
                        "--cold=2147483648", "--duration=3", "--csv", "--tag=b"],
                       capture_output=True, text=True); o.check_returncode()
    return float(o.stdout.strip().split(",")[4])   # GiB/s


def sens(policy):
    o = subprocess.run([SENS, f"--policy={policy}", "--size=1073741824",
                        "--duration=3", "--csv", "--tag=s"],
                       capture_output=True, text=True); o.check_returncode()
    return float(o.stdout.strip().split(",")[3])   # GiB/s


def start_agg(seconds):
    return subprocess.Popen([MEMBENCH, "--mode=stream-read", "--node=1", "--threads=8",
                             "--size=256M", f"--duration={seconds}", "--cpu-offset=64",
                             "--csv", "--tag=a"], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)


def med_under_agg(fn, policy, n=REPS):
    p = start_agg(n * 4 + 6); time.sleep(1.0)
    try: v = med([fn(policy) for _ in range(n)])
    finally: p.terminate(); p.wait()
    return v


def main():
    ts = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    out = os.path.join(ROOT, "benchmarks", "results", f"{ts}-eval"); os.makedirs(out, exist_ok=True)
    print(f"writing to {out}")
    S = {}

    # T1/T2/T5 embedding (solo)
    print("\n[embedding]")
    emb_r = {p: med([emb(p) for _ in range(REPS)]) for p in
             ("cxl", "interleave", "skew", "objplace")}
    with open(os.path.join(out, "embedding.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["place", "per_step_ms"])
        for p, v in emb_r.items(): w.writerow([p, f"{v:.3f}"]); print(f"  {p:<11}{v:.2f} ms")
    S["emb_obj_vs_manual"] = (emb_r["objplace"] - emb_r["skew"]) / emb_r["skew"] * 100
    S["emb_obj_vs_il"] = (emb_r["interleave"] - emb_r["objplace"]) / emb_r["interleave"] * 100

    # T1 gnn (solo)
    print("\n[gnn]")
    gnn_r = {p: med([gnn(p) for _ in range(REPS)]) for p in
             ("dram", "cxl", "interleave", "skew", "objplace")}
    with open(os.path.join(out, "gnn.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["policy", "per_step_ms"])
        for p, v in gnn_r.items(): w.writerow([p, f"{v:.3f}"]); print(f"  {p:<11}{v:.2f} ms")
    S["gnn_obj_vs_manual"] = (gnn_r["objplace"] - gnn_r["skew"]) / gnn_r["skew"] * 100
    S["gnn_obj_vs_il"] = (gnn_r["interleave"] - gnn_r["objplace"]) / gnn_r["interleave"] * 100

    # T3 bwbench under aggressor
    print("\n[bwbench under CXL aggressor]")
    bw_r = {}
    for p in ("allcxl", "interleave", "hint", "objplace"):
        bw_r[p] = med_under_agg(bwb, p)
        print(f"  {p:<11}{bw_r[p]:.2f} GiB/s")
    with open(os.path.join(out, "bwbench.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["policy", "loaded_gib_s"])
        for p, v in bw_r.items(): w.writerow([p, f"{v:.3f}"])
    S["bw_recovery"] = (bw_r["objplace"] - bw_r["allcxl"]) / bw_r["allcxl"] * 100

    # T4 sensbench under aggressor
    print("\n[sensbench under CXL aggressor]")
    sens_r = {}
    for p in ("hotness", "objplace"):
        sens_r[p] = med_under_agg(sens, p)
        print(f"  {p:<11}{sens_r[p]:.2f} GiB/s")
    with open(os.path.join(out, "sensbench.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["policy", "bw_object_gib_s"])
        for p, v in sens_r.items(): w.writerow([p, f"{v:.3f}"])
    S["sens_obj_vs_hotness"] = (sens_r["objplace"] - sens_r["hotness"]) / sens_r["hotness"] * 100

    # summary
    lines = [
        f"T1 emb  objplace vs manual : {S['emb_obj_vs_manual']:+.1f}%  (target ~0)",
        f"T1 gnn  objplace vs manual : {S['gnn_obj_vs_manual']:+.1f}%  (target ~0)",
        f"T2 emb  objplace vs interleave : +{S['emb_obj_vs_il']:.1f}%  (target ~15%)",
        f"   gnn  objplace vs interleave : +{S['gnn_obj_vs_il']:.1f}%",
        f"T3 bwbench recovery objplace vs allcxl (loaded) : +{S['bw_recovery']:.0f}%",
        f"T4 sensbench objplace vs hotness-only : +{S['sens_obj_vs_hotness']:.0f}%",
        f"T5 overhead (=T1 emb objplace vs manual) : {abs(S['emb_obj_vs_manual']):.1f}%",
    ]
    with open(os.path.join(out, "summary.txt"), "w") as f: f.write("\n".join(lines) + "\n")
    print("\n=== SUMMARY ===\n" + "\n".join(lines))
    print(f"\nDONE -> {out}")


if __name__ == "__main__":
    main()
