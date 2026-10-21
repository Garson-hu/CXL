#!/usr/bin/env python3
"""Trace statistics for the bounded ghost history study (2026-10-21): how long a hash must be remembered to recognize its
second touch. For every block's FIRST touch that is followed by a second touch: the gap in seconds and in distinct new
hashes first-touched in between (= the ghost's LRU stack distance in entries, what a ghost of N entries must hold);
the same for every later touch (second -> third, ...). Also the new-hash rate (ghost turnover) and the derived
"ghost residence" of a bounded ghost of N entries (N / new-hash rate), and the share of reused-later blocks whose
second touch falls within a time or entry budget.
usage: kv_ghost_stats.py <trace.jsonl> [--mooncake] [--out stats.json]"""
import json, sys, collections, bisect
mc = "--mooncake" in sys.argv; trace = sys.argv[1]; out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
R = []
for i, l in enumerate(open(trace)):
    r = json.loads(l)
    if mc: R.append((r["timestamp"] / 1000.0, [str(h) for h in r["hash_ids"]], i))
    elif r.get("task", 0) >= 0: R.append((r["t_lookup"], list(r["hashes"]), r.get("task", 0)))
R.sort(key=lambda r: r[0]); half = len(R) // 2
acc = [(t, h, ri) for ri, (t, hs, _) in enumerate(R) for h in hs]
first_idx = {}; new_count = 0; new_pos = {}                                              # hash -> index among new hashes at its first touch
last_t = {}; touches = collections.Counter()
gap_s = collections.defaultdict(list); gap_e = collections.defaultdict(list)             # by touch number: 1 = first -> second, 2 = second -> third, 3 = later
new_times = []
for t, h, ri in acc:
    if h not in last_t:
        new_pos[h] = new_count; new_count += 1; new_times.append(t)
    else:
        k = min(3, touches[h]); gap_s[k].append(t - last_t[h]); gap_e[k].append(new_count - new_pos[h] if k == 1 else new_count - new_pos.get(h, new_count))
    touches[h] += 1; last_t[h] = t
    if touches[h] >= 2: new_pos[h] = new_count                                           # entries first-touched after this touch (for the next gap)
T0, T1 = R[0][0], R[-1][0]; span = T1 - T0
rate_new = new_count / span                                                              # new hashes per second over the whole trace
rate_new_2nd = sum(1 for t in new_times if t >= R[half][0]) / max(1e-9, T1 - R[half][0])
def q(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else None
def cdf(xs, bounds): xs = sorted(xs); return {str(b): round(bisect.bisect_right(xs, b) / max(1, len(xs)), 3) for b in bounds}
res = dict(trace=trace, requests=len(R), accesses=len(acc), unique=new_count, span_s=round(span), new_rate_per_s=round(rate_new, 2), new_rate_2nd_half_per_s=round(rate_new_2nd, 2),
           reused_share_of_new=round(len(gap_s[1]) / max(1, new_count), 3))
for k, name in ((1, "first_to_second"), (2, "second_to_third"), (3, "later")):
    res[name] = dict(n=len(gap_s[k]), gap_s_p50=q(gap_s[k], .5), gap_s_p90=q(gap_s[k], .9), gap_s_p99=q(gap_s[k], .99),
                     gap_entries_p50=q(gap_e[k], .5), gap_entries_p90=q(gap_e[k], .9), gap_entries_p99=q(gap_e[k], .99),
                     cdf_s=cdf(gap_s[k], [15, 30, 60, 120, 300, 600, 1200, 1800, 3600]), cdf_entries=cdf(gap_e[k], [1000, 2000, 4000, 8000, 16000, 32000, 64000, 128000, 256000]))
res["ghost_residence_s_by_entries"] = {str(n): round(n / rate_new, 1) for n in (1000, 2000, 4000, 8000, 16000, 32000, 64000, 128000)}
print(json.dumps(res, indent=1))
if out: json.dump(res, open(out, "w"), indent=1)
