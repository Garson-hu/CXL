#!/usr/bin/env python3
"""Join the three records of one serving run into per-request time lines (Experiment A and the single-request parts of
B / E): the client record (send / first token / end, monotonic ns), the vLLM hook (arrival, queued, scheduled, first
token, monotonic s; kv_wait / kv_arrived / run from the step log) and the LMCache event bus (wall clock s: request start,
lookup, lookup end with hit tokens, retrieve start / end on the GPU stream with bytes). All times are converted to
milliseconds after the client's send instant (monotonic); LMCache's wall clock is mapped with the offset
t_wall - t_mono recorded by the vLLM hook at start-up (same host, both clocks system-wide).
Outputs <out>/<tag>-timeline.csv (one row per request) and prints / writes <out>/<tag>-summary.md (per case and L).
usage: analyze_a.py <out> <tag> [more tags ...]"""
import csv, glob, json, os, statistics as st, sys

def load_run(out, tag):
    cl = [json.loads(l) for l in open(f"{out}/{tag}-client.jsonl")]
    req = {}; off = None; steps_req = {}
    for f in glob.glob(f"{out}/{tag}-vllmevt.req.*.jsonl"):
        for l in open(f):
            d = json.loads(l)
            if d["ev"] == "vllmevt.start": off = d["t_wall"] - d["t_mono"]
            elif d["ev"] == "finished": req[d["rid"]] = d
    for f in glob.glob(f"{out}/{tag}-vllmevt.step.*.jsonl"):
        for l in open(f):
            d = json.loads(l)
            if d.get("ev") == "req": steps_req[d["rid"]] = d
    ev = {}
    if os.path.exists(f"{out}/{tag}-kvevents.jsonl"):
        for l in open(f"{out}/{tag}-kvevents.jsonl"):
            d = json.loads(l); sid = d.get("sid") or d.get("request_id") or ""
            if sid: ev.setdefault(sid, []).append(d)
    return cl, req, steps_req, ev, off

def timeline(c, req, steps_req, ev, off):
    """one row: all instants in ms after the client's send"""
    rid = "cmpl-" + c["rid"] + "-0"; r = req.get(rid); t0 = c["send_mono_ns"] / 1e9
    row = dict(rid=c["rid"], case=c["case"], L=c["L"], rep=c["rep"], grp=c.get("grp", ""), prompt_tokens=c["prompt_tokens"], cached_tokens=c["cached_tokens"],
               ttft_client_ms=c["ttft_ms"], total_ms=c["total_ms"], status=c["status"], error=c.get("error"))
    ms = lambda t_mono: None if t_mono is None else (t_mono - t0) * 1000
    wms = lambda t_wall: None if (t_wall is None or off is None) else (t_wall - off - t0) * 1000
    row["first_token_client_ms"] = ms(c["first_mono_ns"] / 1e9) if c.get("first_mono_ns") else None
    if r:
        row.update(irid=r["irid"], arrival_ms=wms(r["arrival_wall"]), queued_ms=ms(r["queued_mono"]), scheduled_ms=ms(r["scheduled_mono"]),
                   first_token_engine_ms=ms(r["first_token_mono"]), vllm_cached=r["cached_tokens"], preemptions=r["preemptions"])
        s = steps_req.get(r["irid"])
        if s: row.update(kv_wait_ms=ms(s["kv_wait_mono"]), kv_arrived_ms=ms(s["kv_arrived_mono"]), run_ms=ms(s["run_mono"]))
        E = ev.get(r["irid"], [])
        for d in E:
            e = d["ev"]
            if e == "mp.request.start": row["lm_request_ms"] = wms(d["t"])
            elif e == "mp.lookup_prefetch.start": row["lookup_start_ms"] = wms(d["t"])
            elif e == "mp.lookup_prefetch.end":
                row.update(lookup_end_ms=wms(d["t"]), hit_tokens=d.get("hit_tokens"), l1_hit_tokens=d.get("l1_hit_tokens"), l2_hit_tokens=d.get("l2_hit_tokens"), requested_tokens=d.get("requested_tokens"))
            elif e == "mp.retrieve.start": row["retrieve_start_ms"] = min(row.get("retrieve_start_ms", 1e18), wms(d["t"]))
            elif e == "mp.retrieve.end":
                row["retrieve_end_ms"] = max(row.get("retrieve_end_ms", -1e18), wms(d["t"])); row["retrieve_bytes"] = row.get("retrieve_bytes", 0) + (d.get("total_bytes") or 0)
                row["retrieve_tokens"] = row.get("retrieve_tokens", 0) + (d.get("num_tokens") or 0); row["n_retrieves"] = row.get("n_retrieves", 0) + 1
            elif e == "mp.store.end":
                row["store_bytes"] = row.get("store_bytes", 0) + (d.get("total_bytes") or 0); row["n_stores"] = row.get("n_stores", 0) + 1
    g = row.get
    if g("lookup_start_ms") is not None and g("lookup_end_ms") is not None: row["lookup_ms"] = g("lookup_end_ms") - g("lookup_start_ms")
    if g("retrieve_start_ms") is not None and g("retrieve_end_ms") is not None:
        row["retrieve_ms"] = g("retrieve_end_ms") - g("retrieve_start_ms")
        if row["retrieve_ms"] > 0 and g("retrieve_bytes"): row["retrieve_GBps"] = g("retrieve_bytes") / row["retrieve_ms"] / 1e6
        if g("scheduled_ms") is not None: row["kv_end_to_sched_ms"] = g("scheduled_ms") - g("retrieve_end_ms")
    if g("scheduled_ms") is not None and g("first_token_engine_ms") is not None: row["prefill_ms"] = g("first_token_engine_ms") - g("scheduled_ms")
    if g("queued_ms") is not None and g("scheduled_ms") is not None: row["queue_to_sched_ms"] = g("scheduled_ms") - g("queued_ms")
    if g("first_token_engine_ms") is not None and g("first_token_client_ms") is not None: row["engine_to_client_ms"] = g("first_token_client_ms") - g("first_token_engine_ms")
    return row

