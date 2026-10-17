#!/usr/bin/env python3
"""RQ1-B agent runtime validation (2026-10-17): join the agent's events (run_agent.py, OpenAI Agents SDK hooks) with
LMCache's events (kvevt/sitecustomize.py) and measure what the continue / end decisions predict, when they arrive and
what the host cache did with the blocks. REAL APPLICATION evidence (vLLM 0.31 + LMCache 0.5.5 on c28's 4060 Ti).

Outputs (in <out_dir>): <tag>-calls.csv (one row per LLM call), <tag>-decisions.csv (one row per continue/end decision),
<tag>-summary.json, and figures fig-agent-timeline-<tag>, fig-agent-leadtimes-<tag>, fig-agent-signal-<tag>.
usage: kv_agent_events.py <run_dir> <tag> [out_dir=run_dir/..]"""
import bisect, collections, csv, json, os, re, statistics, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

run_dir, tag = sys.argv[1], sys.argv[2]; out_dir = sys.argv[3] if len(sys.argv) > 3 else os.path.dirname(os.path.abspath(run_dir))
RID = re.compile(r"agt(\d{4})c(\d{2})")
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.grid": True, "grid.color": "#e6e6e6", "legend.frameon": False, "svg.fonttype": "none"})
def pct(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else float("nan")
def summ(xs): return dict(n=len(xs), p10=pct(xs, .1), p50=pct(xs, .5), p90=pct(xs, .9), mean=(sum(xs) / len(xs)) if xs else float("nan")) if xs else dict(n=0)

# ------------------------------------------------------------------ agent events
A = [json.loads(l) for l in open(f"{run_dir}/{tag}-agent.jsonl")]
tasks = collections.defaultdict(lambda: dict(calls={}, tools=[], events=[]))
for e in A:
    if "task" not in e: continue
    T = tasks[e["task"]]; T["events"].append(e)
    if e["ev"] == "task_start": T.update(task=e["task"], kind=e["kind"], prompt=e["prompt"], t_start=e["t"], expected_calls=e["expected_calls"])
    elif e["ev"] == "llm_submit": T["calls"][e["rid"]] = dict(rid=e["rid"], t_submit=e["t"], n_items=e["n_items"])
    elif e["ev"] == "llm_response": T["calls"][e["rid"]].update(t_resp=e["t"], decision=e["decision"], tool_calls=e["tool_calls"], in_tokens=e["in_tokens"], out_tokens=e["out_tokens"], cached_tokens=e["cached_tokens"])
    elif e["ev"] == "llm_end": T.setdefault("llm_end", []).append((e["t"], e["decision"]))
    elif e["ev"] in ("tool_start", "tool_end", "tool_call"): T["tools"].append((e["t"], e["ev"], e["tool"]))
    elif e["ev"] == "agent_end": T["t_agent_end"] = e["t"]
    elif e["ev"] in ("task_end", "task_abort"): T["t_end"] = e["t"]; T["outcome"] = e["ev"] if e["ev"] == "task_end" else f"abort:{e['reason']}"; T["ok"] = e.get("ok"); T["n_calls"] = e["n_calls"]
for T in tasks.values():
    T["calls"] = sorted(T["calls"].values(), key=lambda c: c["rid"])
    le = T.get("llm_end", [])
    for c, (t_dec, dec) in zip(T["calls"], le): c["t_dec"] = t_dec; c["dec_hook"] = dec          # the SDK's on_llm_end: the runtime knows
    for c in T["calls"]: c.setdefault("t_dec", c.get("t_resp")); c.setdefault("decision", "?")

# ------------------------------------------------------------------ LMCache events
K = [json.loads(l) for l in open(f"{run_dir}/{tag}-kvevents.jsonl")]
req = collections.defaultdict(dict)                                   # rid -> lookup/prefetch/store/end_session
writes = collections.defaultdict(list); evicts = collections.defaultdict(list); reads = collections.defaultdict(list); touches = collections.defaultdict(list)
lookups = []                                                          # (t, rid, hashes, task, call)
for e in K:
    ev = e["ev"]; m = RID.search(e.get("sid") or "") or RID.search(e.get("request_id") or "")
    rid = m.group(0) if m else None
    if ev == "mp.lookup" and rid: req[rid].update(t_lookup=e["t"], hashes=e["hashes"], seq_len=e.get("seq_len")); lookups.append((e["t"], rid, e["hashes"], int(m.group(1)), int(m.group(2))))
    elif ev == "mp.lookup_prefetch.end" and rid: req[rid].update(t_lookup_end=e["t"], found=e.get("found_count"), hit_tokens=e.get("hit_tokens"), req_tokens=e.get("requested_tokens"))
    elif ev == "mp.store.start" and rid: req[rid].setdefault("t_store_start", e["t"])
    elif ev == "mp.store.end" and rid: req[rid]["t_store_end"] = e["t"]; req[rid]["stored_chunks"] = req[rid].get("stored_chunks", 0) + (e.get("stored_count") or 0)
    elif ev == "mp.retrieve.start" and rid: req[rid].setdefault("t_retrieve_start", e["t"])
    elif ev == "mp.retrieve.end" and rid: req[rid]["t_retrieve_end"] = e["t"]
    elif ev == "mp.vllm.end_session" and rid: req[rid]["t_end_session"] = e["t"]
    elif ev == "l1.write.finished":
        for k in e["keys"]: writes[k.split("/")[0]].append(e["t"])
    elif ev == "l1.keys.evicted":
        for k in e["keys"]: evicts[k.split("/")[0]].append(e["t"])
    elif ev == "l1.read.reserved":
        for k in e["keys"]: reads[k.split("/")[0]].append(e["t"])
    elif ev == "l1.keys.accessed":
        for k in e["keys"]: touches[k.split("/")[0]].append(e["t"])
lookups.sort()
first_write = {k: min(v) for k, v in writes.items()}
# which task(s) referenced each block, in time order
ref_by = collections.defaultdict(list)                                # key -> [(t_lookup, task)]
for t, rid, hs, tk, ci in lookups:
    for h in hs: ref_by[h].append((t, tk))
def seen_before(h, t, tk):
    """tasks other than tk that looked this block up before time t."""
    return {task for tt, task in ref_by[h] if tt < t and task != tk}
def accessed_after(h, t, tk=None):
    """does any request (optionally excluding task tk) look this block up after time t?"""
    return any(tt > t and (tk is None or task != tk) for tt, task in ref_by[h])
def evicted_between(h, t0, t1): return any(t0 < t <= t1 for t in evicts.get(h, ()))
def residence_after(h, t):
    """time from t until the block's next eviction, if it is resident at t (written before t, not evicted since)."""
    w = [x for x in writes.get(h, ()) if x <= t]
    if not w: return None
    ev_after = [x for x in evicts.get(h, ()) if x > t]
    return (ev_after[0] - t) if ev_after else None

# ------------------------------------------------------------------ per call rows
rows = []; lead_q = []; lead_resp = []
for tk, T in sorted(tasks.items()):
    for i, c in enumerate(T["calls"]):
        r = req.get(c["rid"], {}); c.update(r)
        hs = r.get("hashes", []); found = r.get("found") or 0
        n_reuse = sum(1 for h in hs if any(tt < r.get("t_lookup", 0) for tt, _ in ref_by[h]))   # chunks looked up before by anyone
        rows.append(dict(task=tk, call=i + 1, rid=c["rid"], kind=T.get("kind"), t_submit=c["t_submit"], t_lookup=r.get("t_lookup"), t_resp=c.get("t_resp"), t_dec=c.get("t_dec"),
                         queue_wait_s=(r["t_lookup"] - c["t_submit"]) if "t_lookup" in r else None, lookup_to_resp_s=(c["t_resp"] - r["t_lookup"]) if ("t_lookup" in r and "t_resp" in c) else None,
                         chunks=len(hs), chunks_hit=found, chunks_reuse=n_reuse, in_tokens=c.get("in_tokens"), cached_tokens=c.get("cached_tokens"), out_tokens=c.get("out_tokens"),
                         decision=c.get("decision"), tool_calls="|".join(c.get("tool_calls", [])), stored_chunks=r.get("stored_chunks", 0),
                         t_store_end=r.get("t_store_end"), t_end_session=r.get("t_end_session")))
        if "t_lookup" in r: lead_q.append(r["t_lookup"] - c["t_submit"])
with open(f"{out_dir}/{tag}-calls.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
# request trace for the offline replay (kv_agent_replay.py): one line per LLM call with the REAL events attached
with open(f"{out_dir}/{tag}-trace.jsonl", "w") as f:
    for tk, T in sorted(tasks.items()):
        for i, c in enumerate(T["calls"]):
            if c.get("hashes") is None: continue
            f.write(json.dumps(dict(task=tk, call=i + 1, rid=c["rid"], t_submit=c["t_submit"], t_lookup=c["t_lookup"], t_resp=c.get("t_resp"), t_dec=c.get("t_dec"), decision=c.get("decision"),
                                    t_task_end=T.get("t_agent_end") or T.get("t_end"), outcome=T.get("outcome"), hashes=c["hashes"], found=c.get("found"))) + "\n")

# ------------------------------------------------------------------ decisions
dec_rows = []; cont_lead_submit = []; cont_lead_lookup = []; cont_prec = []; cont_rec = []; cont_evicted = []; cont_hit_full = []
end_write_gap = []; end_private_dead = []; end_shared_alive = []; end_private_alive = []; end_dead_residence = []; end_lookup_gap = []
end_store_gap = []; tool_dur = []; cont_block_age = []; end_last_new = []; end_ages = []
for tk, T in sorted(tasks.items()):
    cs = T["calls"]
    # tool durations from the SDK hooks
    starts = {}
    for t, ev, name in T["tools"]:
        if ev == "tool_start": starts[name] = t
        elif ev == "tool_end" and name in starts: tool_dur.append(t - starts.pop(name))
    for i, c in enumerate(cs):
        hs = c.get("hashes"); t_dec = c.get("t_dec")
        if hs is None or t_dec is None: continue
        if c["decision"] == "continue" and i + 1 < len(cs) and cs[i + 1].get("hashes") is not None:
            nx = cs[i + 1]; nh = set(nx["hashes"]); ctx = list(hs)
            reused = [h for h in ctx if h in nh]; prec = len(reused) / max(1, len(ctx)); rec = len(reused) / max(1, len(nh))
            ev_before = sum(1 for h in ctx if evicted_between(h, t_dec, nx["t_lookup"]))
            cont_lead_submit.append(nx["t_submit"] - t_dec); cont_lead_lookup.append(nx["t_lookup"] - t_dec); cont_prec.append(prec); cont_rec.append(rec); cont_evicted.append(ev_before / max(1, len(ctx)))
            ages = [t_dec - first_write[h] for h in ctx if h in first_write and first_write[h] <= t_dec]
            if ages: cont_block_age.append(statistics.median(ages))
            cont_hit_full.append(1.0 if (nx.get("found") or 0) >= len(ctx) else 0.0)
            dec_rows.append(dict(task=tk, call=i + 1, decision="continue", t_dec=t_dec, context_chunks=len(ctx), next_chunks=len(nh), reused=len(reused), precision=prec, recall=rec,
                                 lead_to_next_submit_s=nx["t_submit"] - t_dec, lead_to_next_lookup_s=nx["t_lookup"] - t_dec, evicted_before_next=ev_before, next_found=nx.get("found")))
        elif c["decision"] == "end" or i == len(cs) - 1:
            ctx = list(hs); t_end = T.get("t_agent_end", t_dec)
            priv = [h for h in ctx if not seen_before(h, c["t_lookup"], tk)]; shared = [h for h in ctx if seen_before(h, c["t_lookup"], tk)]
            pd = sum(1 for h in priv if not accessed_after(h, t_end)); pa = len(priv) - pd
            sa = sum(1 for h in shared if accessed_after(h, t_end))
            end_private_dead.append(pd); end_private_alive.append(pa); end_shared_alive.append((sa, len(shared)))
            # KV write of this request's new chunks vs the end event
            new_w = [first_write[h] for h in priv if h in first_write and first_write[h] >= c["t_lookup"] - 1.0]
            if new_w: end_write_gap.append(t_end - max(new_w))
            end_last_new.append(len(new_w)); end_ages.extend(t_end - first_write[h] for h in priv if h in first_write and first_write[h] <= t_end)
            if c.get("t_store_end"): end_store_gap.append(t_end - c["t_store_end"])
            end_lookup_gap.append(t_end - c["t_lookup"])
            for h in priv:
                r_ = residence_after(h, t_end)
                if r_ is not None: end_dead_residence.append(r_)
            dec_rows.append(dict(task=tk, call=i + 1, decision="end" if c["decision"] == "end" else f"last:{T.get('outcome')}", t_dec=t_end, context_chunks=len(ctx), next_chunks=0, reused=0,
                                 precision=(pd / max(1, len(priv))), recall=None, private_chunks=len(priv), shared_chunks=len(shared), private_dead=pd, private_alive=pa, shared_alive=sa,
                                 end_minus_last_write_s=(t_end - max(new_w)) if new_w else None, end_minus_store_end_s=(t_end - c["t_store_end"]) if c.get("t_store_end") else None))
with open(f"{out_dir}/{tag}-decisions.csv", "w", newline="") as f:
    keys = sorted({k for r in dec_rows for k in r}); w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(dec_rows)

# ------------------------------------------------------------------ cache-level facts
res_lru = []                                                          # write -> eviction (turnover) for evicted keys
for k, ws in writes.items():
    for t in ws:
        ev_after = [x for x in evicts.get(k, ()) if x > t]
        if ev_after: res_lru.append(ev_after[0] - t)
reuse_gap = []                                                        # write -> next lookup by anyone
for k, (t0, *_) in ((k, sorted(v)) for k, v in writes.items()):
    nxt = [tt for tt, _ in ref_by[k] if tt > t0]
    if nxt: reuse_gap.append(nxt[0] - t0)
n_calls = len(rows); n_tasks = len(tasks); outcomes = collections.Counter(T.get("outcome", "?") for T in tasks.values())
reuse_chunks = sum(r["chunks_reuse"] for r in rows); hit_chunks = sum(min(r["chunks_hit"], r["chunks_reuse"]) for r in rows)
summary = dict(tag=tag, tasks=n_tasks, calls=n_calls, outcomes=dict(outcomes), calls_per_task=summ([len(T["calls"]) for T in tasks.values()]),
               decisions=dict(continue_=sum(1 for r in rows if r["decision"] == "continue"), end=sum(1 for r in rows if r["decision"] == "end")),
               queue_wait_s=summ(lead_q), tool_duration_s=summ(tool_dur), lookup_to_response_s=summ([r["lookup_to_resp_s"] for r in rows if r["lookup_to_resp_s"] is not None]),
               continue_lead_to_next_submit_s=summ(cont_lead_submit), continue_lead_to_next_lookup_s=summ(cont_lead_lookup),
               continue_context_block_age_s=summ(cont_block_age), continue_precision=summ(cont_prec), continue_recall_of_next=summ(cont_rec), continue_context_evicted_before_next=summ(cont_evicted), continue_next_full_hit=summ(cont_hit_full),
               end_private_chunks=sum(end_private_dead) + sum(end_private_alive), end_private_dead=sum(end_private_dead), end_private_alive=sum(end_private_alive),
               end_shared_chunks=sum(n for _, n in end_shared_alive), end_shared_alive=sum(a for a, _ in end_shared_alive),
               end_last_call_new_chunks=sum(end_last_new), end_last_call_new_chunks_share_of_writes=sum(end_last_new) / max(1, sum(len(v) for v in writes.values())), end_private_block_age_s=summ(end_ages), end_minus_last_write_s=summ(end_write_gap), end_minus_store_end_s=summ(end_store_gap), end_minus_last_lookup_s=summ(end_lookup_gap), dead_residence_after_end_s=summ(end_dead_residence),
               l1_turnover_write_to_evict_s=summ(res_lru), write_to_next_reuse_s=summ(reuse_gap), chunks_lookedup=sum(r["chunks"] for r in rows), reuse_chunks=reuse_chunks, reuse_chunks_hit=hit_chunks,
               reuse_hit_share_real=hit_chunks / max(1, reuse_chunks), evictions=sum(len(v) for v in evicts.values()), writes=sum(len(v) for v in writes.values()), unique_chunks=len(ref_by))
json.dump(summary, open(f"{out_dir}/{tag}-summary.json", "w"), indent=1)
print(json.dumps(summary, indent=1))

# ------------------------------------------------------------------ figures
# 1. lead-time CDFs
def cdf(ax, xs, label, **kw):
    xs = sorted(x for x in xs if x is not None and x > 0)
    if xs: ax.plot(xs, [i / len(xs) for i in range(1, len(xs) + 1)], label=f"{label} (n={len(xs)})", **kw)
fig, axs = plt.subplots(1, 2, figsize=(12, 4.4))
cdf(axs[0], lead_q, "request submit → LMCache lookup"); cdf(axs[0], cont_lead_lookup, "continue decision → next call's lookup"); cdf(axs[0], tool_dur, "tool execution")
cdf(axs[0], [r["lookup_to_resp_s"] for r in rows], "lookup → response (prefill + decode)")
axs[0].set_xscale("log"); axs[0].set_xlabel("seconds"); axs[0].set_ylabel("CDF"); axs[0].legend(fontsize=8.5, loc="upper left"); axs[0].set_title("Agent-side lead times (real run)", fontsize=11)
cdf(axs[1], end_write_gap, "end decision − last KV write of the task"); cdf(axs[1], cont_block_age, "age of the context blocks at a continue decision"); cdf(axs[1], end_dead_residence, "end decision → eviction of its private blocks (LRU)")
cdf(axs[1], res_lru, "L1 turnover: write → eviction"); cdf(axs[1], reuse_gap, "write → next reuse of the block")
axs[1].set_xscale("log"); axs[1].set_xlabel("seconds"); axs[1].set_ylabel("CDF"); axs[1].legend(fontsize=8.5, loc="upper left"); axs[1].set_title(f"Cache-side timing (L1 as configured, tag {tag})", fontsize=11)
fig.tight_layout(); fig.savefig(f"{out_dir}/fig-agent-leadtimes-{tag}.png", dpi=200); fig.savefig(f"{out_dir}/fig-agent-leadtimes-{tag}.svg"); plt.close(fig)
# 2. one example task timeline (the longest completed task)
ex = max((T for T in tasks.values() if T.get("outcome") == "task_end" and len(T["calls"]) >= 3), key=lambda T: len(T["calls"]), default=None)
if ex:
    t0 = ex["t_start"]; fig, ax = plt.subplots(figsize=(12, 4.2)); y = 0; seen_dec = set(); TOOLC = {"search_reports": "#ff7f0e", "read_report": "#bcbd22", "calculate": "#8c564b"}; seen_tool = set()
    for i, c in enumerate(ex["calls"]):
        ax.plot([c["t_submit"] - t0, c["t_resp"] - t0], [2, 2], color="#1f77b4", lw=6, solid_capstyle="butt", label="LLM call (submit → response)" if i == 0 else None)
        if c.get("t_lookup"): ax.plot(c["t_lookup"] - t0, 2, marker="|", color="k", ms=14, label="LMCache lookup" if i == 0 else None)
        if c.get("t_store_end"): ax.plot(c["t_store_end"] - t0, 1.5, marker="v", color="#d62728", ms=7, label="KV store finished" if i == 0 else None)
        if c.get("t_dec"): ax.plot(c["t_dec"] - t0, 2.3, marker="o" if c["decision"] == "continue" else "X", color="#2ca02c" if c["decision"] == "continue" else "#d62728", ms=7, ls="", label=("runtime decision: continue" if c["decision"] == "continue" else "runtime decision: end") if c["decision"] not in seen_dec else None); seen_dec.add(c["decision"])
    starts = {}
    first_tool = True
    for t, ev, name in ex["tools"]:
        if ev == "tool_start": starts[name] = t
        elif ev == "tool_end" and name in starts:
            ax.plot([starts[name] - t0, t - t0], [1, 1], color=TOOLC.get(name, "#ff7f0e"), lw=6, solid_capstyle="butt", label=f"tool: {name}" if name not in seen_tool else None); seen_tool.add(name)
            starts.pop(name)
    if ex.get("t_agent_end"): ax.axvline(ex["t_agent_end"] - t0, color="#d62728", ls=":", label="agent end (final output)")
    # evictions of this task's private blocks
    priv = {h for c in ex["calls"] for h in c.get("hashes", []) if not seen_before(h, c.get("t_lookup", 0), None)}
    xmax = (ex["t_end"] - t0) + 35
    evs = sorted(t - t0 for h in priv for t in evicts.get(h, ()))
    if evs: ax.plot([e for e in evs if e <= xmax], [0.3] * len([e for e in evs if e <= xmax]), marker="x", ls="", color="#9467bd", label="eviction of one of its private blocks")
    late = [e for e in evs if e > xmax]
    if late: ax.annotate(f"+{len(late)} evictions later (up to {max(late):.0f} s)", (xmax, 0.3), ha="right", va="bottom", fontsize=8, color="#9467bd")
    ax.set_xlim(-0.5, xmax); ax.set_yticks([0.3, 1, 2]); ax.set_yticklabels(["cache", "tools", "LLM"]); ax.set_xlabel("seconds since task start"); ax.set_ylim(0, 2.6)
    ax.set_title(f"Task {ex.get('task', '')} ({ex.get('kind')}): {ex['prompt'][:90]}", fontsize=10, loc="left"); ax.legend(fontsize=8, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.22))
    fig.tight_layout(); fig.savefig(f"{out_dir}/fig-agent-timeline-{tag}.png", dpi=200); fig.savefig(f"{out_dir}/fig-agent-timeline-{tag}.svg"); plt.close(fig)
# 3. signal semantics
fig, ax = plt.subplots(figsize=(8.5, 4))
items = [("continue:\ncontext re-read\nby next call", summary["continue_precision"].get("mean", 0)), ("continue:\nnext call's blocks\nalready existing", summary["continue_recall_of_next"].get("mean", 0)),
         ("continue:\ncontext evicted\nbefore next call", summary["continue_context_evicted_before_next"].get("mean", 0)),
         ("end:\nprivate blocks\nnever read again", summary["end_private_dead"] / max(1, summary["end_private_chunks"])), ("end:\nshared blocks\nread again by others", summary["end_shared_alive"] / max(1, summary["end_shared_chunks"]))]
b = ax.bar(range(len(items)), [100 * v for _, v in items], color=["#2ca02c", "#2ca02c", "#9467bd", "#d62728", "#1f77b4"])
for r, (_, v) in zip(b, items): ax.annotate(f"{100 * v:.0f}%", (r.get_x() + r.get_width() / 2, 100 * v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=9)
ax.set_xticks(range(len(items))); ax.set_xticklabels([k for k, _ in items], fontsize=8.5); ax.set_ylabel("% of blocks"); ax.set_ylim(0, 112); ax.set_title(f"What the real continue / end decisions say about the blocks (tag {tag})", fontsize=10.5)
fig.tight_layout(); fig.savefig(f"{out_dir}/fig-agent-signal-{tag}.png", dpi=200); fig.savefig(f"{out_dir}/fig-agent-signal-{tag}.svg"); plt.close(fig)
print("figures written to", out_dir)
