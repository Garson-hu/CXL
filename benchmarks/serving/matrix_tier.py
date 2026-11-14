#!/usr/bin/env python3
"""Experiment matrix of the 2026-11-12 CXL-vs-NVMe serving study: one row per run found under the results directory (every
<tag>-meta.txt), with the phase (sub-directory), the start time, the configuration recorded by serving_env (host tier, DRAM for KV,
extension medium and size, L2 policy, GPU KV pool), the workload (trace window and time scale from the replay mark, or the driver's
marks), the number of measured requests, their errors (non-200 / exceptions) and those that were answered with status 200 but
without an output token (a stream that was open when the engine died keeps its 200), the errors of filler requests (warm-up,
populate, fill and flush requests), settings that differ from the study's common ones (LMCache read-lock TTL, vLLM
kv_load_failure_policy), whether the driver reached its end mark, the exit code the queue recorded, and whether the run is used as
a result (runs under void/ and the superseded smoke runs are not). Writes <results>/experiment-matrix.csv and .md.
usage: matrix_tier.py <results dir>"""
import csv, datetime, glob, json, os, re, sys
R = sys.argv[1]; rows = []
rc = {}
for f, pat in ((f"{R}/done.txt", r"end (\S+) rc=(\d+)"), (f"{R}/queue_p0a.log", r"\] (\S+) rc=(\d+)")):
    if os.path.exists(f):
        for l in open(f):
            m = re.search(pat, l)
            if m: rc[m.group(1)] = int(m.group(2))
FILL = ("warm", "populate", "flush", "gpuwarm", "fill_store")
EXT = {"dram": "-", "none": "-", "dax": "CXL Device-DAX as L1 (no DRAM)", "hyb": "CXL Device-DAX, hybrid L1", "daxl2": "CXL Device-DAX, L2 adapter",
       "ssdn": "NVMe, fs_native L2", "ssd": "NVMe, Python fs L2"}
