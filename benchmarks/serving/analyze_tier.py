#!/usr/bin/env python3
"""CXL-vs-NVMe study (2026-11-12): per-request time lines of a serving run with the media-level records of the kvtier hook.

Builds on analyze_a.py (client + vLLM hook + LMCache event bus -> instants in ms after the client's send) and adds, per request:
  media          where LMCache served the request's chunks from, counted per chunk:
                   l1_dram / l1_dax  chunks read from L1 objects on DRAM / on Device-DAX (LMCache's own L1ObjectMeta.backend)
                   l2_chunks         chunks loaded from the L2 adapter for this request (dax.r / fs.r lines, or load-task key counts)
  l2_load_ms     wall time of the L2 load tasks of the request (l2.load_task.submitted -> completed): the media read, including
                 the copy into the L1 object the GPU transfer then reads; l2_bytes; l2_GiBps = l2_bytes / l2_load_ms
  media_copy_ms  sum of the per-chunk copy / read times inside those tasks (thread time; > l2_load_ms when workers run in parallel)
  staging_ms     host -> GPU staging copies of the request's retrieve (TransferPhase.STAGING samples), staging_bytes, h2d_GiBps
  kernel_ms      GPU kernels that scatter the staged bytes into vLLM's KV blocks (TransferPhase.KERNEL): the KV install
  lm_cpu_ms      CPU time the LMCache server process spent between the request's start and end events (all threads; valid for
                 sequential requests only)
Joins: a request's L2 prefetch (the prefetch controller has its own request counter) is the one submitted inside the request's
lookup window whose loaded chunk count equals the lookup's l2_hit_tokens (exact for sequential requests; under concurrency ties are
broken by the nearest submission time); L1 media letters by chunk hash; the per-chunk copy lines (dax.r / fs.r) carry no request
and are summed over the lookup window, so media_copy_ms is per request only when requests do not overlap.
usage: analyze_tier.py <out> <tag> [more tags ...]     -> <out>/<tag>-tier-timeline.csv, <out>/<tag>-tier-summary.md"""
import csv, json, os, statistics as st, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_a import load_run, timeline, COLS, q, fmt

XCOLS = ["l1_dram", "l1_dax", "l2_chunks", "l2_tasks", "l2_load_ms", "l2_bytes", "l2_GiBps", "l2_start_ms", "l2_end_ms", "media_copy_ms", "media_first_ms", "media_last_ms",
         "staging_ms", "staging_bytes", "h2d_GiBps", "kernel_ms", "n_stage", "lm_cpu_ms", "store_staging_ms", "store_kernel_ms", "l2_store_ms", "l2_store_bytes"]

def load_tier(out, tag):
    """the records without a session id, in time order"""
    recs = []; mono_off = None
    p = f"{out}/{tag}-kvevents.jsonl"
    if not os.path.exists(p): return recs, mono_off
    for l in open(p):
        try: d = json.loads(l)
        except Exception: continue
        if mono_off is None and "t" in d and "tm" in d and d["ev"] != "mem": mono_off = d["t"] - d["tm"] / 1e9     # wall - monotonic of the LMCache process
        recs.append(d)
    return recs, mono_off

