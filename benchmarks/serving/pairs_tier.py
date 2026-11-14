#!/usr/bin/env python3
"""CXL-vs-NVMe study (2026-11-12), Experiment B: per-request comparisons between two replays of the same window, and the checks of
the sustained-overload round. Every replay of a window sends the same requests at the same instants, so request i of one run is
paired with request i of another (index = the last field of the request id). Reads <B>/<tag>-tier-requests.csv, <tag>-requests.csv,
<tag>-tier.json, <tag>-kvevents.jsonl (analyze_tier_replay.py, analyze_b.py, the kvtier hook). Prints; writes nothing.

usage: pairs_tier.py <B dir> <command> ...
  pair <tagA> <tagB> <t0,t1,...>      A - B per request, by send-time segment: TTFT, queued -> scheduled, prefill, lookup interval, request
                                      time (mean, median, share of requests faster in A); prefill of the requests with equal cached tokens
  cached <tagA> <tagB> <t0,t1,...>    requests with more cached tokens in A / in B per segment, their token sums and TTFT differences, and
                                      the TTFT difference of the requests with equal cached tokens
  l2pair <group> [other ...]          requests that loaded from the NVMe L2 (b-<group>-ssdn) and have the same cached tokens in the other
                                      configuration (default: hyb daxl2): NVMe load time, TTFT difference; the subset served without a queue
  l2direct <tag> ...                  L2 load time inside the cache server of EVERY prefetch that loaded a chunk (submitted -> load completed,
                                      keyed by the prefetch's own id: independent of the join of prefetches to lookups)
  overload <tag> [<tag at 0.08x>]     a saturated replay: completions during the arrival phase and after it, TTFT by quarter of the arrivals,
                                      cached share by source; against the same requests in the second run: who has more / fewer cached tokens
  lookups <tag> ...                   when the lookup of a request starts: send -> lookup, lookup -> first token (from the mp.lookup events)
  timed <tag> <host GiB> [pin=0] [lookup=send]
                                      a cache MODEL (not a measurement) driven by the measured times of a replay of the conversation window
                                      0-400 s: every request looks up at its measured lookup time (longest prefix of 512-token trace blocks in
                                      a host LRU of the given capacity; with pin, blocks found stay until the request is served), and stores
                                      its blocks when its first token is produced; the GPU pool (200 blocks, LRU in service order) can add a
                                      prefix at service time. lookup=send places the lookup at the send time instead."""
import csv, json, os, statistics as st, sys
from collections import OrderedDict

B = sys.argv[1].rstrip("/"); CMD = sys.argv[2]; ARGS = sys.argv[3:]
idx = lambda rid: rid.rsplit("-", 1)[1]
def tier(tag): return {idx(r["rid"]): r for r in csv.DictReader(open(f"{B}/{tag}-tier-requests.csv"))}
def full(tag):
    """tier-requests.csv joined with the time line of requests.csv"""
    t = tier(tag); d = {}
    for r in csv.DictReader(open(f"{B}/{tag}-requests.csv")):
        k = idx(r["rid"])
        if k in t: r["send_s"] = float(t[k]["send_s"]); d[k] = r
    return d
f = lambda r, k: float(r[k]) if r.get(k) not in (None, "") else None
def q(v, p):
    v = sorted(v); return v[min(len(v) - 1, int(round(p * (len(v) - 1))))] if v else float("nan")
def lookup_times(tag):
    """request index -> wall time of its first mp.lookup event"""
    lk = {}
    for line in open(f"{B}/{tag}-kvevents.jsonl"):
        if '"mp.lookup"' not in line: continue
        d = json.loads(line)
        if d.get("ev") != "mp.lookup": continue
        try: i = (d.get("sid") or "").split("-")[-3]; int(i)
        except Exception: continue
        lk.setdefault(i, d["t"])
    return lk

