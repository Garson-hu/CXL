#!/usr/bin/env python3
"""CXL-vs-NVMe study (2026-11-12): tier-level summary of a trace replay (Experiments B and E).

On top of analyze_replay.py (hit shares as vLLM reports them, TTFT quantiles, throughput, GPU busy share, backlog) it reads the
kvtier hook's records (<tag>-kvevents.jsonl), the /status poll and the samplers and writes
  <out>/<tag>-tier.json      one record per run:
      tokens by source   gpu_prefix (vLLM's own prefix cache) / dram (L1 objects on DRAM) / cxl_l1 (L1 objects on Device-DAX) /
                         l2 (loaded from the L2 adapter for the request: CXL DAX slots or NVMe files) / recomputed
                         -- per retrieved chunk: the last chunks of the request's LMCache hit, with the medium LMCache reported for
                            each chunk at its read reservation (L1ObjectMeta.backend) or its L2 load
      lookup-level hits  l1_hit_tokens / l2_hit_tokens summed over the lookups (what LMCache found, used or not)
      bytes              L1 writes by medium, L1 evictions by medium, L2 stores / loads / evictions, GPU link H2D / D2H
      traffic (E)        per medium: bytes, busy seconds (union of the copy intervals), peak bytes in one second, and the seconds
                         during which a read copy and a write copy of the same medium were in flight at the same time
      memory             LMCache RSS (anon / shmem / file) maximum, system MemAvailable minimum, page cache growth, NVMe sectors
      CPU                CPU seconds of the LMCache and vLLM processes, busy share of their CPU sets
  <out>/<tag>-traffic.csv    per second of the replay: bytes read / written per medium, H2D / D2H bytes, L1 and L2 occupancy
  <out>/<tag>-tier-requests.csv   per request: tokens retrieved from DRAM / Device-DAX L1 / the L2 adapter, lookup-level hits, lookup time
and adds the run to <out>/tier-summary.csv.
Copy intervals: DAX L2 = the memmove of every chunk (dax.r / dax.w lines); Python file adapter = every O_DIRECT read / write (fs.r /
fs.w); native file adapter = its store / load tasks (submitted -> completed: includes queueing in the adapter) and, independently,
the block device's sector counters at 1 Hz; hybrid L1 = the GPU staging copies (TransferPhase.STAGING samples) of the stores and
retrieves whose L1 objects are on Device-DAX.
usage: analyze_tier_replay.py <out> <tag> [more tags ...]"""
import bisect, csv, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_replay
from analyze_a import q

CHUNK_TOK = 256

def union(iv):
    iv = sorted(iv); out = []
    for a, b in iv:
        if out and a <= out[-1][1]: out[-1][1] = max(out[-1][1], b)
        else: out.append([a, b])
    return out
def length(u): return sum(b - a for a, b in u)
def intersect(u, v):
    i = j = 0; s = 0.0
    while i < len(u) and j < len(v):
        a = max(u[i][0], v[j][0]); b = min(u[i][1], v[j][1])
        if b > a: s += b - a
        if u[i][1] < v[j][1]: i += 1
        else: j += 1
    return s

