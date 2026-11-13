#!/usr/bin/env python3
"""Experiment E, write side: what happens to the KV chunks a replay writes to the host tiers.

    writes_tier.py <B dir> [tag ...]      (default: every run with a <tag>-kvevents.jsonl)

No admission policy is enabled in this study: LMCache stores every chunk vLLM computed. From the event mirror of a run this script
follows every stored chunk (key = chunk hash) and reports how much of the write traffic was ever used afterwards within the replay:

    stored        distinct chunks written to L1 (and, with a write-through L2, to the L2); bytes incl. repeated stores of a chunk
    found         chunks that a LATER lookup found on the host (part of the prefix LMCache reported as a hit)
    retrieved     chunks that were copied back to the GPU at least once (a found chunk that the GPU's own prefix cache still
                  held is not copied)
    reuse delay   time from the first store of a chunk to the first lookup that found it

"found" is what an oracle admission policy would have kept; the rest is write traffic that bought nothing inside the window. This
is an accounting of measured events, not a policy that was run.

Second table, operations: LMCache's store and retrieve operations of the GPU transfer path (mp.store.* / mp.retrieve.*: submitted,
start, end). An operation is open from its start to its end; the table gives the time between the submission of a retrieve and
its start, the share of that waiting time during which another transfer operation (store or retrieve) was open - only that part
can be contention for the transfer thread; the rest is not explained by transfer traffic -, how many retrieves were submitted
or running while a store was open, and the seconds with both kinds open. This is overlap at the level of the application's
operations; whether the copies themselves overlap on the medium is in tables-e.md (copy intervals of the transfer thread).

Output: <B dir>/tables-writes.md, <B dir>/writes-summary.csv.
"""
import csv, glob, json, os, sys

CH = 256; CB = 9437184; G = 2**30


def q(v, p):
    v = sorted(v)
    return v[min(len(v) - 1, int(p * len(v)))] if v else None


def union(iv):
    out = []
    for a, b in sorted(iv):
        if out and a <= out[-1][1]: out[-1][1] = max(out[-1][1], b)
        else: out.append([a, b])
    return out


def intersect(A, B):
    i = j = 0; tot = 0.0
    while i < len(A) and j < len(B):
        lo = max(A[i][0], B[j][0]); hi = min(A[i][1], B[j][1])
        if hi > lo: tot += hi - lo
        if A[i][1] < B[j][1]: i += 1
        else: j += 1
    return tot


def one(d, tag):
    sub = {"store": {}, "retrieve": {}}; op = {"store": [], "retrieve": []}; open_ = {}
    first = {}; nstore = 0; look = {}; found = {}; retr = {}; n_ret_chunks = 0; n_found_chunks = 0; evicted = set(); lost = 0
    for l in open(f"{d}/{tag}-kvevents.jsonl"):
        if '"ev": "mem"' in l or "phase_samples" in l: continue
        try: e = json.loads(l)
        except Exception: continue
        ev = e.get("ev"); sid = e.get("sid")
        if ev.startswith("mp.store.") or ev.startswith("mp.retrieve."):
            kind, what = ev.split(".")[1:3]
            if what == "submitted": sub[kind].setdefault(sid, []).append(e["t"])
            elif what == "start":
                q_ = sub[kind].get(sid) or []; open_[(kind, e.get("transfer_key"))] = (q_.pop(0) if q_ else e["t"], e["t"])
            elif what == "end":
                o = open_.pop((kind, e.get("transfer_key")), None)
                if o: op[kind].append((o[0], o[1], e["t"], e.get("total_bytes") or 0))
        if ev == "l1.write.finished":
            for k in e.get("keys") or []:
                k = k[:16]; nstore += 1
                if k not in first: first[k] = e["t"]
                evicted.discard(k)
        elif ev == "l1.keys.evicted":
            for k in e.get("keys") or []: evicted.add(k[:16])
        elif ev == "mp.lookup":
            look[sid] = dict(hs=[h[:16] for h in e.get("hashes") or []], done=0, hit=0)
        elif ev == "mp.lookup_prefetch.end":
            L = look.get(sid)
            if L is None: continue
            L["hit"] = (e.get("hit_tokens") or 0) // CH
            for k in L["hs"][:L["hit"]]:
                n_found_chunks += 1
                if k not in found: found[k] = e["t"]
        elif ev == "mp.retrieve.end":
            L = look.get(sid)
            if L is None: continue
            n = int(round((e.get("num_tokens") or 0) / CH)); hi = max(0, L["hit"] - L["done"]); lo = max(0, hi - n); L["done"] += n
            for k in L["hs"][lo:hi]:
                n_ret_chunks += 1
                if k not in retr: retr[k] = e["t"]
        elif ev == "mp.vllm.end_session":
            look.pop(sid, None)
    us = union([(a, b) for _, a, b, _ in op["store"]]); ur = union([(a, b) for _, a, b, _ in op["retrieve"]])
    starts = sorted(a for _, a, b, _ in op["store"]); ends = sorted(b for _, a, b, _ in op["store"])
    import bisect
    def n_open(t0, t1):          # stores open at some time in [t0, t1]: started before t1 and not ended before t0
        return bisect.bisect_right(starts, t1) - bisect.bisect_left(ends, t0)
    with_store = sum(1 for s_, a, b, _ in op["retrieve"] if n_open(s_, b) > 0)
    allops = union([(a, b) for k in op for _, a, b, _ in op[k]]); cov = {}
    for k in op:
        w = [(s_, a) for s_, a, b, _ in op[k] if a > s_]
        cov[k] = (sum(a - s_ for s_, a in w), sum(intersect([[s_, a]], allops) for s_, a in w))
    O = dict(store_ops=len(op["store"]), retrieve_ops=len(op["retrieve"]),
             store_ms_p50=q([(b - a) * 1e3 for _, a, b, _ in op["store"]], .5), store_ms_p95=q([(b - a) * 1e3 for _, a, b, _ in op["store"]], .95),
             retrieve_ms_p50=q([(b - a) * 1e3 for _, a, b, _ in op["retrieve"]], .5), retrieve_ms_p95=q([(b - a) * 1e3 for _, a, b, _ in op["retrieve"]], .95),
             retrieve_wait_ms_p50=q([(a - s_) * 1e3 for s_, a, b, _ in op["retrieve"]], .5), retrieve_wait_ms_p95=q([(a - s_) * 1e3 for s_, a, b, _ in op["retrieve"]], .95),
             retrieve_wait_ms_max=max([(a - s_) * 1e3 for s_, a, b, _ in op["retrieve"]], default=None),
             store_wait_ms_p50=q([(a - s_) * 1e3 for s_, a, b, _ in op["store"]], .5), store_wait_ms_p95=q([(a - s_) * 1e3 for s_, a, b, _ in op["store"]], .95),
             retrieve_wait_s=cov["retrieve"][0], retrieve_wait_other_op_open_s=cov["retrieve"][1], store_wait_s=cov["store"][0], store_wait_other_op_open_s=cov["store"][1],
             retrieves_with_open_store=with_store, store_open_s=sum(b - a for a, b in us), retrieve_open_s=sum(b - a for a, b in ur), both_open_s=intersect(us, ur))
    S = len(first); F = sum(1 for k in found if k in first); R = sum(1 for k in retr if k in first)
    delay = [found[k] - first[k] for k in found if k in first and found[k] >= first[k]]
    return dict(tag=tag, stored_chunks=S, stores=nstore, written_GiB=nstore * CB / G, distinct_GiB=S * CB / G,
                found_chunks=F, found_share=F / S if S else None, retrieved_chunks=R, retrieved_share=R / S if S else None,
                never_found_GiB=(S - F) * CB / G, lookups_found_chunks=n_found_chunks, retrieved_chunk_copies=n_ret_chunks,
                retrieved_GiB=n_ret_chunks * CB / G, reuse_delay_s_p50=q(delay, .5), reuse_delay_s_p90=q(delay, .9), reuse_delay_s_max=max(delay) if delay else None, **O)


