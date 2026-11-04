#!/usr/bin/env python3
"""Experiment C (2026-11-04): scheduling gap analysis. For every scenario group of the given B runs, replays the MEASURED
request sequence (arrival instants, lengths, tiers served) through the calibrated model (sched_sim.py) under the policies
vllm (model of the inspected scheduler; its agreement with the measured TTFTs is the model's validation), zero (ZERO-DELAY
loads), srpt (CLAIRVOYANT shortest-remaining-prefill-first) and hits (hits before cold), and decomposes the MEASURED TTFT
of each request into queue wait before the load starts, KV load, ready-but-waiting, compute (scheduled -> first token)
and the client / frontend legs. Writes <out>/c-summary.csv (one row per run x group x policy) and
<out>/c-decomposition.csv (one row per run x group x tier with the median / mean of each leg).
usage: run_c.py <B dir> <params.json> <out dir> [tags=b-default,b-eager,b-workers4,b-prio-hits,b-prio-cold] [out_tokens=32]"""
import csv, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sched_sim import Sim, DEFAULT
from analyze_a import q

B, PJ, OUT = sys.argv[1:4]; kv = dict(a.split("=", 1) for a in sys.argv[4:])
TAGS = kv.get("tags", "b-default,b-eager,b-workers4,b-prio-hits,b-prio-cold").split(","); OUT_TOK = int(kv.get("out_tokens", "32"))
os.makedirs(OUT, exist_ok=True); P = json.load(open(PJ)); sim = Sim(P)
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None

summary = []; decomp = []
for tag in TAGS:
    p = f"{B}/{tag}-requests.csv"
    if not os.path.exists(p): continue
    rows = [r for r in csv.DictReader(open(p)) if r["status"] == "200" and r["case"] in ("host", "gpu", "cold")]
    groups = {}
    for r in rows: groups.setdefault(r["grp"], []).append(r)
    for grp, rs in sorted(groups.items()):
        if not (grp.startswith("s1") or grp.startswith("s2") or grp.startswith("s3") or grp.startswith("s0") or grp.startswith("s4")): continue
        reqs = []
        for r in sorted(rs, key=lambda r: float(r["send_mono"])):
            L = int(float(r["prompt_tokens"])); tier = r["tier"]
            reqs.append(dict(rid=r["rid"], t_arr=float(r["send_mono"]), L=L, tier=tier, out=OUT_TOK, bytes=(fl(r["retrieve_bytes"]) or (L * DEFAULT["kv_bytes"] if tier == "host" else 0)), ttft_meas=float(r["ttft_client_ms"]) / 1000))
        t0 = reqs[0]["t_arr"]
        for r in reqs: r["t_arr"] -= t0
        meas = [r["ttft_meas"] for r in reqs]
        base = dict(tag=tag, grp=grp, n=len(reqs), policy="measured", mean_ms=sum(meas) / len(meas) * 1000, p50_ms=q(meas, .5) * 1000, p95_ms=q(meas, .95) * 1000, p99_ms=q(meas, .99) * 1000)
        summary.append(base)
        p_ch = dict(P, n_ch=4) if tag == "b-workers4" else P
        for pol in ("vllm", "zero", "srpt", "hits"):
            res = Sim(p_ch).run(reqs, pol); v = [x["ttft_s"] for x in res if x["ttft_s"] is not None]
            if not v: continue
            row = dict(tag=tag, grp=grp, n=len(v), policy=pol, mean_ms=sum(v) / len(v) * 1000, p50_ms=q(v, .5) * 1000, p95_ms=q(v, .95) * 1000, p99_ms=q(v, .99) * 1000)
            if pol == "vllm":
                err = [(x["ttft_s"] - r["ttft_meas"]) * 1000 for x, r in zip(res, reqs) if x["ttft_s"] is not None]
                row["err_median_ms"] = q(err, .5); row["err_p90_abs_ms"] = q([abs(e) for e in err], .9)
            summary.append(row)
        # measured decomposition per tier
        for tier in ("all", "host", "gpu", "cold"):
            sel = [r for r in rs if tier == "all" or r["tier"] == tier]
            if not sel: continue
            legs = {"client_to_queued": [fl(r["queued_ms"]) for r in sel], "queued_to_load_start": [fl(r["kv_wait_ms"]) - fl(r["queued_ms"]) if fl(r["kv_wait_ms"]) is not None and fl(r["queued_ms"]) is not None else None for r in sel],
                    "kv_load": [fl(r["kv_load_wait_ms"]) for r in sel], "ready_to_sched": [fl(r["ready_to_sched_ms"]) for r in sel],
                    "queued_to_sched_no_load": [fl(r["scheduled_ms"]) - fl(r["queued_ms"]) if fl(r["kv_wait_ms"]) is None and fl(r["scheduled_ms"]) is not None and fl(r["queued_ms"]) is not None else None for r in sel],
                    "compute": [fl(r["prefill_ms"]) for r in sel], "engine_to_client": [fl(r["engine_to_client_ms"]) for r in sel], "ttft": [fl(r["ttft_client_ms"]) for r in sel]}
            d = dict(tag=tag, grp=grp, tier=tier, n=len(sel))
            for k, v in legs.items():
                v = [x for x in v if x is not None]
                d[k + "_p50"] = q(v, .5) if v else None; d[k + "_mean"] = sum(v) / len(v) if v else None; d[k + "_n"] = len(v)
            decomp.append(d)
keys = sorted({k for s in summary for k in s}, key=lambda k: (k not in ("tag", "grp", "n", "policy"), k))
with open(f"{OUT}/c-summary.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); [w.writerow({k: ("" if s.get(k) is None else (f"{s[k]:.3f}" if isinstance(s.get(k), float) else s.get(k))) for k in keys}) for s in summary]
keys = sorted({k for s in decomp for k in s}, key=lambda k: (k not in ("tag", "grp", "tier", "n"), k))
with open(f"{OUT}/c-decomposition.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); [w.writerow({k: ("" if s.get(k) is None else (f"{s[k]:.3f}" if isinstance(s.get(k), float) else s.get(k))) for k in keys}) for s in decomp]
for s in summary:
    if s["policy"] in ("measured", "vllm", "zero", "srpt"): print(f"{s['tag']:12s} {s['grp']:12s} {s['policy']:9s} n={s['n']:3d} mean {s['mean_ms']:7.0f} p50 {s['p50_ms']:7.0f} p95 {s['p95_ms']:7.0f} p99 {s['p99_ms']:7.0f}" + (f"  model err median {s['err_median_ms']:.0f} ms, p90|err| {s['err_p90_abs_ms']:.0f} ms" if s["policy"] == "vllm" else ""))