def tier_summary(out, tag):
    base = analyze_replay.summarize(out, tag)
    if base is None: return None
    S = dict(base); p = f"{out}/{tag}-kvevents.jsonl"
    cl = [json.loads(l) for l in open(f"{out}/{tag}-client.jsonl")]; tr = [c for c in cl if c["case"] == "trace" and c["status"] == 200]
    w0 = min(c["send_wall"] for c in tr); w1 = max(c["send_wall"] + c["total_ms"] / 1000 for c in tr); W = w1 - w0
    S.update(wall_start=w0, wall_s=W, out_tokens=sum(c["out_tokens"] for c in tr), out_tok_per_s=sum(c["out_tokens"] for c in tr) / W,
             total_ms_p95=q([c["total_ms"] for c in tr], .95), total_ms_p99=q([c["total_ms"] for c in tr], .99), total_ms_mean=sum(c["total_ms"] for c in tr) / len(tr))
    nsec = int(W) + 2; series = {k: [0] * nsec for k in ("cxl_r", "cxl_w", "nvme_r", "nvme_w", "dram_r", "dram_w", "h2d", "d2h")}
    iv = {k: [] for k in ("cxl_r", "cxl_w", "nvme_r", "nvme_w", "h2d", "d2h")}
    def add(kind, t0, t1, nbytes):
        if t1 < w0 or t0 > w1: return
        i = int(max(t0, w0) - w0)
        if 0 <= i < nsec: series[kind][i] += nbytes
        if kind in iv and t1 > t0: iv[kind].append((t0, t1))
    medium = {}                    # chunk key -> 'D' | 'X' | 'L' (last read reservation / L2 load)
    look = {}                      # sid -> dict(hashes, hit, l1, l2, ret_tok)
    tok = dict(dram=0, cxl_l1=0, l2=0, unknown=0); lk = dict(l1=0, l2=0, hit=0, n=0)
    by = dict(l1w_D=0, l1w_X=0, l1ev_D=0, l1ev_X=0, l2_store=0, l2_load=0, l2_evicted_keys=0, l2_store_tasks=0, l2_load_tasks=0, l2_store_failed=0)
    last_write_bk = ""; store_bk = {}; ret_frac = {}; samples = []; mono_off = None; l2name = ""; store_open = {}; load_open = {}
    mem = []; arenas = []; cpu_first = cpu_last = None; l2_busy_store = []; l2_busy_load = []
    if os.path.exists(p):
        for line in open(p):
            try: d = json.loads(line)
            except Exception: continue
            e = d["ev"]
            if e == "mem":
                mem.append(d)
                if cpu_first is None and "cpu" in d: cpu_first = d
                if "cpu" in d: cpu_last = d
                continue
            if mono_off is None and "t" in d and "tm" in d: mono_off = d["t"] - d["tm"] / 1e9
            if e in ("l1dax.arena", "l1dax.add"): arenas.append(d); continue
            sid = d.get("sid") or ""
            if e == "mp.lookup": look.setdefault(sid, {})["hashes"] = [h[:16] for h in d.get("hashes") or []]
            elif e == "mp.lookup_prefetch.start": look.setdefault(sid, {})["ls"] = d["t"]
            elif e == "mp.lookup_prefetch.end":
                L = look.setdefault(sid, {}); L.update(hit=d.get("hit_tokens") or 0, l1=d.get("l1_hit_tokens") or 0, l2=d.get("l2_hit_tokens") or 0, le=d["t"])
                if w0 <= d["t"] <= w1: lk["n"] += 1; lk["hit"] += L["hit"]; lk["l1"] += L["l1"]; lk["l2"] += L["l2"]
            elif e == "l1.read.reserved":
                for k, ch in zip(d.get("keys") or [], d.get("bk") or ""):
                    if ch in "DX": medium[k[:16]] = ch
            elif e == "l1.write_finished_and_read_reserved":
                for k in d.get("keys") or []: medium[k[:16]] = "L"
            elif e == "l1.write.finished":
                b = d.get("bk") or ""; last_write_bk = b; nb = d.get("nb") or 0; per = nb / len(b) if b else 0
                if w0 <= d["t"] <= w1: by["l1w_D"] += per * b.count("D"); by["l1w_X"] += per * b.count("X")
                add("dram_w", d["t"], d["t"], per * b.count("D"))
            elif e == "l1.keys.evicted":
                b = d.get("bk") or ""; nb = d.get("nb") or 0; per = nb / len(b) if b else 0
                if w0 <= d["t"] <= w1: by["l1ev_D"] += per * b.count("D"); by["l1ev_X"] += per * b.count("X")
            elif e == "mp.store.end": store_bk[d.get("transfer_key")] = last_write_bk
            elif e == "mp.retrieve.end":
                L = look.get(sid) or {}; n_ret = int(round((d.get("num_tokens") or 0) / CHUNK_TOK)); hs = L.get("hashes") or []; hit_ch = (L.get("hit") or 0) // CHUNK_TOK
                done = L.get("ret_done", 0); hi = max(0, hit_ch - done); lo = max(0, hi - n_ret); L["ret_done"] = done + n_ret     # several retrieves: from the end backwards
                cnt = dict(D=0, X=0, L=0, U=0)
                for k in hs[lo:hi]: cnt[medium.get(k, "U")] += 1
                cnt["U"] += n_ret - (hi - lo)
                if w0 <= d["t"] <= w1:
                    tok["dram"] += cnt["D"] * CHUNK_TOK; tok["cxl_l1"] += cnt["X"] * CHUNK_TOK; tok["l2"] += cnt["L"] * CHUNK_TOK; tok["unknown"] += cnt["U"] * CHUNK_TOK
                ret_frac[d.get("transfer_key")] = cnt["X"] / n_ret if n_ret else 0.0
                for k_ in "DXLU": L[k_] = L.get(k_, 0) + cnt[k_]
                L["ret_bytes"] = L.get("ret_bytes", 0) + (d.get("total_bytes") or 0); L["ret_end"] = d["t"]
                per = (d.get("total_bytes") or 0) / n_ret if n_ret else 0
                add("dram_r", d["t"], d["t"], per * (cnt["D"] + cnt["L"]))      # the GPU reads L2-loaded chunks from their DRAM L1 objects
            elif e == "mp.transfer.phase_samples":
                for s in d.get("samples") or []:
                    if s[0] == 1: samples.append(s)
            elif e == "l2.store.submitted": store_open[(d.get("adapter_index"), d.get("task_id"))] = d; l2name = d.get("l2_name") or l2name
            elif e == "l2.store.completed":
                s = store_open.pop((d.get("adapter_index"), d.get("task_id")), None)
                if w0 <= d["t"] <= w1: by["l2_store"] += d.get("bytes_transferred") or 0; by["l2_store_tasks"] += 1; by["l2_store_failed"] += d.get("failed_count") or 0
                if s: l2_busy_store.append((s["t"], d["t"], d.get("bytes_transferred") or 0))
            elif e == "l2.load_task.submitted": load_open[(d.get("adapter_index"), d.get("task_id"))] = d; l2name = d.get("l2_name") or l2name
            elif e == "l2.load_task.completed":
                s = load_open.pop((d.get("adapter_index"), d.get("task_id")), None)
                if s:
                    if w0 <= d["t"] <= w1: by["l2_load"] += s.get("total_bytes") or 0; by["l2_load_tasks"] += 1
                    l2_busy_load.append((s["t"], d["t"], s.get("total_bytes") or 0))
            elif e in ("l2.keys.evicted", "l2.keys.deleted"):
                if w0 <= d.get("t", 0) <= w1: by["l2_evicted_keys"] += len(d.get("keys") or [])
            elif e in ("dax.r", "dax.w"):
                t0 = d["t0"] / 1e9 + (mono_off or 0); add("cxl_r" if e == "dax.r" else "cxl_w", t0, t0 + d["dt"] / 1e9, d["n"])
            elif e in ("fs.r", "fs.w"):
                t0 = d["t0"] / 1e9 + (mono_off or 0); add("nvme_r" if e == "fs.r" else "nvme_w", t0, t0 + d["dt"] / 1e9, max(0, d["n"]))
    # GPU staging copies: H2D / D2H; the share of each that touches Device-DAX L1 objects
    for s in samples:
        ph, direction, _, ms, nbytes, key, t0, t1 = s[:8]
        if direction == 0:
            add("h2d", t0, t1, nbytes); f = ret_frac.get(key, 0.0)
            if f > 0: add("cxl_r", t0, t1, nbytes * f)
        else:
            add("d2h", t0, t1, nbytes); b = store_bk.get(key, ""); f = b.count("X") / len(b) if b else 0.0
            if f > 0: add("cxl_w", t0, t1, nbytes * f)
    native = "native" in l2name.lower() or (by["l2_load_tasks"] and not iv["nvme_r"] and not iv["cxl_r"] and "dax" not in l2name.lower())
    if native:                     # C++ file adapter: its task intervals stand in for the per-chunk I/O intervals
        for t0, t1, n in l2_busy_store: add("nvme_w", t0, t1, n)
        for t0, t1, n in l2_busy_load: add("nvme_r", t0, t1, n)
    S["l2_name"] = l2name
    prompt = S["prompt_tokens"]; cached = S["cached_share"] * prompt; host = tok["dram"] + tok["cxl_l1"] + tok["l2"] + tok["unknown"]
    S.update(tok_gpu_prefix=cached - host, tok_dram=tok["dram"], tok_cxl_l1=tok["cxl_l1"], tok_l2=tok["l2"], tok_unknown=tok["unknown"], tok_recomputed=prompt - cached,
             share_gpu_prefix=(cached - host) / prompt, share_dram=tok["dram"] / prompt, share_cxl_l1=tok["cxl_l1"] / prompt, share_l2=tok["l2"] / prompt, share_unknown=tok["unknown"] / prompt,
             share_recomputed=1 - cached / prompt, lookup_l1_hit_tokens=lk["l1"], lookup_l2_hit_tokens=lk["l2"], lookup_hit_tokens=lk["hit"])
    G = 2**30
    S.update(l1_write_dram_GiB=by["l1w_D"] / G, l1_write_cxl_GiB=by["l1w_X"] / G, l1_evict_dram_GiB=by["l1ev_D"] / G, l1_evict_cxl_GiB=by["l1ev_X"] / G,
             l2_store_GiB=by["l2_store"] / G, l2_load_GiB=by["l2_load"] / G, l2_store_tasks=by["l2_store_tasks"], l2_load_tasks=by["l2_load_tasks"], l2_evicted_keys=by["l2_evicted_keys"], l2_store_failed=by["l2_store_failed"])
    for k in ("cxl_r", "cxl_w", "nvme_r", "nvme_w", "h2d", "d2h"):
        u = union(iv[k]); S[f"{k}_GiB"] = sum(series[k]) / G; S[f"{k}_busy_s"] = length(u); S[f"{k}_peak_GiB_s"] = max(series[k]) / G if series[k] else 0
        S[f"{k}_busy_GiBps"] = S[f"{k}_GiB"] / S[f"{k}_busy_s"] if S[f"{k}_busy_s"] > 0 else None
        iv[k] = u
    S["cxl_rw_overlap_s"] = intersect(iv["cxl_r"], iv["cxl_w"]); S["nvme_rw_overlap_s"] = intersect(iv["nvme_r"], iv["nvme_w"]); S["h2d_d2h_overlap_s"] = intersect(iv["h2d"], iv["d2h"])
    S["cxl_rw_same_second"] = sum(1 for a, b in zip(series["cxl_r"], series["cxl_w"]) if a > 0 and b > 0); S["nvme_rw_same_second"] = sum(1 for a, b in zip(series["nvme_r"], series["nvme_w"]) if a > 0 and b > 0)
    # memory, block device, CPU
    mw = [m for m in mem if w0 - 2 <= m["t"] <= w1 + 2]
    if mw:
        S.update(lm_rss_anon_GiB_max=max(m.get("RssAnon", 0) for m in mw) / 2**20, lm_rss_shmem_GiB_max=max(m.get("RssShmem", 0) for m in mw) / 2**20, lm_rss_file_GiB_max=max(m.get("RssFile", 0) for m in mw) / 2**20,
                 lm_rss_GiB_max=max(m.get("VmRSS", 0) for m in mw) / 2**20, mem_available_GiB_min=min(m.get("MemAvailable", 0) for m in mw) / 2**20, mem_available_GiB_first=mw[0].get("MemAvailable", 0) / 2**20,
                 page_cache_growth_GiB=(max(m.get("Cached", 0) - m.get("Shmem", 0) for m in mw) - (mw[0].get("Cached", 0) - mw[0].get("Shmem", 0))) / 2**20,
                 dirty_GiB_max=max(m.get("Dirty", 0) + m.get("Writeback", 0) for m in mw) / 2**20)
        if "rd_sec" in mw[0]:
            S.update(nvme_dev_read_GiB=(mw[-1]["rd_sec"] - mw[0]["rd_sec"]) * 512 / G, nvme_dev_write_GiB=(mw[-1]["wr_sec"] - mw[0]["wr_sec"]) * 512 / G)
            pr = [(b["rd_sec"] - a["rd_sec"]) * 512 / max(1e-3, b["t"] - a["t"]) for a, b in zip(mw, mw[1:])]; pw = [(b["wr_sec"] - a["wr_sec"]) * 512 / max(1e-3, b["t"] - a["t"]) for a, b in zip(mw, mw[1:])]
            if pr: S.update(nvme_dev_read_peak_GiBps=max(pr) / G, nvme_dev_write_peak_GiBps=max(pw) / G)
        if "cpu" in mw[0]: S["lm_cpu_s"] = (mw[-1]["cpu"] - mw[0]["cpu"]) / 1e9; S["lm_cpu_cores"] = S["lm_cpu_s"] / (mw[-1]["t"] - mw[0]["t"]) if mw[-1]["t"] > mw[0]["t"] else None
    S["arenas"] = [dict(dev=a.get("dev"), GiB=(a.get("size") or 0) / G, pinned=a.get("pinned")) for a in arenas if a["ev"] == "l1dax.arena"]
    # CPU sampler: busy share of the CPU sets, process CPU seconds, vLLM RSS
    p = f"{out}/{tag}-cpu.txt"
    if os.path.exists(p):
        off = None; g = {}; pr = {}; tm0 = min(c["send_mono_ns"] for c in tr); tm1 = max(c["end_mono_ns"] for c in tr)
        for l in open(p):
            f = l.split()
            if not f or f[0] not in "GP" or len(f) < 4: continue
            t = int(f[1])
            if not tm0 <= t <= tm1: continue
            if f[0] == "G": g.setdefault(f[2], []).append(float(f[3]))
            else: pr.setdefault(f[2], []).append((t, float(f[3]), float(f[4]) if len(f) > 4 else 0.0))
        for name, v in g.items(): S[f"cpu_busy_{name}"] = sum(v) / len(v)
        vc = 0.0; vr = 0.0
        for name, v in pr.items():
            if name.startswith("vllm"): vc += v[-1][1] - v[0][1]; vr += max(x[2] for x in v) / 1024      # API server + engine core (its child processes)
            else: S[f"cpu_s_{name}"] = v[-1][1] - v[0][1]; S[f"rss_GiB_max_{name}"] = max(x[2] for x in v) / 1024
        S["cpu_s_vllm"] = vc; S["rss_GiB_max_vllm"] = vr
    # occupancy from the /status poll
    p = f"{out}/{tag}-status.txt"; occ = []
    if os.path.exists(p):
        tm0 = min(c["send_mono_ns"] for c in tr); tm1 = max(c["end_mono_ns"] for c in tr); wm = w0 - tm0 / 1e9
        for l in open(p):
            if not l.startswith("S "): continue
            try:
                t, js = l[2:].split(" ", 1); t = int(t); d = json.loads(js)
            except Exception: continue
            if not tm0 - 5e9 <= t <= tm1 + 5e9: continue
            sm = d["storage_manager"]; m = sm["l1_manager"]; ad = (sm.get("l2_eviction_controller") or {}).get("adapters") or []
            l2u = ad[0].get("total_bytes_used") if ad else None; l2c = ad[0].get("total_capacity_bytes") if ad else None
            if l2u is None:
                for a in sm.get("l2_adapters") or []:
                    if "live_slot_count" in a: l2u = a["live_slot_count"] * a.get("slot_bytes", 0); l2c = a.get("max_dax_size_bytes")
            occ.append((t / 1e9 + wm, m["memory_used_bytes"], m["memory_total_bytes"], l2u, l2c, m["total_object_count"]))
        if occ:
            S.update(l1_used_GiB_max=max(o[1] for o in occ) / G, l1_total_GiB=occ[-1][2] / G, l1_used_GiB_end=occ[-1][1] / G)
            if occ[-1][3] is not None: S.update(l2_used_GiB_max=max(o[3] or 0 for o in occ) / G, l2_used_GiB_end=(occ[-1][3] or 0) / G, l2_capacity_GiB=(occ[-1][4] or 0) / G)
    with open(f"{out}/{tag}-traffic.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["second", "cxl_read_bytes", "cxl_write_bytes", "nvme_read_bytes", "nvme_write_bytes", "dram_read_bytes", "dram_write_bytes", "h2d_bytes", "d2h_bytes", "l1_used_bytes", "l2_used_bytes"])
        ot = [o[0] - w0 for o in occ]
        for i in range(nsec):
            j = bisect.bisect_right(ot, i) - 1; o = occ[j] if j >= 0 else None
            w.writerow([i] + [int(series[k][i]) for k in ("cxl_r", "cxl_w", "nvme_r", "nvme_w", "dram_r", "dram_w", "h2d", "d2h")] + [o[1] if o else "", (o[3] if o and o[3] is not None else "")])
    # per request: tokens by host medium, lookup-level hits, lookup time (to be joined with <tag>-requests.csv by rid)
    by_rid = {}
    for sid, L in look.items():
        if sid.startswith("cmpl-"): by_rid[sid[5:].rsplit("-", 2)[0]] = L
    with open(f"{out}/{tag}-tier-requests.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["rid", "send_s", "prompt_tokens", "cached_tokens", "out_tokens", "ttft_ms", "total_ms", "tok_dram", "tok_cxl_l1", "tok_l2", "tok_unknown", "lookup_hit_tokens", "lookup_l1_tokens", "lookup_l2_tokens", "lookup_ms", "retrieve_bytes"])
        for c in tr:
            L = by_rid.get(c["rid"], {})
            w.writerow([c["rid"], round(c["send_wall"] - w0, 3), c["prompt_tokens"], c["cached_tokens"], c["out_tokens"], round(c["ttft_ms"], 2), round(c["total_ms"], 2), L.get("D", 0) * CHUNK_TOK, L.get("X", 0) * CHUNK_TOK, L.get("L", 0) * CHUNK_TOK,
                        L.get("U", 0) * CHUNK_TOK, L.get("hit", ""), L.get("l1", ""), L.get("l2", ""), (round((L["le"] - L["ls"]) * 1000, 2) if "le" in L and "ls" in L else ""), L.get("ret_bytes", 0)])
    json.dump(S, open(f"{out}/{tag}-tier.json", "w"), indent=1)
    return S

if __name__ == "__main__":
    out = sys.argv[1]; rows = {}
    p = f"{out}/tier-summary.csv"
    if os.path.exists(p):
        for r in csv.DictReader(open(p)): rows[r["tag"]] = r
    for tag in sys.argv[2:]:
        s = tier_summary(out, tag)
        if not s: print(tag, "no completed trace requests"); continue
        rows[tag] = {k: ("" if v is None else (json.dumps(v) if isinstance(v, (list, dict)) else v)) for k, v in s.items()}
        print(f"{tag}: n {s['n_ok']}/{s['n']} cached {s['cached_share']:.3f} = gpu {s['share_gpu_prefix']:.3f} + dram {s['share_dram']:.3f} + cxl-L1 {s['share_cxl_l1']:.3f} + L2 {s['share_l2']:.3f} (+ unknown {s['share_unknown']:.3f}); "
              f"TTFT p50/p95/p99/mean {s['ttft_p50']:.0f}/{s['ttft_p95']:.0f}/{s['ttft_p99']:.0f}/{s['ttft_mean']:.0f} ms; {s['req_per_s']:.3f} req/s; L1 max {s.get('l1_used_GiB_max', 0):.1f} GiB, L2 max {s.get('l2_used_GiB_max') or 0:.1f} GiB; "
              f"CXL r/w {s['cxl_r_GiB']:.1f}/{s['cxl_w_GiB']:.1f} GiB (overlap {s['cxl_rw_overlap_s']:.2f} s), NVMe r/w {s['nvme_r_GiB']:.1f}/{s['nvme_w_GiB']:.1f} GiB; LMCache RSS max {s.get('lm_rss_GiB_max') or 0:.1f} GiB")
    keys = sorted({k for r in rows.values() for k in r}, key=lambda k: (k != "tag", k))
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
        for t in sorted(rows): w.writerow({k: rows[t].get(k, "") for k in keys})
