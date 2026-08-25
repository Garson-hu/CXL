#!/usr/bin/env python3
"""
phase22.py — Phase 2.2 targeted retest (no full matrix).

Part A: are bandwidth-hungry MULTI-THREADED victims hurt > 1.5x by a CXL
        streaming aggressor? (Phase 2.1 only tested 1-thread victims.)
  victims: stream-read, random-read (membench)
  victim threads: 1, 2, 4, 8     (cores 0..N-1, --cpu-offset=0)
  aggressor: stream-read
  aggressor threads: 0, 1, 2, 4, 8   (cores 64.., --cpu-offset=64, disjoint)
  nodes: 0 (DRAM), 1 (CXL)

Part B: Direction C probe — does skew-aware split ever beat interleave by >=15%?
  embedding only, Zipf alpha {0.8,1.0,1.2,1.5} x hot-frac {1,5,10,20}%
  policies: cxl, interleave, skew  (solo, no aggressor — intrinsic placement)

Output: benchmarks/results/<TS>-phase22/{partA.csv, partB.csv, summary.txt}
"""
import csv, os, subprocess, sys, time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMBENCH = os.path.join(ROOT, "benchmarks", "memory", "membench")
EMBBENCH = os.path.join(ROOT, "benchmarks", "embedding", "embbench.py")
AGG_OFFSET = 64
DUR = 3.0
ENV1 = {**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"}


def mb_csv(text):
    row = [r for r in text.strip().splitlines() if r and not r.startswith("tag")][-1]
    p = row.split(",")
    return {"bw": float(p[8]), "total_bw": float(p[12])}


def run_victim(mode, node, threads):
    cmd = [MEMBENCH, f"--mode={mode}", f"--node={node}", f"--threads={threads}",
           "--size=256M", f"--duration={DUR}", "--cpu-offset=0", "--csv", "--tag=v"]
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        sys.stderr.write(out.stderr); raise RuntimeError("victim failed")
    return mb_csv(out.stdout)["total_bw"]


def start_agg(node, threads, seconds):
    cmd = [MEMBENCH, "--mode=stream-read", f"--node={node}", f"--threads={threads}",
           "--size=256M", f"--duration={seconds}", f"--cpu-offset={AGG_OFFSET}",
           "--csv", "--tag=a"]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            text=True)


def finish_agg(p):
    out, _ = p.communicate()
    try:
        return mb_csv(out)["total_bw"]
    except Exception:
        return 0.0


def part_a(outdir):
    path = os.path.join(outdir, "partA.csv")
    print("\n===== PART A: multi-threaded bandwidth-hungry victims =====")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["node", "victim", "victim_threads", "agg_threads",
                    "victim_bw_gib_s", "baseline_bw_gib_s", "slowdown",
                    "aggressor_bw_gib_s", "total_cxl_bw_gib_s", "exceeds_1.5x"])
        for node in (0, 1):
            for vmode in ("stream-read", "random-read"):
                for vth in (1, 2, 4, 8):
                    base = run_victim(vmode, node, vth)
                    for ath in (0, 1, 2, 4, 8):
                        if ath == 0:
                            vbw, abw = base, 0.0
                        else:
                            p = start_agg(node, ath, DUR + 3.0)
                            time.sleep(1.0)
                            vbw = run_victim(vmode, node, vth)
                            abw = finish_agg(p)
                        sd = base / vbw if vbw > 0 else float("nan")
                        total = vbw + abw
                        w.writerow([node, vmode, vth, ath, f"{vbw:.3f}",
                                    f"{base:.3f}", f"{sd:.3f}", f"{abw:.3f}",
                                    f"{total:.3f}", "yes" if sd > 1.5 else "no"])
                        if ath == 8:
                            print(f"[node {node}] {vmode:<12} vth={vth} "
                                  f"agg8: slowdown={sd:.2f}x "
                                  f"victim_bw={vbw:.1f} agg_bw={abw:.1f} "
                                  f"total={total:.1f} GiB/s")
    return path


def emb(place, alpha, hotfrac, reps=2):
    vals = []
    for _ in range(reps):
        cmd = ["taskset", "-c", "0-15", "python3", EMBBENCH,
               "--rows=2000000", "--row-dim=2048", "--batch=8192", "--steps=30",
               "--dist=zipf", f"--zipf-s={alpha}", f"--place={place}",
               f"--hot-frac={hotfrac}", "--csv", "--tag=r"]
        out = subprocess.run(cmd, capture_output=True, text=True, env=ENV1)
        if out.returncode != 0:
            sys.stderr.write(out.stderr); raise RuntimeError("emb failed")
        row = [r for r in out.stdout.strip().splitlines() if not r.startswith("tag")][-1]
        vals.append(float(row.split(",")[9]))   # per_step_ms
    vals.sort()
    return vals[len(vals)//2]


def part_b(outdir):
    path = os.path.join(outdir, "partB.csv")
    print("\n===== PART B: Direction C embedding probe (solo) =====")
    best = {"impr": -1e9}
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["alpha", "hot_frac", "cxl_ms", "interleave_ms", "skew_ms",
                    "skew_vs_interleave_pct", "skew_vs_cxl_pct"])
        for alpha in (0.8, 1.0, 1.2, 1.5):
            for hf in (0.01, 0.05, 0.10, 0.20):
                cxl = emb("cxl", alpha, hf)
                il = emb("interleave", alpha, hf)
                sk = emb("skew", alpha, hf)
                impr_il = (il - sk) / il * 100.0
                impr_cxl = (cxl - sk) / cxl * 100.0
                w.writerow([alpha, hf, f"{cxl:.3f}", f"{il:.3f}", f"{sk:.3f}",
                            f"{impr_il:.1f}", f"{impr_cxl:.1f}"])
                print(f"  alpha={alpha} hot={hf:.0%}  cxl={cxl:.1f} il={il:.1f} "
                      f"skew={sk:.1f}  skew/il={impr_il:+.1f}%  skew/cxl={impr_cxl:+.1f}%")
                if impr_il > best["impr"]:
                    best = {"impr": impr_il, "alpha": alpha, "hf": hf,
                            "il": il, "sk": sk}
    return path, best


def main():
    ts = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outdir = os.path.join(ROOT, "benchmarks", "results", f"{ts}-phase22")
    os.makedirs(outdir, exist_ok=True)
    print(f"writing to {outdir}")
    part_a(outdir)
    _, best = part_b(outdir)
    with open(os.path.join(outdir, "summary.txt"), "w") as f:
        f.write(f"Part B best skew-vs-interleave: {best['impr']:+.1f}% "
                f"at alpha={best.get('alpha')} hot_frac={best.get('hf')}\n")
        f.write(f"any setting >= 15%: {best['impr'] >= 15}\n")
    print(f"\nBest skew-vs-interleave: {best['impr']:+.1f}% "
          f"(alpha={best.get('alpha')}, hot={best.get('hf')})")
    print(f"DONE -> {outdir}")


if __name__ == "__main__":
    main()
