#!/usr/bin/env python3
"""Markdown tables for the RQ1-B agent runtime validation (2026-10-17) from <tag>-summary.json and <tag>-replay.csv.
usage: kv_agent_tables.py <dir> <tag1> [tag2 ...]"""
import csv, json, os, sys
D = sys.argv[1]; tags = sys.argv[2:]
S = {t: json.load(open(f"{D}/{t}-summary.json")) for t in tags}
def q(t, k, p="p50", f="{:.2f}"): v = S[t][k]; return f.format(v[p]) if isinstance(v, dict) and p in v else "–"
def pp(t, k, p1="p50", p2="p90", f="{:.2f}"): return f"{q(t, k, p1, f)} / {q(t, k, p2, f)}"
rows = [
 ("tasks / LLM calls", lambda t: f"{S[t]['tasks']} / {S[t]['calls']}"),
 ("LLM calls per task p50 / p90", lambda t: pp(t, "calls_per_task", f="{:.0f}")),
 ("outcomes", lambda t: ", ".join(f"{k} {v}" for k, v in S[t]["outcomes"].items())),
 ("request submit → LMCache lookup, s (p50 / p90)", lambda t: pp(t, "queue_wait_s", f="{:.3f}")),
 ("lookup → response (prefill + decode), s", lambda t: pp(t, "lookup_to_response_s")),
 ("tool execution, s", lambda t: pp(t, "tool_duration_s")),
 ("continue decision → next call's lookup, s", lambda t: pp(t, "continue_lead_to_next_lookup_s")),
 ("continue: context chunks re-read by the next call", lambda t: f"{100 * S[t]['continue_precision']['mean']:.0f}%"),
 ("continue: next call's chunks that already exist", lambda t: f"{100 * S[t]['continue_recall_of_next']['mean']:.0f}%"),
 ("continue: context chunks evicted before the next call", lambda t: f"{100 * S[t]['continue_context_evicted_before_next']['mean']:.1f}%"),
 ("continue: next call fully hit in LMCache", lambda t: f"{100 * S[t]['continue_next_full_hit']['mean']:.0f}%"),
 ("end: private chunks never read again", lambda t: f"{S[t]['end_private_dead']} / {S[t]['end_private_chunks']} ({100 * S[t]['end_private_dead'] / max(1, S[t]['end_private_chunks']):.0f}%)"),
 ("end: shared chunks read again by other tasks", lambda t: f"{S[t]['end_shared_alive']} / {S[t]['end_shared_chunks']} ({100 * S[t]['end_shared_alive'] / max(1, S[t]['end_shared_chunks']):.0f}%)"),
 ("end decision − last KV write of the task, s", lambda t: pp(t, "end_minus_last_write_s")),
 ("end decision − last LMCache lookup of the task, s", lambda t: pp(t, "end_minus_last_lookup_s")),
 ("age of the task's private chunks at the end, s", lambda t: pp(t, "end_private_block_age_s")),
 ("end decision → eviction of its private chunks under LRU, s", lambda t: pp(t, "dead_residence_after_end_s", f="{:.1f}")),
 ("L1 turnover (write → eviction), s", lambda t: pp(t, "l1_turnover_write_to_evict_s", f="{:.1f}")),
 ("write → next reuse of a chunk, s", lambda t: pp(t, "write_to_next_reuse_s", f="{:.1f}")),
 ("chunks written / evicted / unique", lambda t: f"{S[t]['writes']} / {S[t]['evictions']} / {S[t]['unique_chunks']}"),
 ("final call's new chunks, share of all writes", lambda t: f"{100 * S[t]['end_last_call_new_chunks_share_of_writes']:.0f}%"),
 ("REAL reuse-hit share in LMCache (chunks seen before that hit)", lambda t: f"{S[t]['reuse_hit_share_real']:.3f} ({S[t]['reuse_chunks_hit']}/{S[t]['reuse_chunks']})"),
]
print("| | " + " | ".join(tags) + " |"); print("|---|" + "---|" * len(tags))
for name, f in rows: print(f"| {name} | " + " | ".join(f(t) for t in tags) + " |")
print()
for t in tags:
    p = f"{D}/{t}-replay.csv"
    if not os.path.exists(p): continue
    R = list(csv.DictReader(open(p))); caps = sorted({int(r["cap"]) for r in R}); G = {(r["policy"], int(r["cap"])): r for r in R}
    pols = ["split", "lru", "slru", "ttl10", "ttl30", "event_end", "event_both", "event_both+slru", "event_end+defer", "event_both+defer", "oracle"]
    print(f"Replay of {t} — reuse-hit share (share of the oracle's gain over global LRU) and chunks written (w):\n")
    print("| capacity | " + " | ".join(pols) + " |"); print("|---|" + "---|" * len(pols))
    for c in caps:
        sp = float(G[("lru", c)]["reuse_hit_share"]); orc = float(G[("oracle", c)]["reuse_hit_share"]); cells = []
        for p_ in pols:
            r = G.get((p_, c))
            if r is None: cells.append("–"); continue
            v = float(r["reuse_hit_share"]); g = 100 * (v - sp) / max(1e-9, orc - sp)
            cells.append(f"{v:.3f}" + ("" if p_ in ("split", "lru", "oracle") else f" ({g:.0f}%)") + f" w{int(r['written_chunks'])}")
        print(f"| {c} chunks = {float(G[('split', c)]['cap_GB']):.2f} GB | " + " | ".join(cells) + " |")
    print()