if CMD == "pair":
    A, Bt = ARGS[0], ARGS[1]; a = full(A); b = full(Bt); ks = [k for k in a if k in b]; edges = [float(x) for x in ARGS[2].split(",")]
    print(f"{A} - {Bt}: {len(ks)} requests")
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = [k for k in ks if lo <= a[k]["send_s"] < hi]; out = [f"send {lo:.0f}-{hi:.0f} s n={len(sel)}"]
        for col in ("ttft_client_ms", "queue_to_sched_ms", "prefill_ms", "lookup_ms", "total_ms"):
            dv = [f(a[k], col) - f(b[k], col) for k in sel if f(a[k], col) is not None and f(b[k], col) is not None]
            if not dv: continue
            base = [f(b[k], col) for k in sel if f(b[k], col) is not None]
            out.append(f"{col}: mean {st.mean(dv):+.0f} med {q(dv, .5):+.0f} ms, first faster {sum(1 for x in dv if x < 0) / len(dv):.2f} (base mean {st.mean(base):.0f})")
        same = [k for k in sel if a[k]["cached_tokens"] == b[k]["cached_tokens"] and f(a[k], "prefill_ms") and f(b[k], "prefill_ms")]
        dv = [f(a[k], "prefill_ms") - f(b[k], "prefill_ms") for k in same]; base = [f(b[k], "prefill_ms") for k in same]
        if dv: out.append(f"prefill, same cached tokens (n={len(same)}): sum diff {sum(dv) / 1e3:+.1f} s of {sum(base) / 1e3:.0f} s ({sum(dv) / sum(base) * 100:+.2f} %), med {q(dv, .5):+.1f} ms")
        print("  " + "\n     ".join(out))

elif CMD == "cached":
    A, Bt = ARGS[0], ARGS[1]; a = tier(A); b = tier(Bt); ks = [k for k in a if k in b]; edges = [float(x) for x in ARGS[2].split(",")]
    print(f"{A} - {Bt}: {len(ks)} requests; cached share {sum(f(a[k], 'cached_tokens') for k in ks) / sum(f(a[k], 'prompt_tokens') for k in ks):.4f} / {sum(f(b[k], 'cached_tokens') for k in ks) / sum(f(b[k], 'prompt_tokens') for k in ks):.4f}")
    for lo, hi in list(zip(edges[:-1], edges[1:])) + [(edges[0], edges[-1])]:
        sel = [k for k in ks if lo <= f(a[k], "send_s") < hi]; dc = {k: f(a[k], "cached_tokens") - f(b[k], "cached_tokens") for k in sel}; dt = {k: f(a[k], "ttft_ms") - f(b[k], "ttft_ms") for k in sel}
        more = [k for k in sel if dc[k] > 0]; less = [k for k in sel if dc[k] < 0]; same = [k for k in sel if dc[k] == 0]
        s = f"  send {lo:.0f}-{hi:.0f} s: n {len(sel)}; more cached in A: {len(more)} requests, +{sum(dc[k] for k in more):.0f} tok"
        if more: s += f" (first sent at {min(f(a[k], 'send_s') for k in more):.0f} s; TTFT A-B mean {st.mean(dt[k] for k in more):+.0f} ms, median {q([dt[k] for k in more], .5):+.0f})"
        s += f"; more cached in B: {len(less)}, {sum(dc[k] for k in less):.0f} tok"
        if less: s += f" (TTFT A-B mean {st.mean(dt[k] for k in less):+.0f} ms)"
        if same: s += f"; equal: {len(same)}, TTFT A-B mean {st.mean(dt[k] for k in same):+.0f} ms, median {q([dt[k] for k in same], .5):+.0f}"
        print(s)