COLS = ["rid", "case", "L", "rep", "grp", "prompt_tokens", "cached_tokens", "vllm_cached", "hit_tokens", "l1_hit_tokens", "l2_hit_tokens", "ttft_client_ms", "arrival_ms", "queued_ms",
        "lm_request_ms", "lookup_start_ms", "lookup_end_ms", "lookup_ms", "kv_wait_ms", "retrieve_start_ms", "retrieve_end_ms", "retrieve_ms", "retrieve_bytes", "retrieve_tokens", "n_retrieves",
        "retrieve_GBps", "kv_arrived_ms", "kv_end_to_sched_ms", "scheduled_ms", "run_ms", "queue_to_sched_ms", "first_token_engine_ms", "prefill_ms", "first_token_client_ms", "engine_to_client_ms",
        "store_bytes", "n_stores", "preemptions", "total_ms", "status", "error", "irid"]

def q(v, p):
    v = sorted(v); return v[min(len(v) - 1, int(round(p * (len(v) - 1))))]

def fmt(v):
    return "-" if v is None else (f"{v:.1f}" if isinstance(v, float) else str(v))

def summarize(rows, keys=("ttft_client_ms", "lookup_ms", "retrieve_ms", "retrieve_GBps", "kv_end_to_sched_ms", "queue_to_sched_ms", "prefill_ms", "engine_to_client_ms")):
    groups = {}
    for r in rows:
        if r["status"] != 200 or r["case"] in ("warm", "fill_store"): continue
        groups.setdefault((r["case"], r["L"]), []).append(r)
    lines = ["| case | L | n | cached tok (median) | TTFT client ms p50 / min / max | " + " | ".join(k.replace("_ms", "").replace("_", " ") + " (median)" for k in keys[1:]) + " | retrieve MB |", "|" + "---|" * (6 + len(keys)) ]
    for (case, L), g in sorted(groups.items(), key=lambda x: (x[0][0], x[0][1])):
        tt = [r["ttft_client_ms"] for r in g]
        cells = [case, str(L), str(len(g)), fmt(q([r["cached_tokens"] for r in g], .5)), f"{q(tt, .5):.1f} / {min(tt):.1f} / {max(tt):.1f}"]
        for k in keys[1:]:
            v = [r[k] for r in g if r.get(k) is not None]; cells.append(fmt(q(v, .5)) if v else "-")
        mb = [r["retrieve_bytes"] / 1e6 for r in g if r.get("retrieve_bytes")]; cells.append(fmt(q(mb, .5)) if mb else "-")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)

if __name__ == "__main__":
    out = sys.argv[1]
    for tag in sys.argv[2:]:
        cl, req, steps_req, ev, off = load_run(out, tag)
        rows = [timeline(c, req, steps_req, ev, off) for c in cl]
        with open(f"{out}/{tag}-timeline.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore"); w.writeheader()
            for r in rows: w.writerow({k: ("" if r.get(k) is None else (f"{r[k]:.3f}" if isinstance(r.get(k), float) else r.get(k))) for k in COLS})
        s = f"## {tag}\n\n" + summarize(rows) + "\n"
        open(f"{out}/{tag}-summary.md", "w").write(s); print(s)
