#!/usr/bin/env python3
"""Configuration matrix of the 2026-11-10 GPU-KV admission study: one row per run found under the given results directories (every
<tag>-meta.txt), with the node, the start time, the configuration recorded by serving_env (model, host tier, GPU KV pool, scheduler
options, KVADM_POLICY flags), the workload (trace window and speed from the replay mark, or the driver's scenario / trial marks), the
number of measured requests and their errors (non-200 / exceptions), the errors of filler requests (warm-up, populate, the flushes
between scenarios; holders are cancelled by the driver and not counted) and the completion status. Writes <out>/experiment-matrix.csv
and .md.
usage: matrix_adm.py <out dir> <family>=<results dir> [<family>=<results dir> ...]"""
import csv, datetime, glob, json, os, re, sys
OUT = sys.argv[1]; rows = []
for spec in sys.argv[2:]:
    fam, R = spec.split("=", 1)
    for meta in sorted(glob.glob(f"{R}/**/*-meta.txt", recursive=True)):
        d = os.path.dirname(meta); tag = os.path.basename(meta)[: -len("-meta.txt")]; sub = os.path.relpath(d, R)
        cfg = {}; marks = []; done = False; wl = ""; t_wall = None; ntr = 0
        for l in open(meta):
            if not l.startswith("M "): continue
            name = l.split()[1]; marks.append(name)
            if name == "config":
                try: cfg = json.loads(l[l.index("{"):])
                except Exception: cfg = {}
                m = re.search(r"wall=([\d.]+)", l); t_wall = float(m.group(1)) if m else None
            elif name == "replay_start":
                m = re.search(r"trace=(\S+) t0=(\S+) t1=(\S+) speed=(\S+) n=(\d+)", l)
                if m: wl = f"{m.group(1).replace('mooncake_', '').replace('_trace.jsonl', '')} {float(m.group(2)):g}-{float(m.group(3)):g} s at {m.group(4)}x ({m.group(5)} requests)"
            elif name == "trial": ntr += 1
            if name in ("bench_end", "replay_end"): done = True
        if not wl:
            sc = sorted({m for m in marks if re.fullmatch(r"s\d", m)})
            wl = (f"run_adm.py, {ntr} trials" if ntr else ("run_b.py " + "+".join(sc) if sc else "?"))
        node = "c28"; np_ = f"{d}/{tag}-node.txt"
        if os.path.exists(np_):
            m = re.match(r"# \S+ (\S+)", open(np_).readline()); node = m.group(1) if m else "?"
        n = 0; err = 0; ferr = 0
        cp = f"{d}/{tag}-client.jsonl"
        if os.path.exists(cp):
            for l in open(cp):
                try: r = json.loads(l)
                except Exception: continue
                if r.get("case") == "holder": continue
                bad = r.get("status") != 200 or bool(r.get("error"))
                if r.get("case") in ("warm", "populate", "flush", "gpuwarm"): ferr += bad
                else: n += 1; err += bad
        pool = ""
        for f in glob.glob(f"{d}/{tag}-vllmevt.adm.*.jsonl"):
            for l in open(f):
                if '"ev":"kv"' in l: pool = json.loads(l)["tot"]; break
        pol = (cfg.get("adm_env") or "").replace("KVADM_POLICY=", "")
        rows.append(dict(family=fam + ("" if sub == "." else "/" + sub), tag=tag, node=node, start=datetime.datetime.fromtimestamp(t_wall).strftime("%Y-%m-%d %H:%M") if t_wall else "",
                         model=(cfg.get("model") or "").split("/")[-1], host_tier_GB=cfg.get("l1_gb"), gpu_kv_blocks=pool, pool_pinned="yes" if cfg.get("gpu_blocks") else "no",
                         async_sched=cfg.get("async_sched") or "on", max_batched=cfg.get("max_batched") or 2048, long_prefill_threshold=cfg.get("long_prefill_threshold") or 0,
                         sched_policy=cfg.get("sched_policy"), extra_vllm=cfg.get("extra_vllm") or "", kvadm_policy=pol or "(stock)", workload=wl, requests=n, errors=err, filler_errors=ferr, completed="yes" if done else "NO"))
keys = list(rows[0].keys()) if rows else []
with open(f"{OUT}/experiment-matrix.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); [w.writerow(r) for r in rows]
with open(f"{OUT}/experiment-matrix.md", "w") as f:
    f.write("| " + " | ".join(keys) + " |\n|" + "---|" * len(keys) + "\n")
    for r in rows: f.write("| " + " | ".join(str(r[k]) for k in keys) + " |\n")
print(f"{len(rows)} runs; with errors in measured requests: {[(r['tag'], r['errors']) for r in rows if r['errors']]}; filler errors: {[(r['tag'], r['filler_errors']) for r in rows if r['filler_errors']]}; not completed: {[r['tag'] for r in rows if r['completed'] != 'yes']}")