def main():
    d = sys.argv[1]; tags = sys.argv[2:] or sorted(os.path.basename(p)[:-len("-kvevents.jsonl")] for p in glob.glob(f"{d}/*-kvevents.jsonl"))
    rows = [one(d, t) for t in tags if os.path.exists(f"{d}/{t}-kvevents.jsonl")]
    rows = [r for r in rows if r["stored_chunks"]]
    if not rows: return
    with open(f"{d}/writes-summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    f1 = lambda x, n=1: "-" if x is None else f"{x:.{n}f}"
    T = ["# Experiment E, write side — the chunks a replay stored and what became of them (accounting of measured events; no admission policy was run)", "",
         "| run | stores (chunks) | written GiB | distinct chunks | distinct GiB | found by a later lookup: chunks (share of distinct) | copied back to the GPU: chunks (share) | never found GiB | chunk copies host → GPU (GiB) | reuse delay p50 / p90 / max s |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        T.append(f"| {r['tag']} | {r['stores']} | {r['written_GiB']:.1f} | {r['stored_chunks']} | {r['distinct_GiB']:.1f} | {r['found_chunks']} ({f1(r['found_share'], 3)}) | {r['retrieved_chunks']} ({f1(r['retrieved_share'], 3)}) | "
                 f"{r['never_found_GiB']:.1f} | {r['retrieved_chunk_copies']} ({r['retrieved_GiB']:.1f}) | {f1(r['reuse_delay_s_p50'], 0)} / {f1(r['reuse_delay_s_p90'], 0)} / {f1(r['reuse_delay_s_max'], 0)} |")
    T += ["", "Operations of the GPU transfer path (store = GPU -> host tier, retrieve = host tier -> GPU; one transfer thread):", "",
          "| run | store ops | retrieve ops | store op p50 / p95 ms | retrieve op p50 / p95 ms | retrieve: submitted → start p50 / p95 / max ms | sum of those waits s (of which another transfer op was open) | store: submitted → start p50 / p95 ms | sum s (of which another transfer op was open) | retrieves submitted or running while a store was open (share) | s with a store open | s with a retrieve open | s with both open |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        sh = r["retrieves_with_open_store"] / r["retrieve_ops"] if r["retrieve_ops"] else None
        T.append(f"| {r['tag']} | {r['store_ops']} | {r['retrieve_ops']} | {f1(r['store_ms_p50'])} / {f1(r['store_ms_p95'])} | {f1(r['retrieve_ms_p50'])} / {f1(r['retrieve_ms_p95'])} | "
                 f"{f1(r['retrieve_wait_ms_p50'])} / {f1(r['retrieve_wait_ms_p95'])} / {f1(r['retrieve_wait_ms_max'])} | {r['retrieve_wait_s']:.1f} ({r['retrieve_wait_other_op_open_s']:.1f}) | "
                 f"{f1(r['store_wait_ms_p50'], 0)} / {f1(r['store_wait_ms_p95'], 0)} | {r['store_wait_s']:.0f} ({r['store_wait_other_op_open_s']:.0f}) | "
                 f"{r['retrieves_with_open_store']} ({f1(sh, 2)}) | {r['store_open_s']:.1f} | {r['retrieve_open_s']:.1f} | {r['both_open_s']:.2f} |")
    open(f"{d}/tables-writes.md", "w").write("\n".join(T) + "\n"); print("\n".join(T))


if __name__ == "__main__":
    main()