elif CMD == "l2pair":
    g = ARGS[0]; a = tier(f"b-{g}-ssdn")
    for other in (ARGS[1:] or ["hyb", "daxl2"]):
        try: b = tier(f"b-{g}-{other}")
        except FileNotFoundError: continue
        ks = [k for k in a if k in b and float(a[k]["tok_l2"] or 0) > 0 and a[k]["cached_tokens"] == b[k]["cached_tokens"]]
        d = [float(a[k]["ttft_ms"]) - float(b[k]["ttft_ms"]) for k in ks]; l2 = [float(a[k]["l2_ms"]) for k in ks if a[k]["l2_ms"]]; tt = [float(b[k]["ttft_ms"]) for k in ks]
        print(f"{g}: requests that loaded from the NVMe L2 (same cached tokens in {other}): n={len(ks)}; NVMe load ms p50/p95/max {q(l2, .5):.0f}/{q(l2, .95):.0f}/{max(l2) if l2 else 0:.0f}; TTFT ssdn-{other} ms: median {q(d, .5):+.0f}, mean {st.mean(d):+.0f}, p10 {q(d, .1):+.0f}, p90 {q(d, .9):+.0f}; share slower on NVMe {sum(1 for x in d if x > 0) / len(d):.2f}; TTFT in {other} p50 {q(tt, .5):.0f} ms")
        sq = [k for k in ks if float(b[k]["ttft_ms"]) < 1000]
        if sq:
            d2 = [float(a[k]["ttft_ms"]) - float(b[k]["ttft_ms"]) for k in sq]; l22 = [float(a[k]["l2_ms"]) for k in sq if a[k]["l2_ms"]]
            print(f"     of these, TTFT < 1 s in {other}: n={len(sq)}; NVMe load p50 {q(l22, .5):.0f} ms; TTFT diff median {q(d2, .5):+.0f}, mean {st.mean(d2):+.0f} ms; TTFT {other} p50 {q([float(b[k]['ttft_ms']) for k in sq], .5):.0f} vs ssdn p50 {q([float(a[k]['ttft_ms']) for k in sq], .5):.0f}")

elif CMD == "l2direct":
    for t in ARGS:
        sub = {}; lat = []; ch = []; n_sub = nohit = 0
        for line in open(f"{B}/{t}-kvevents.jsonl"):
            if '"l2.prefetch.' not in line: continue
            d = json.loads(line); e = d["ev"]; r = d.get("request_id")
            if e == "l2.prefetch.lookup.submitted": sub[r] = d["t"]; n_sub += 1
            elif e == "l2.prefetch.load.completed" and r in sub:
                n = d.get("loaded_count") or 0
                if n > 0: lat.append((d["t"] - sub[r]) * 1e3); ch.append(n)
                else: nohit += 1
        big = [l for l, c in zip(lat, ch) if c >= 64]
        print(f"{t}: prefetches submitted {n_sub}, loaded >= 1 chunk {len(lat)} ({sum(ch) * 9 / 1024:.1f} GiB), none {nohit}; ms p50/p95/max {q(lat, .5):.0f}/{q(lat, .95):.0f}/{max(lat) if lat else 0:.0f}; >= 64 chunks: n {len(big)}, p50 {q(big, .5):.0f}")

