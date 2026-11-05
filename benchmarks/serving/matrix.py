#!/usr/bin/env python3
"""Experiment matrix of the 2026-11-04 serving study: one row per run found under the results directory (every
<tag>-meta.txt), with the configuration recorded by serving_env (model, tier, L1, transfer threads, eager prefetch,
scheduling policy, chunk, async, hooks / samplers), the workload (experiment family from the directory, scenario list
from the meta marks or the driver), the number of requests, errors (non-200 / exceptions) and the completion status
(bench_end mark present, rc from the chain log). Writes <results dir>/experiment-matrix.csv and .md.
usage: matrix.py <results dir>"""
import csv, glob, json, os, re, sys
R = sys.argv[1]; rows = []
rc = {}
for ch in glob.glob(f"{R}/**/chain.txt", recursive=True) + [f"{R}/queue.txt"]:
    if not os.path.exists(ch): continue
    for l in open(ch):
        m = re.search(r"\] (?:end )?([a-z0-9][\w\-\.]*) rc=(\d+)", l)
        if m: rc[m.group(1)] = int(m.group(2))
for meta in sorted(glob.glob(f"{R}/**/*-meta.txt", recursive=True)):
    d = os.path.dirname(meta); tag = os.path.basename(meta)[: -len("-meta.txt")]; fam = os.path.relpath(d, R)
    cfg = {}; marks = []; done = False; stopped = False
    for l in open(meta):
        if l.startswith("M config "):
            js = l[l.index("{"):].strip() if "{" in l else ""
            try: cfg = json.loads(js)
            except Exception: cfg = {"raw": js[:100]}
        elif l.startswith("M "):
            name = l.split()[1]; marks.append(name)
            if name == "bench_end" or name == "replay_end": done = True
            if name == "stopped": stopped = True
    n = 0; err = 0; cases = {}
    cp = f"{d}/{tag}-client.jsonl"
    if os.path.exists(cp):
        for l in open(cp):
            try: r = json.loads(l)
            except Exception: continue
            n += 1; cases[r.get("case", "")] = cases.get(r.get("case", ""), 0) + 1
            if r.get("status") != 200 or r.get("error"): err += 1
    scen = sorted({m for m in marks if m in ("s0", "s1", "s2", "s3", "s4", "e1", "e2", "e3", "case", "replay_start")})
    extra = ""
    drv = f"{d}/{tag}-driver.txt"
    if os.path.exists(drv):
        t = open(drv, errors="replace").read()
        if "Traceback" in t: extra = "driver exception"
    rows.append(dict(family=fam, tag=tag, model=cfg.get("model", "").split("/")[-1], tier=cfg.get("tier"), l1_gb=cfg.get("l1_gb"), gpu_workers=cfg.get("gpu_workers"), eager_prefetch=cfg.get("eager_prefetch"),
                     sched_policy=cfg.get("sched_policy"), max_batched=cfg.get("max_batched") or "default(2048)", async_sched=cfg.get("async_sched") or "default(on)", enforce_eager=cfg.get("enforce_eager"),
                     gpu_blocks=cfg.get("gpu_blocks") or "all", hooks=cfg.get("hooks"), samplers=cfg.get("samplers"), scenarios="+".join(scen), n_requests=n, n_cases=";".join(f"{k}:{v}" for k, v in sorted(cases.items())),
                     n_errors=err, completed=done, servers_stopped=stopped, rc=rc.get(tag, ""), note=extra))
keys = list(rows[0].keys()) if rows else []
with open(f"{R}/experiment-matrix.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); [w.writerow(r) for r in rows]
with open(f"{R}/experiment-matrix.md", "w") as f:
    f.write("| " + " | ".join(keys) + " |\n|" + "---|" * len(keys) + "\n")
    for r in rows: f.write("| " + " | ".join(str(r[k]) for k in keys) + " |\n")
print(f"{len(rows)} runs; errors in {sum(1 for r in rows if r['n_errors'])} runs; not completed: {[r['tag'] for r in rows if not r['completed']]}")