def enrich(rows, cl, req, recs, off, mono_off, chunk=256):
    """off: vLLM hook's wall - monotonic; LMCache event times are wall clock"""
    import bisect
    by_sid = {}; loose = []; pf = {}
    for d in recs:
        sid = d.get("sid") or ""; e = d["ev"]
        if sid: by_sid.setdefault(sid, []).append(d)
        else: loose.append(d)
        # the L2 prefetch requests of the prefetch controller (its own request_id counter) and their load tasks
        if e == "l2.prefetch.lookup.submitted": pf.setdefault(d["request_id"], dict(tasks=[], open={})).update(sub_t=d["t"], key_count=d.get("key_count"))
        elif e == "l2.prefetch.load.completed": pf.setdefault(d["request_id"], dict(tasks=[], open={})).update(done_t=d["t"], loaded=d.get("loaded_count"), failed=d.get("failed_count"))
        elif e == "l2.load_task.submitted": pf.setdefault(d["request_id"], dict(tasks=[], open={}))["open"][(d.get("adapter_index"), d.get("task_id"))] = d
        elif e == "l2.load_task.completed":
            P = pf.setdefault(d["request_id"], dict(tasks=[], open={})); s_ = P["open"].pop((d.get("adapter_index"), d.get("task_id")), None)
            if s_: P["tasks"].append((s_["t"], d["t"], s_.get("total_bytes") or 0, s_.get("key_count") or 0))
    # wall time of the media-copy lines (they carry monotonic ns of the LMCache process, same system-wide clock)
    def wall(d): return d["t"] if "t" in d else (d["t0"] / 1e9 + mono_off if mono_off is not None else None)
    loose_t = [(wall(d), d) for d in loose if wall(d) is not None and d["ev"] in ("l1.read.reserved", "dax.r", "fs.r")]; loose_t.sort(key=lambda x: x[0])
    keys_t = [x[0] for x in loose_t]
    pf_sub = sorted((P["sub_t"], rid) for rid, P in pf.items() if "sub_t" in P); pf_t = [x[0] for x in pf_sub]; used = set()
    order = []
    for row, c in zip(rows, cl):
        r = req.get("cmpl-" + c["rid"] + "-0")
        if not r: continue
        t = {}; hashes = None
        for d in by_sid.get(r["irid"], []):
            if d["ev"] in ("mp.request.start", "mp.lookup_prefetch.start", "mp.lookup_prefetch.end", "mp.request.end"): t[d["ev"]] = d
            elif d["ev"] == "mp.lookup" and hashes is None: hashes = set(h[:16] for h in d.get("hashes") or [])
        if "mp.lookup_prefetch.start" in t and "mp.lookup_prefetch.end" in t: order.append((t["mp.lookup_prefetch.start"]["t"], row, c, t, hashes))
    order.sort(key=lambda x: x[0])
    for ls, row, c, t, hashes in order:
        le = t["mp.lookup_prefetch.end"]["t"]; l2tok = t["mp.lookup_prefetch.end"].get("l2_hit_tokens")
        if "mp.request.start" in t and "mp.request.end" in t and "cpu" in t["mp.request.start"]:
            row["lm_cpu_ms"] = (t["mp.request.end"]["cpu"] - t["mp.request.start"]["cpu"]) / 1e6
        t0 = c["send_mono_ns"] / 1e9; wms = lambda tw: (tw - off - t0) * 1000
        # L1 reads of this request's chunks, with their medium (by key when the lookup's hashes are known, else by time)
        i0 = bisect.bisect_left(keys_t, ls - 0.0005); i1 = bisect.bisect_right(keys_t, le + 0.0005)
        dram = dax = 0; copy = 0.0; first = last = None
        for tw, d in loose_t[i0:i1]:
            e = d["ev"]
            if e == "l1.read.reserved":
                b = d.get("bk", "")
                for k_, ch in zip(d.get("keys") or [], b):
                    if hashes is not None and k_[:16] not in hashes: continue
                    dram += ch == "D"; dax += ch == "X"
            else:
                copy += d["dt"] / 1e6; a_ = wms(tw); b_ = a_ + d["dt"] / 1e6
                first = a_ if first is None else min(first, a_); last = b_ if last is None else max(last, b_)
        row.update(l1_dram=dram, l1_dax=dax)
        if copy: row.update(media_copy_ms=copy, media_first_ms=first, media_last_ms=last)
        # the L2 prefetch request of this lookup: submitted inside the lookup window, loaded_count x chunk = the lookup's l2_hit_tokens
        j0 = bisect.bisect_left(pf_t, ls - 0.002); j1 = bisect.bisect_right(pf_t, le + 0.002); best = None
        for ts_, rid in pf_sub[j0:j1]:
            if rid in used: continue
            P = pf[rid]
            if l2tok is not None and P.get("loaded") is not None and P["loaded"] * chunk != l2tok: continue
            if best is None or abs(ts_ - ls) < abs(pf[best]["sub_t"] - ls): best = rid
        if best is not None:
            used.add(best); P = pf[best]
            if P["tasks"]:
                a_ = min(x[0] for x in P["tasks"]); b_ = max(x[1] for x in P["tasks"]); l2b = sum(x[2] for x in P["tasks"]); l2ms = (b_ - a_) * 1000
                row.update(l2_tasks=len(P["tasks"]), l2_load_ms=l2ms, l2_bytes=l2b, l2_chunks=sum(x[3] for x in P["tasks"]), l2_start_ms=wms(a_), l2_end_ms=wms(b_))
                if l2ms > 0: row["l2_GiBps"] = l2b / 2**30 / (l2ms / 1000)
    # GPU transfer phases, by transfer key "<irid>#n"
    ph = {}
    for d in recs:
        if d["ev"] != "mp.transfer.phase_samples": continue
        for s in d.get("samples") or []:
            irid = str(s[5]).rsplit("#", 1)[0]; a = ph.setdefault(irid, dict(st=0.0, sb=0, k=0.0, n=0, sst=0.0, sk=0.0))
            if s[1] == 0:                                   # retrieve direction
                if s[0] == 1: a["st"] += s[3]; a["sb"] += s[4]; a["n"] += 1
                else: a["k"] += s[3]
            else:
                if s[0] == 1: a["sst"] += s[3]
                else: a["sk"] += s[3]
    for row, c in zip(rows, cl):
        r = req.get("cmpl-" + c["rid"] + "-0")
        if not r or r["irid"] not in ph: continue
        a = ph[r["irid"]]
        if a["n"]:
            row.update(staging_ms=a["st"], staging_bytes=a["sb"], kernel_ms=a["k"], n_stage=a["n"])
            if a["st"] > 0: row["h2d_GiBps"] = a["sb"] / 2**30 / (a["st"] / 1000)
        if a["sst"] or a["sk"]: row.update(store_staging_ms=a["sst"], store_kernel_ms=a["sk"])
    return rows

