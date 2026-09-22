#!/usr/bin/env python3
"""Per-step timeline of the Adam victim around one copy/stage window, several runs overlaid (the headline
figure of Observation 2). Each series: <tag> <label> <color>; the window shown is the given period of the run
(0-based), time relative to the window's START; step times relative to the median of the 10 s before it.
usage: plot_timeline.py <dir> <out.png> <period> <title> <tag>:<label>:<color> [...]"""
import re, statistics as st, sys
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
d, out, period, title = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
fig, ax = plt.subplots(figsize=(13, 4.2))
for i, spec in enumerate(sys.argv[5:]):
    tag, label, color = spec.rsplit(":", 2)
    pt = open(f"{d}/{tag}-producer.txt").read()
    wins = [(int(m[1]), int(m[2])) for m in re.findall(r"COPY (\d+) START (\d+) END (\d+)", pt)]
    s0, s1 = wins[period]
    steps = [(int(m[1]), float(m[0])) for m in re.findall(r"\[STEP\] \d+ ([\d.]+) (\d+)", open(f"{d}/{tag}-victim.txt").read())]   # (end ns, seconds)
    base = st.median(v for t, v in steps if s0 - 10_000_000_000 <= t < s0 - 500_000_000)
    xs = [(t - s0) / 1e9 for t, v in steps if s0 - 4e9 <= t <= s0 + 12e9]; ys = [100 * (v / base - 1) for t, v in steps if s0 - 4e9 <= t <= s0 + 12e9]
    pers = [(int(m[1]), int(m[2])) for m in re.findall(r"PERSIST (\d+) START (\d+) END (\d+)", pt)]
    dur = f", durable after {(pers[period][1] - s0) / 1e9:.0f} s" if len(pers) > period else ""
    ax.plot(xs, ys, color=color, lw=1.6, label=f"{label}  (training thread blocked {(s1 - s0) / 1e9:.2f} s{dur})")
    ax.axvspan(0, (s1 - s0) / 1e9, color=color, alpha=0.10)
ax.axhline(0, color="k", lw=0.8); ax.set_xlabel("time relative to the start of async_save, s"); ax.set_ylabel("Adam step time vs. no checkpoint, %")
ax.set_title(title, fontsize=9); ax.grid(alpha=0.3); ax.legend(loc="upper right", fontsize=9); fig.tight_layout(); fig.savefig(out, dpi=130); print("wrote", out)