elif CMD == "overload":
    t = ARGS[0]; J = json.load(open(f"{B}/{t}-tier.json")); R = {k: {c: (float(v) if v not in ("", None) and c != "rid" else v) for c, v in r.items()} for k, r in tier(t).items()}
    arr = max(r["send_s"] for r in R.values()); done = sorted(r["send_s"] + r["total_ms"] / 1e3 for r in R.values()); n_arr = sum(1 for d in done if d <= arr); last = done[-1]
    ok = sum(1 for r in R.values() if (r["out_tokens"] or 0) > 0); out_arr = sum(r["out_tokens"] for r in R.values() if r["send_s"] + r["total_ms"] / 1e3 <= arr)
    print(f"== {t}: {len(R)} requests, {ok} with output tokens; last arrival {arr:.0f} s, last completion {last:.0f} s")
    print(f"   completed during the arrival phase {n_arr} = {n_arr / arr:.3f} req/s (offered {len(R) / arr:.3f}); after it {len(R) - n_arr} in {last - arr:.0f} s = {(len(R) - n_arr) / (last - arr):.3f} req/s; whole run {len(R) / last:.3f} req/s")
    print(f"   output tok/s: arrival phase {out_arr / arr:.1f}, whole run {sum(r['out_tokens'] for r in R.values()) / last:.1f}; computed prompt tok/s {J['computed_tok_per_s']:.0f}; GPU busy {J['gpu_busy_steps']:.3f}; backlog max {J['backlog_max']}")
    tt = [r["ttft_ms"] / 1e3 for r in R.values()]; tot = [r["total_ms"] / 1e3 for r in R.values()]
    print(f"   TTFT p50/p95/p99/mean {q(tt, .5):.0f}/{q(tt, .95):.0f}/{q(tt, .99):.0f}/{st.mean(tt):.0f} s; request time p50/p95 {q(tot, .5):.0f}/{q(tot, .95):.0f} s")
    print(f"   cached {J['cached_share']:.3f} = GPU {J['share_gpu_prefix']:.3f} + DRAM {J['share_dram']:.3f} + CXL L1 {J['share_cxl_l1']:.3f} + L2 {J['share_l2']:.3f}; recomputed {J['tok_recomputed'] / 1e6:.2f} M; found at lookup {J['lookup_hit_tokens'] / 1e6:.3f} M tok (L1 {J['lookup_l1_hit_tokens'] / 1e6:.3f}, L2 {J['lookup_l2_hit_tokens'] / 1e6:.3f})")
    print(f"   L1 max / mean {J['l1_used_GB_max'] / 1.073741824:.1f} / {J['l1_used_GB_mean'] / 1.073741824:.1f} GiB; written DRAM / CXL {J['l1_write_dram_GiB']:.1f} / {J['l1_write_cxl_GiB']:.1f}, evicted {J['l1_evict_dram_GiB']:.1f} / {J['l1_evict_cxl_GiB']:.1f} GiB; L2 stored / loaded {J['l2_store_GiB']:.1f} / {J['l2_load_GiB']:.1f} GiB, L2 keys evicted {J['l2_evicted_keys']}")
    ks = sorted(R, key=lambda k: R[k]["send_s"]); m = len(ks) // 4
    for i in range(4):
        seg = [R[k] for k in ks[i * m:(i + 1) * m if i < 3 else len(ks)]]
        print(f"   arrivals {seg[0]['send_s']:.0f}-{seg[-1]['send_s']:.0f} s: n {len(seg)}, TTFT p50 {q([r['ttft_ms'] / 1e3 for r in seg], .5):.0f} s, cached share {sum(r['cached_tokens'] for r in seg) / sum(r['prompt_tokens'] for r in seg):.3f}")
    if len(ARGS) > 1:
        R8 = tier(ARGS[1]); J8 = json.load(open(f"{B}/{ARGS[1]}-tier.json"))
        more = [k for k in R if k in R8 and R[k]["cached_tokens"] > float(R8[k]["cached_tokens"])]; less = [k for k in R if k in R8 and R[k]["cached_tokens"] < float(R8[k]["cached_tokens"])]
        print(f"   against {ARGS[1]} (cached {J8['cached_share']:.3f} = GPU {J8['share_gpu_prefix']:.3f} + DRAM {J8['share_dram']:.3f} + CXL L1 {J8['share_cxl_l1']:.3f} + L2 {J8['share_l2']:.3f}; computed prompt tok/s {J8['computed_tok_per_s']:.0f}; {J8['req_per_s']:.3f} req/s):")
        print(f"      more cached tokens here: {len(more)} requests, +{sum(R[k]['cached_tokens'] - float(R8[k]['cached_tokens']) for k in more) / 1e6:.3f} M tok; fewer: {len(less)} requests, -{sum(float(R8[k]['cached_tokens']) - R[k]['cached_tokens'] for k in less) / 1e6:.3f} M tok")