def summarize(rows):
    keys = ["ttft_client_ms", "lookup_ms", "l2_load_ms", "l2_GiBps", "media_copy_ms", "retrieve_ms", "staging_ms", "h2d_GiBps", "kernel_ms", "kv_end_to_sched_ms", "prefill_ms", "lm_cpu_ms"]
    groups = {}
    for r in rows:
        if r["status"] != 200 or r["case"] in ("warm", "fill_store", "flush"): continue
        groups.setdefault((r["case"], r["L"]), []).append(r)
    head = ["case", "L", "n", "cached", "chunks DRAM / DAX / L2", "TTFT p50 (min–max)"] + [k.replace("_ms", " ms").replace("_", " ") for k in keys[1:]] + ["MiB"]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for (case, L), g in sorted(groups.items()):
        tt = [r["ttft_client_ms"] for r in g]; med = lambda k: (lambda v: fmt(q(v, .5)) if v else "-")([r[k] for r in g if r.get(k) is not None])
        cells = [case, str(L), str(len(g)), fmt(q([r["cached_tokens"] for r in g], .5)), f"{med('l1_dram')} / {med('l1_dax')} / {med('l2_chunks')}", f"{q(tt, .5):.1f} ({min(tt):.1f}–{max(tt):.1f})"]
        cells += [med(k) for k in keys[1:]]
        mb = [r["retrieve_bytes"] / 2**20 for r in g if r.get("retrieve_bytes")]; cells.append(fmt(q(mb, .5)) if mb else "-")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)

def analyze(out, tag):
    cl, req, steps_req, ev, off = load_run(out, tag)
    rows = [timeline(c, req, steps_req, ev, off) for c in cl]
    recs, mono_off = load_tier(out, tag)
    if recs and off is not None: enrich(rows, cl, req, recs, off, mono_off)
    return rows

if __name__ == "__main__":
    out = sys.argv[1]
    for tag in sys.argv[2:]:
        rows = analyze(out, tag); cols = COLS[:-1] + XCOLS + COLS[-1:]
        with open(f"{out}/{tag}-tier-timeline.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
            for r in rows: w.writerow({k: ("" if r.get(k) is None else (f"{r[k]:.3f}" if isinstance(r.get(k), float) else r.get(k))) for k in cols})
        s = f"## {tag}\n\n" + summarize(rows) + "\n"
        open(f"{out}/{tag}-tier-summary.md", "w").write(s); print(s)
