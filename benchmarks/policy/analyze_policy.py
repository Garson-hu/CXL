#!/usr/bin/env python3
"""For every run in <outdir>: per copy window, the victim's slowdown (median step time inside the window vs
the 10 s before it; for the reader, mean GiB/s inside vs before) and the copy's completion time.
Prints one line per run (median over the LAST 3 windows) and writes <outdir>/summary.csv."""
import glob, os, re, statistics as st, sys
out = sys.argv[1]; rows = []
for pf in sorted(glob.glob(f"{out}/*-producer.txt")):
    tag = os.path.basename(pf)[:-len("-producer.txt")]; victim = re.sub(r"\d+$", "", tag.split("-")[0])   # "llama32" -> "llama"
    wins = [(int(m[1]), int(m[2]), float(m[3]), float(m[4])) for m in re.findall(r"COPY (\d+) START (\d+) END (\d+) bytes=\d+ GiBs=([\d.]+) dram_share=([\d.]+)", open(pf).read())]
    vt = open(f"{out}/{tag}-victim.txt").read()
    fully_inside = victim == "pr"                        # PageRank trials are ~1 s: count only trials that START and END inside the window
    if victim in ("opt", "pr"): samples = [(int(m[1]), float(m[0])) for m in re.findall(r"\[STEP\] \d+ ([\d.]+) (\d+)", vt)]   # (end ns, step s)
    elif victim == "llama": samples = [(int(m), 1.0) for m in re.findall(r"^TOK (\d+)", vt, flags=re.M)]                       # one token per line: rate = count / time
    else: samples = [(int(m[0]), float(m[1])) for m in re.findall(r"^T (\d+) ([\d.]+)", vt, flags=re.M)]                     # (ns, GiB/s)
    per = []
    for s0, s1, gibs, share in wins:
        if fully_inside: inside = [v for t, v in samples if s0 <= t - int(v * 1e9) and t <= s1 + 150_000_000]
        else: inside = [v for t, v in samples if s0 <= t <= s1 + 150_000_000]
        before = [v for t, v in samples if s0 - 10_000_000_000 <= t < s0 - 500_000_000]
        if not inside or not before: continue
        if victim in ("opt", "pr"): slow = 100 * (st.median(inside) / st.median(before) - 1)
        elif victim == "llama": slow = 100 * (1 - (len(inside) / ((s1 + 150_000_000 - s0) / 1e9)) / (len(before) / 9.5))     # tok/s inside vs before
        else: slow = 100 * (1 - st.mean(inside) / st.mean(before))
        per.append((slow, (s1 - s0) / 1e9, gibs, share))
    last = per[-3:] if len(per) >= 3 else per
    if not last: print(f"{tag}: no windows"); continue
    r = dict(tag=tag, victim=victim, windows=len(per), slowdown=st.median(x[0] for x in last), completion_s=st.median(x[1] for x in last), copy_GiBs=st.median(x[2] for x in last), dram_share=st.median(x[3] for x in last),
             slow_all=" ".join(f"{x[0]:.1f}" for x in per))
    rows.append(r); print(f"{tag:34s} windows={len(per)}  slowdown {r['slowdown']:6.1f}%  completion {r['completion_s']:5.2f} s ({r['copy_GiBs']:5.1f} GiB/s)  dram_share {r['dram_share']:.2f}   per-window: {r['slow_all']}")
with open(f"{out}/summary.csv", "w") as f:
    f.write("tag,victim,windows,slowdown_pct,completion_s,copy_GiBs,dram_share\n")
    for r in rows: f.write(f"{r['tag']},{r['victim']},{r['windows']},{r['slowdown']:.2f},{r['completion_s']:.3f},{r['copy_GiBs']:.2f},{r['dram_share']:.3f}\n")