elif CMD == "lookups":
    for t in ARGS:
        J = json.load(open(f"{B}/{t}-tier.json")); R = tier(t); lk = lookup_times(t); late = []; gap = []
        for k, r in R.items():
            if k not in lk: continue
            s = float(r["send_s"]); l = lk[k] - J["wall_start"]; late.append(l - s); gap.append(s + float(r["ttft_ms"]) / 1e3 - l)
        print(f"{t}: lookups of {len(late)} of {len(R)} requests; send -> lookup p50 / p90 / max {q(late, .5):.1f} / {q(late, .9):.1f} / {max(late):.1f} s; lookup -> first token p50 / p90 / max {q(gap, .5):.1f} / {q(gap, .9):.1f} / {max(gap):.1f} s; requests with more than 300 s / 600 s between lookup and first token: {sum(1 for g in gap if g > 300)} / {sum(1 for g in gap if g > 600)}")

elif CMD == "timed":
    tag, cap_gib = ARGS[0], float(ARGS[1]); pin = "pin=0" not in ARGS; at_send = "lookup=send" in ARGS
    here = os.path.dirname(os.path.abspath(__file__)); ns = {}; exec(open(os.path.join(here, "trace_reuse.py")).read().split('if __name__ == "__main__":')[0], ns)
    BPT, ML, GIB, GPU_BLOCKS = 36864, 31736, 2**30, 200; cap = int(cap_gib * GIB / (512 * BPT))
    reqs = ns["load"](dict(ns["TRACES"])["conv"], 0, 400, ML); R = {int(k): r for k, r in tier(tag).items()}; assert len(R) == len(reqs), (len(R), len(reqs))
    J = json.load(open(f"{B}/{tag}-tier.json")); lk = {} if at_send else {int(k): v - J["wall_start"] for k, v in lookup_times(tag).items()}
    ev = []
    for i in range(len(reqs)):
        s = float(R[i]["send_s"]); ev.append((lk.get(i, s), 0, i)); ev.append((s + float(R[i]["ttft_ms"]) / 1e3, 1, i))
    ev.sort(); host = OrderedDict(); pins = {}; gpu = OrderedDict(); found = {}; hit = hit_host = 0; tot = sum(n for _, _, n in reqs)
    for _, kind, i in ev:
        _, hs, n = reqs[i]
        if kind == 0:                                    # lookup: longest prefix of blocks in the host tier
            k = 0
            for h in hs:
                if h in host: k += 1
                else: break
            found[i] = k
            for h in hs[:k]:
                host.move_to_end(h)
                if pin: pins[h] = pins.get(h, 0) + 1
        else:                                            # service: count the hit, release the blocks, store the prompt
            k = found.get(i, 0); g = 0
            for h in hs:
                if h in gpu: g += 1
                else: break
            hit += min(n, max(k, g) * 512); hit_host += min(n, k * 512)
            if pin:
                for h in hs[:k]:
                    pins[h] -= 1
                    if not pins[h]: del pins[h]
            for h in hs: host[h] = 1; host.move_to_end(h); gpu[h] = 1; gpu.move_to_end(h)
            while len(gpu) > GPU_BLOCKS: gpu.popitem(last=False)
            if len(host) > cap:
                for h in list(host):
                    if len(host) <= cap: break
                    if h not in pins: del host[h]
    meas = sum(float(r["cached_tokens"]) for r in R.values()) / sum(float(r["prompt_tokens"]) for r in R.values())
    print(f"{tag}, host tier {cap_gib} GiB, pin={int(pin)}, lookup at {'send' if at_send else 'its measured time'}: MODEL cached share {hit / tot:.3f} (found in the host tier at lookup {hit_host / tot:.3f}); measured cached share {meas:.3f}")
else:
    sys.exit(__doc__)
