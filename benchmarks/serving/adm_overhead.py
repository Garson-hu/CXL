#!/usr/bin/env python3
"""Instrumentation overhead of the admission stream (2026-11-10 study, brief section 9): duration of Scheduler.schedule() per engine
step, from the step stream of the base hook (vllmevt/sitecustomize.py records t0 / t1 around the scheduler's own schedule()), for a run
WITHOUT the admission wrappers and a run WITH them (the wrappers of allocate_slots, of the connector poll and of _preempt_request run
inside that interval). Steps are split by what they did (tokens scheduled or not) so that equal work is compared.
usage: adm_overhead.py <dir>:<tag without admission stream> <dir>:<tag with admission stream> [...]"""
import glob, json, sys
def q(v, p): return v[min(len(v) - 1, int(p * len(v)))] if v else float("nan")
rows = []
for spec in sys.argv[1:]:
    d, tag = spec.split(":"); S = []; t_first = None; t_last = None
    for f in glob.glob(f"{d}/{tag}-vllmevt.step.*.jsonl"):
        for l in open(f):
            if '"ev":"step"' in l:
                x = json.loads(l); S.append((x["t1"] - x["t0"], x["tok"], x["run"] + x["wait"] + x["hold"]))
                t_first = x["t0"] if t_first is None else min(t_first, x["t0"]); t_last = x["t1"] if t_last is None else max(t_last, x["t1"])
    adm = bool(glob.glob(f"{d}/{tag}-vllmevt.adm.*.jsonl"))
    for name, sel in (("all steps", lambda s: True), ("steps that scheduled tokens", lambda s: s[1] > 0), ("steps with ≥ 8 requests in the scheduler", lambda s: s[2] >= 8)):
        v = sorted(1e6 * s[0] for s in S if sel(s))
        rows.append((tag, "yes" if adm else "no", name, len(v), sum(v) / max(1, len(v)), q(v, .5), q(v, .95), q(v, .99), sum(v) / 1e6, 100 * sum(v) / 1e6 / (t_last - t_first)))
print("| run | admission stream | steps | n | schedule() mean (µs) | p50 | p95 | p99 | total (s) | share of the run's wall time (%) |"); print("|---|---|---|---|---|---|---|---|---|---|")
for r in rows: print(f"| `{r[0]}` | {r[1]} | {r[2]} | {r[3]} | {r[4]:.0f} | {r[5]:.0f} | {r[6]:.0f} | {r[7]:.0f} | {r[8]:.1f} | {r[9]:.2f} |")
