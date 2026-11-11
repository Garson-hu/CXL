#!/usr/bin/env python3
"""Correctness record of instrumented serving runs (2026-11-10 admission study, brief section 9). For every run:
  completion      requests sent / HTTP 200 / errors, output tokens generated (ignore_eos: must equal the reference run's)
  outputs         generated text identical to the reference run's, request by request (sha1 of the text, temperature 0);
                  split into requests served the same way in both runs (same tier: host / gpu / cold / part) and requests
                  served differently (e.g. loaded from LMCache in one run and computed in the other: a direct check that
                  loaded KV blocks are valid)
  loads           requests with more than one LMCache retrieve (repeated loads), retrieves in total
  preemption      Scheduler._preempt_request calls, running requests refused their next chunk
  block pool      engine steps at which no request holds blocks (nothing running, loading or holding KV in the waiting
                  queue) and the last step with a holder ended >= 50 ms earlier: free blocks must equal pool - 1 (the
                  null block). The 50 ms skip the two steps right after a request finishes, in which vLLM still holds
                  its blocks until the worker reports the LMCache store done (delayed free). Also min / max free.
  stores          requests with a store, bytes stored
Reads <out>/<tag>-client.jsonl, <out>/<tag>-requests.csv (analyze_b.py; optional) and <out>/<tag>-vllmevt.adm.*.jsonl.
usage: check_runs.py <out> <reference tag> <tag> [<tag> ...] [cases=trace|host,cold|all]     (the reference is listed first)"""
import csv, glob, json, os, sys
args = [a for a in sys.argv[1:] if "=" not in a]; kv = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
out, tags = args[0], args[1:]; CASES = kv.get("cases", "trace")
def keep(c): return CASES == "all" or c in CASES.split(",")
def load(tag):
    cl = {}
    for l in open(f"{out}/{tag}-client.jsonl"):
        r = json.loads(l)
        if keep(r.get("case") or ""): cl[r["rid"][len(tag) + 1:]] = r
    tier = {}; rq = {}
    p = f"{out}/{tag}-requests.csv"
    if os.path.exists(p):
        for r in csv.DictReader(open(p)):
            if r["rid"].startswith(tag + "-"): rq[r["rid"][len(tag) + 1:]] = r; tier[r["rid"][len(tag) + 1:]] = r.get("tier")
    pre = runfail = 0; idle = idle_ok = 0; fmin = None; fmax = None; tot = None; last_busy = None
    for f in glob.glob(f"{out}/{tag}-vllmevt.adm.*.jsonl"):
        for l in open(f):
            if '"ev":"kv"' in l:
                d = json.loads(l); tot = d["tot"]; f0 = d["free0"]
                fmin = f0 if fmin is None else min(fmin, f0); fmax = f0 if fmax is None else max(fmax, f0, d["free1"])
                if d["run"] or d["wfr"] or d["hold"]: last_busy = d["t1"]
                elif last_busy is None or d["t0"] - last_busy >= 0.05: idle += 1; idle_ok += f0 == d["tot"] - 1
            elif '"ev":"preempt"' in l: pre += 1
            elif '"ev":"runfail"' in l: runfail += 1
    return dict(cl=cl, tier=tier, rq=rq, pre=pre, runfail=runfail, idle=idle, idle_ok=idle_ok, fmin=fmin, fmax=fmax, tot=tot)
R = {t: load(t) for t in tags}; ref = R[tags[0]]
def ok(r): return r["status"] == 200 and not r.get("error")
rows = [("requests sent", lambda t, d: len(d["cl"])), ("HTTP 200 without error", lambda t, d: sum(ok(r) for r in d["cl"].values())),
        ("output tokens generated", lambda t, d: sum(r.get("out_tokens") or 0 for r in d["cl"].values() if ok(r)))]
def same(t, d, mode):
    ks = [k for k in d["cl"] if k in ref["cl"] and ok(d["cl"][k]) and ok(ref["cl"][k]) and d["cl"][k].get("out_sha") and ref["cl"][k].get("out_sha")]
    if mode == "same": ks = [k for k in ks if d["tier"].get(k) and d["tier"].get(k) == ref["tier"].get(k)]
    if mode == "diff": ks = [k for k in ks if d["tier"].get(k) and ref["tier"].get(k) and d["tier"].get(k) != ref["tier"].get(k)]
    if mode == "h2c": ks = [k for k in ks if {d["tier"].get(k), ref["tier"].get(k)} in ({"host", "cold"}, {"host", "part"}, {"host", "gpu"})]
    if t == tags[0] or not ks: return "–"
    n = sum(d["cl"][k]["out_sha"] == ref["cl"][k]["out_sha"] for k in ks); return f"{n} / {len(ks)} ({100 * n / len(ks):.1f} %)"
rows += [("text identical to the reference, all requests", lambda t, d: same(t, d, "all")), ("… served the same way in both runs", lambda t, d: same(t, d, "same")),
         ("… served differently (tier differs)", lambda t, d: same(t, d, "diff")), ("… loaded from LMCache in one run only", lambda t, d: same(t, d, "h2c"))]
def nret(d, f):
    v = [int(float(r["n_retrieves"] or 0)) for r in d["rq"].values()] if d["rq"] else None
    return "–" if v is None else f(v)
rows += [("LMCache retrieves (requests with one)", lambda t, d: nret(d, lambda v: f"{sum(v)} ({sum(1 for x in v if x)})")),
         ("requests with more than one retrieve", lambda t, d: nret(d, lambda v: sum(1 for x in v if x > 1))),
         ("preemptions", lambda t, d: d["pre"]), ("running requests refused their next chunk", lambda t, d: d["runfail"]),
         ("GPU KV pool (blocks)", lambda t, d: d["tot"]), ("free blocks, min / max over the run", lambda t, d: f"{d['fmin']} / {d['fmax']}"),
         ("steps with no block holder (≥ 50 ms after the last one): free = pool − 1", lambda t, d: f"{d['idle_ok']} / {d['idle']}"),
         ("requests with a store", lambda t, d: "–" if not d["rq"] else sum(1 for r in d["rq"].values() if float(r["n_stores"] or 0) > 0)),
         ("bytes stored (GB)", lambda t, d: "–" if not d["rq"] else f"{sum(float(r['store_bytes'] or 0) for r in d['rq'].values()) / 1e9:.1f}")]
L = ["| check | " + " | ".join(tags) + " |", "|---|" + "---|" * len(tags)]
for lab, f in rows: L.append(f"| {lab} | " + " | ".join(str(f(t, R[t])) for t in tags) + " |")
print("\n".join(L))