for meta in sorted(glob.glob(f"{R}/**/*-meta.txt", recursive=True)):
    d = os.path.dirname(meta); tag = os.path.basename(meta)[: -len("-meta.txt")]; sub = os.path.relpath(d, R)
    cfg = {}; marks = []; done = False; wl = ""; t_wall = None; t_end = None; pol = ""
    for l in open(meta):
        if not l.startswith("M "): continue
        name = l.split()[1]; marks.append(name); m = re.search(r"wall=([\d.]+)", l)
        if name == "config":
            try: cfg = json.loads(l[l.index("{"):])
            except Exception: cfg = {}
            t_wall = float(m.group(1)) if m else None
        elif name == "lmcache_cmd":
            try:
                cmd = json.loads(l[l.index("["):]); pol = cmd[cmd.index("--l2-store-policy") + 1] if "--l2-store-policy" in cmd else ""
            except Exception: pol = ""
        elif name == "replay_start":
            m2 = re.search(r"trace=(\S+) t0=(\S+) t1=(\S+) speed=(\S+) n=(\d+)", l)
            if m2: wl = f"{m2.group(1).replace('mooncake_', '').replace('_trace.jsonl', '')} trace {float(m2.group(2)):g}-{float(m2.group(3)):g} s at {m2.group(4)}x"
        if name in ("bench_end", "replay_end"): done = True
        if name == "stopped" and m: t_end = float(m.group(1))
    if not wl:
        if "pass_start" in marks: wl = f"equal-hit comparison (run_eqhit.py), {marks.count('pass_start')} passes"
        elif "e1" in marks: wl = f"concurrent retrieval (run_e.py e1), {marks.count('e1')} points"
        elif "case" in marks: wl = f"single-request retrieval (run_a.py), {marks.count('case')} cases"
        elif sub.startswith("env"): wl = "start and stop only (GPU memory of the configuration)"
        else: wl = "?"
    n = 0; err = 0; fn = 0; ferr = 0; noout = 0; cp = f"{d}/{tag}-client.jsonl"
    if os.path.exists(cp):
        for l in open(cp):
            try: r = json.loads(l)
            except Exception: continue
            bad = r.get("status") != 200 or bool(r.get("error"))
            if r.get("case") in FILL: fn += 1; ferr += bad
            else: n += 1; err += bad; noout += (not bad) and not (r.get("out_tokens") or 0)
    tier = cfg.get("tier") or "?"; ext = EXT.get(tier, tier); size = ""
    if tier in ("hyb", "daxl2", "dax"):
        devs = cfg.get("dax_devs") or ""; size = " + ".join(f"{x.split(':')[0].replace('/dev/', '')} {x.split(':')[1]} GiB" for x in devs.split(",") if ":" in x) or (cfg.get("dax_path") or "")
    elif tier in ("ssdn", "ssd"):
        size = f"{cfg.get('l2_gb'):g} GiB limit" if tier == "ssdn" and cfg.get("l2_gb") else "no limit"
        size += ", O_DIRECT" if cfg.get("ssd_odirect") else ", BUFFERED (control)"
    if sub.startswith("env") and "pass_start" in marks: wl = "stress: 16 concurrent 16K requests (GPU memory fit of the full hybrid)"
    used = "void" if sub.startswith("void") else "GPU-memory record" if sub.startswith("env") else ("superseded smoke run" if re.fullmatch(r"p0-.*-s", tag) else ("functional check" if sub in ("B0",) else "result"))
    rows.append(dict(phase=sub, tag=tag, start=datetime.datetime.fromtimestamp(t_wall).strftime("%Y-%m-%d %H:%M") if t_wall else "",
                     minutes=f"{(t_end - t_wall) / 60:.0f}" if t_wall and t_end else "", tier=tier, dram_for_kv_GiB=("-" if tier in ("none", "dax") else cfg.get("l1_gb")),
                     extension=ext, extension_size=size, l2_policy=({"default": "write-through", "": "-"}.get(pol, pol) if tier in ("daxl2", "ssdn", "ssd") else "-"),
                     cuda_registered_dax=("-" if tier not in ("hyb", "dax") else ("no" if "no-pin" in (cfg.get("extra_lm") or "") or "nopin" in tag else "yes")),
                     gpu_kv_blocks=cfg.get("gpu_blocks") or "(default)", store_fix=("-" if tier == "none" else "yes" if "storefix" in (cfg.get("adm_env") or "") else "NO"),
                     workload=wl, other_settings=("; ".join(x for x in ((f"read-lock TTL {cfg.get('read_ttl')} s" if cfg.get("read_ttl") else ""), (f"kv_load_failure_policy={cfg.get('kv_fail')}" if cfg.get("kv_fail") else "")) if x) or "-"),
                     requests=n, errors=err, status_200_without_output=noout, filler_requests=fn, filler_errors=ferr, driver_finished=("yes" if done else "-" if sub.startswith("env") else "NO"), exit_code=("" if sub.startswith(("void", "env")) else rc.get(tag, "")), used_as=used))
keys = list(rows[0].keys()) if rows else []
with open(f"{R}/experiment-matrix.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); [w.writerow(r) for r in rows]
with open(f"{R}/experiment-matrix.md", "w") as f:
    f.write(f"# Experiment matrix — every run of the 2026-11-12 CXL-vs-NVMe serving study ({len(rows)} runs; written by `benchmarks/serving/matrix_tier.py`)\n\n")
    f.write("| " + " | ".join(keys) + " |\n|" + "---|" * len(keys) + "\n")
    for r in rows: f.write("| " + " | ".join(str(r[k]) for k in keys) + " |\n")
print(f"{len(rows)} runs; errors in measured requests: {[(r['tag'], r['errors']) for r in rows if r['errors']]}; status 200 without output: {[(r['tag'], r['status_200_without_output']) for r in rows if r['status_200_without_output']]}; filler errors: {[(r['tag'], r['filler_errors']) for r in rows if r['filler_errors']]}; "
      f"driver not finished: {[r['phase'] + '/' + r['tag'] for r in rows if r['driver_finished'] == 'NO']}; by use: " + ", ".join(f"{u} {sum(1 for r in rows if r['used_as'] == u)}" for u in sorted({r['used_as'] for r in rows})))
