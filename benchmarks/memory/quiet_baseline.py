#!/usr/bin/env python3
"""Quiet-baseline stability (2026-10-12, budget-gated admission experiment): run one neighbour ALONE for <record_s> after
the same 25 s settle as run_exp2b.py, then report its median and p99 in consecutive 60 s and 120 s windows, so the
spread of the quiet p99 across windows can be compared with the 7% slowdown target. Neighbours: opt (80-thread Adam
step, cpus 0-79; p99 of step time) and reader (8 streaming readers, cpus 0-7, 64 MiB progress; p99 of the time per GiB
in 100 ms samples, i.e. the 1% slowest samples). Files: <out>/<neighbor>-quiet.txt (raw), <out>/quiet-summary.txt.
usage: quiet_baseline.py <out_dir> [record_s=600]"""
import os, re, signal, statistics as st, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__)); POL = os.path.join(HERE, "..", "policy"); BUDGET = os.path.join(HERE, "..", "budget")
out = sys.argv[1]; rec = float(sys.argv[2]) if len(sys.argv) > 2 else 600; os.makedirs(out, exist_ok=True)
q = lambda xs, p: sorted(xs)[min(len(xs) - 1, int(p * len(xs)))]
summ = open(f"{out}/quiet-summary.txt", "w")
def say(s=""): print(s, flush=True); summ.write(s + "\n"); summ.flush()
for nbn in ("opt", "reader"):
    f = open(f"{out}/{nbn}-quiet.txt", "w")
    if nbn == "opt":
        env = dict(os.environ, OMP_NUM_THREADS="80", OMP_PROC_BIND="close", OMP_PLACES="{0}:80:1")
        p = subprocess.Popen(["taskset", "-c", "0-79", "python3", f"{BUDGET}/opt_step.py", "80", "1500", "100000"], stdout=f, stderr=subprocess.STDOUT, env=env)
    else:
        p = subprocess.Popen([f"{POL}/reader_victim", "8", "0", "64"], stdout=f, stderr=subprocess.STDOUT)
    time.sleep(25); t0 = time.monotonic_ns(); time.sleep(rec); t1 = time.monotonic_ns()
    p.send_signal(signal.SIGTERM); p.wait(); f.close()
    txt = open(f"{out}/{nbn}-quiet.txt").read()
    if nbn == "opt": s = [(int(t), float(v)) for v, t in re.findall(r"\[STEP\] \d+ ([\d.]+) (\d+)", txt)]
    else: s = [(int(t), 1.0 / float(v)) for t, v in re.findall(r"^T (\d+) ([\d.]+)$", txt, re.M) if float(v) > 0]   # seconds per GiB
    s = [(t, v) for t, v in s if t0 <= t < t1]
    say(f"## {nbn} alone, {rec:.0f} s, {len(s)} samples; whole: median {st.median(v for _, v in s):.5f} p99 {q([v for _, v in s], .99):.5f} (p99/median {q([v for _, v in s], .99) / st.median(v for _, v in s):.3f})")
    for w in (60, 120):
        rows = []
        for k in range(int(rec // w)):
            v = [x for t, x in s if t0 + k * w * 1e9 <= t < t0 + (k + 1) * w * 1e9]
            if v: rows.append((st.median(v), q(v, .99), len(v)))
        m0, p0 = st.median(r[0] for r in rows), st.median(r[1] for r in rows)
        say(f"  {w} s windows: median {' '.join(f'{r[0] / m0:.3f}' for r in rows)} | p99 {' '.join(f'{r[1] / p0:.3f}' for r in rows)} (each / its median over windows; "
            f"{rows[0][2]} samples per window) -> p99 spread {100 * (max(r[1] for r in rows) / min(r[1] for r in rows) - 1):.1f}%, median spread {100 * (max(r[0] for r in rows) / min(r[0] for r in rows) - 1):.1f}%")
summ.close()
