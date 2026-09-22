#!/usr/bin/env python3
"""The real-producer runs (torch_ckpt_producer.py): per checkpoint, how long the training thread was blocked
in async_save (the STAGE window), the victim's slowdown during it and during the persist that follows (the
first 7 s after the stage, and the rest until durable), and the time to durable. Same victim samples as
analyze_policy.py, but the reference is the 15 s BEFORE THE FIRST checkpoint (with the stock path a persist
lasts longer than the period, so the 10 s before a later checkpoint lie inside the previous persist).
Prints one line per run (medians over the last 3 checkpoints) and writes <outdir>/summary-dcp.csv."""
import glob, os, re, statistics as st, sys
out = sys.argv[1]; rows = []
for pf in sorted(glob.glob(f"{out}/*-dcp-*-producer.txt")):
    tag = os.path.basename(pf)[:-len("-producer.txt")]; victim = re.sub(r"\d+$", "", tag.split("-")[0]); pt = open(pf).read()
    wins = [(int(m[1]), int(m[2])) for m in re.findall(r"COPY (\d+) START (\d+) END (\d+)", pt)]
    pers = {int(m[0]): (int(m[1]), int(m[2])) for m in re.findall(r"PERSIST (\d+) START (\d+) END (\d+)", pt)}
    vt = open(f"{out}/{tag}-victim.txt").read()
    if victim == "opt": samples = [(int(m[1]), float(m[0])) for m in re.findall(r"\[STEP\] \d+ ([\d.]+) (\d+)", vt)]
    elif victim == "llama": samples = [(int(m), 1.0) for m in re.findall(r"^TOK (\d+)", vt, flags=re.M)]
    else: samples = [(int(m[0]), float(m[1])) for m in re.findall(r"^T (\d+) ([\d.]+)", vt, flags=re.M)]
    r0 = wins[0][0]; before = [v for t, v in samples if r0 - 15_000_000_000 <= t < r0 - 500_000_000]
    def slow(a, b):
        inside = [v for t, v in samples if a <= t <= b]
        if not inside or not before: return None
        if victim == "opt": return 100 * (st.median(inside) / st.median(before) - 1)
        if victim == "llama": return 100 * (1 - (len(inside) / ((b - a) / 1e9)) / (len(before) / 14.5))
        return 100 * (1 - st.mean(inside) / st.mean(before))
    per = []
    for i, (s0, s1) in enumerate(wins):
        if i not in pers: continue
        p0, p1 = pers[i]
        a = slow(s0, s1 + 150_000_000); b = slow(s1 + 1_000_000_000, min(s1 + 8_000_000_000, p1)); c = slow(s1 + 8_000_000_000, p1) if p1 > s1 + 9_000_000_000 else 0.0
        if a is None or b is None or c is None: continue
        per.append(((s1 - s0) / 1e9, a, b, c, (p1 - s0) / 1e9))
    last = per[-3:] if len(per) >= 3 else per
    if not last: print(f"{tag}: no windows"); continue
    r = dict(tag=tag, victim=victim, n=len(per), blocked_s=st.median(x[0] for x in last), stage_slow=st.median(x[1] for x in last), p7=st.median(x[2] for x in last), prest=st.median(x[3] for x in last), durable_s=st.median(x[4] for x in last),
             per=" ".join(f"{x[1]:.1f}/{x[2]:.1f}/{x[3]:.1f}" for x in per))
    rows.append(r); print(f"{tag:32s} n={len(per)}  blocked {r['blocked_s']:.2f} s  slowdown during stage {r['stage_slow']:5.1f}%  persist first 7 s {r['p7']:4.1f}%  rest {r['prest']:4.1f}%  durable after {r['durable_s']:5.1f} s   per-ckpt: {r['per']}")
with open(f"{out}/summary-dcp.csv", "w") as f:
    f.write("tag,victim,checkpoints,blocked_s,stage_slowdown_pct,persist_first7s_pct,persist_rest_pct,durable_s\n")
    for r in rows: f.write(f"{r['tag']},{r['victim']},{r['n']},{r['blocked_s']:.3f},{r['stage_slow']:.2f},{r['p7']:.2f},{r['prest']:.2f},{r['durable_s']:.2f}\n")
