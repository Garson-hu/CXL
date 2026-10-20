#!/usr/bin/env python3
"""Historical reuse-pattern characterization (RQ1-B historical learning round, 2026-10-18). OFFLINE TRACE ANALYSIS of a
KV request trace: Mooncake jsonl (timestamp ms, input_length, hash_ids of 512-token blocks, prefix-chained) or an agent
trace jsonl exported by kv_agent_events.py (t_lookup, hashes of 256-token chunks, task). Everything is computed in trace
order; "history" statistics that are meant to be online are computed with past information only where stated.

A1 cross-request reuse: prefix-tree roots / groups at several depths, sharing of blocks across requests, reuse
   concentration, long-lived shared prefixes, per-group new-block reuse rates and their stability across halves.
A2 temporal: inter-reuse intervals (and their regularity per block), burstiness of arrivals, persistence of group /
   block popularity between consecutive windows, hot-to-cold transitions.
A3 conditional: new-block reuse rate by online-available context (group at depth d, position, request length,
   continuation depth, time since the previous request of the same chain); lift and coverage.
A4 reuse distance / pressure: next-use time and stack distance of reuses; LRU at several capacities: reuses that miss
   because the block was evicted (premature evictions), their history (past uses at eviction, age, group rate) and the
   lead a predictor could have had (last access -> eviction, eviction -> reuse).
usage: kv_history_characterize.py <trace> <out_dir> <tag> [--mooncake] [--block-mb 67.1] [--caps-gb 100,200,400]"""
import argparse, bisect, collections, json, os, statistics
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser(); ap.add_argument("trace"); ap.add_argument("out"); ap.add_argument("tag"); ap.add_argument("--mooncake", action="store_true")
ap.add_argument("--block-mb", type=float, default=67.1); ap.add_argument("--caps-gb", default="100,200,400"); ap.add_argument("--window-s", type=float, default=300)
A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.grid": True, "grid.color": "#e6e6e6", "legend.frameon": False, "svg.fonttype": "none"})
INF = float("inf")
def q(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else float("nan")
def spearman(a, b):
    n = len(a)
    if n < 3: return float("nan")
    ra = sorted(range(n), key=lambda i: a[i]); rb = sorted(range(n), key=lambda i: b[i]); pa = [0] * n; pb = [0] * n
    for k, i in enumerate(ra): pa[i] = k
    for k, i in enumerate(rb): pb[i] = k
    return 1 - 6 * sum((x - y) ** 2 for x, y in zip(pa, pb)) / (n * (n * n - 1))

# ------------------------------------------------------------------ load
R = []
for l in open(A.trace):
    r = json.loads(l)
    if A.mooncake: R.append(dict(t=r["timestamp"] / 1000.0, hs=[str(h) for h in r["hash_ids"]], L=r["input_length"], task=None))
    else:
        if r.get("task", 0) < 0: continue
        R.append(dict(t=r["t_lookup"], hs=list(r["hashes"]), L=len(r["hashes"]) * 256, task=r.get("task")))
R.sort(key=lambda r: r["t"]); T0 = R[0]["t"]; SPAN = R[-1]["t"] - T0; HALF = T0 + SPAN / 2
N = len(R); print(f"{A.tag}: {N} requests over {SPAN:.0f} s")
first = {}; uses = collections.defaultdict(list); users = collections.defaultdict(set); pos_at_first = {}
acc = []                                                                 # (t, h, ri, j)
for i, r in enumerate(R):
    for j, h in enumerate(r["hs"]):
        if h not in first: first[h] = i; pos_at_first[h] = j
        uses[h].append(r["t"]); users[h].add(i); acc.append((r["t"], h, i, j))
B = len(first); reused = {h for h in first if len(uses[h]) > 1}
out = dict(tag=A.tag, requests=N, span_s=SPAN, blocks=B, accesses=len(acc), reused_blocks=len(reused), never_share=1 - len(reused) / B)

# ------------------------------------------------------------------ A1 cross-request reuse
share = collections.Counter(min(len(users[h]), 10) for h in reused)
out["reused_blocks_by_distinct_requests"] = {str(k): v for k, v in sorted(share.items())}
# prefix groups at depths
groups = {}
for d in (1, 2, 3, 4, 8):
    G = collections.defaultdict(lambda: dict(req=0, new1=0, re1=0, new2=0, re2=0, first_t=INF, last_t=-INF))
    for i, r in enumerate(R):
        hs = r["hs"]
        if len(hs) < d: continue
        g = tuple(hs[:d]); e = G[g]; e["req"] += 1; e["first_t"] = min(e["first_t"], r["t"]); e["last_t"] = max(e["last_t"], r["t"]); k = "1" if r["t"] < HALF else "2"
        for j, h in enumerate(hs):
            if first[h] != i or j < d: continue
            e["new" + k] += 1; e["re" + k] += (h in reused)
    big = [(g, e) for g, e in G.items() if e["new1"] >= 100 and e["new2"] >= 100]
    r1 = [e["re1"] / e["new1"] for _, e in big]; r2 = [e["re2"] / e["new2"] for _, e in big]
    tot_new = sum(e["new1"] + e["new2"] for e in G.values())
    long_lived = sum(1 for e in G.values() if e["last_t"] - e["first_t"] > 0.5 * SPAN and e["req"] >= 10)
    groups[d] = dict(groups=len(G), big_groups=len(big), big_cover_new=sum(e["new1"] + e["new2"] for _, e in big) / max(1, tot_new), rate_p10=q(r1, .1), rate_p50=q(r1, .5), rate_p90=q(r1, .9),
                     spearman_halves=spearman(r1, r2), long_lived_groups=long_lived, top_groups=[dict(req=e["req"], new=e["new1"] + e["new2"], rate1=e["re1"] / max(1, e["new1"]), rate2=e["re2"] / max(1, e["new2"])) for _, e in sorted(big, key=lambda x: -x[1]["req"])[:5]])
out["prefix_groups_by_depth"] = {str(d): v for d, v in groups.items()}
# concentration of reuses
cnt = sorted((len(uses[h]) - 1 for h in reused), reverse=True); tot_re = sum(cnt)
out["reuse_concentration"] = {f"top_{p}pct_blocks_share_of_reuses": sum(cnt[:max(1, int(p / 100 * B))]) / max(1, tot_re) for p in (0.1, 1, 10)}
# long-lived shared blocks: used over > 50% of the span by >= 10 requests
out["long_lived_shared_blocks"] = sum(1 for h in reused if uses[h][-1] - uses[h][0] > 0.5 * SPAN and len(users[h]) >= 10)

# ------------------------------------------------------------------ A2 temporal
iv_all = []; cv = []
for h in reused:
    ts = uses[h]; iv = [b - a for a, b in zip(ts, ts[1:])]; iv_all.extend(iv)
    if len(iv) >= 3 and statistics.mean(iv) > 0: cv.append(statistics.pstdev(iv) / statistics.mean(iv))
out["inter_reuse_interval_s"] = dict(p10=q(iv_all, .1), p50=q(iv_all, .5), p90=q(iv_all, .9), n=len(iv_all))
out["interval_cv_blocks_ge4_uses"] = dict(n=len(cv), p25=q(cv, .25), p50=q(cv, .5), p75=q(cv, .75))
# burstiness: Fano factor of request counts per 10 s
bins = collections.Counter(int((r["t"] - T0) // 10) for r in R); counts = [bins.get(k, 0) for k in range(int(SPAN // 10) + 1)]
out["arrival_fano_10s"] = statistics.pvariance(counts) / max(1e-9, statistics.mean(counts))
# popularity persistence between consecutive windows: per block (reused ones) and per depth-2 group
W = A.window_s; nw = int(SPAN // W) + 1
def window_counts(keyf):
    C = [collections.Counter() for _ in range(nw)]
    for t, h, ri, j in acc:
        k = keyf(h, ri)
        if k is not None: C[int((t - T0) // W)][k] += 1
    return C
Cb = window_counts(lambda h, ri: h if h in reused else None)
rho_b = []; top_keep = []
for w in range(nw - 1):
    keys = set(Cb[w]) | set(Cb[w + 1])
    if len(keys) >= 10:
        a = [Cb[w].get(k, 0) for k in keys]; b = [Cb[w + 1].get(k, 0) for k in keys]; rho_b.append(spearman(a, b))
        top = [k for k, _ in Cb[w].most_common(100)]; nxt = set(k for k, _ in Cb[w + 1].most_common(100)); top_keep.append(sum(1 for k in top if k in nxt) / max(1, len(top)))
out["popularity_persistence_blocks"] = dict(window_s=W, spearman_consecutive_p50=q(rho_b, .5), top100_kept_next_window_p50=q(top_keep, .5), windows=len(rho_b))
# hot-to-cold: of blocks in the top-100 of a window, share never used again after that window
dead_after = []
for w in range(nw - 1):
    top = [k for k, _ in Cb[w].most_common(100)]
    if len(top) >= 20: dead_after.append(sum(1 for k in top if uses[k][-1] < T0 + (w + 1) * W) / len(top))
out["top100_blocks_dead_after_window_p50"] = q(dead_after, .5)

# ------------------------------------------------------------------ A3 conditional reuse of NEW blocks (creation-time, online-available context)
def lift_table(keyf, name, min_n=200):
    T = collections.defaultdict(lambda: [0, 0])
    for i, r in enumerate(R):
        for j, h in enumerate(r["hs"]):
            if first[h] != i: continue
            k = keyf(r, j, i); T[k][0] += 1; T[k][1] += (h in reused)
    base = sum(v[1] for v in T.values()) / max(1, sum(v[0] for v in T.values()))
    rows = {str(k): dict(n=v[0], rate=v[1] / v[0]) for k, v in T.items() if v[0] >= min_n}
    rates = [v["rate"] for v in rows.values()]
    out[name] = dict(base=base, cells=rows, spread_p10=q(rates, .1), spread_p90=q(rates, .9), max_lift=(max(rates) / base) if rates and base > 0 else float("nan"))
prev_t = {}                                                            # chain -> time of the previous request that extended it (online)
chain_prev = {}
for i, r in enumerate(R):
    hs = r["hs"]; key = hs[-1]; old = sum(1 for h in hs if first[h] != i)
    pv = chain_prev.get(tuple(hs[:old])) if old else None
    r["depth"] = old; r["gap"] = (r["t"] - pv) if pv is not None else None; chain_prev[tuple(hs)] = r["t"]
lift_table(lambda r, j, i: f"len{min(64, (r['L'] // 4096) * 8)}k", "cond_by_request_length")
lift_table(lambda r, j, i: f"pos{min(4, j // 8)}", "cond_by_position_bucket")
lift_table(lambda r, j, i: f"depth{min(3, r['depth'] // 8)}", "cond_by_continuation_depth")
lift_table(lambda r, j, i: "fresh" if r["gap"] is None else ("gap<60" if r["gap"] < 60 else "gap<300" if r["gap"] < 300 else "gap>=300"), "cond_by_time_since_previous_turn")
lift_table(lambda r, j, i: f"root{r['hs'][0][:6]}", "cond_by_root", min_n=500)
if not A.mooncake: lift_table(lambda r, j, i: f"task_call{min(5, r['hs'].count(r['hs'][0]))}", "cond_by_task", min_n=50)

# ------------------------------------------------------------------ A4 reuse distance / pressure (LRU at several capacities)
nu = [INF] * len(acc); last = {}
for i in range(len(acc) - 1, -1, -1):
    h = acc[i][1]; nu[i] = last.get(h, INF); last[h] = i
next_t = [acc[nu[i]][0] - acc[i][0] if nu[i] < INF else INF for i in range(len(acc))]
out["next_use_time_s_of_reuses"] = dict(p10=q([x for x in next_t if x < INF], .1), p50=q([x for x in next_t if x < INF], .5), p90=q([x for x in next_t if x < INF], .9))
caps = [int(float(c) * 1024 / A.block_mb) for c in A.caps_gb.split(",")]
prem = {}
for cap in caps:
    lru = collections.OrderedDict(); stored = {}; hits = 0; reuse_n = 0; premature = []; seen = set(); last_acc = {}; use_cnt = collections.Counter()
    for i, (t, h, ri, j) in enumerate(acc):
        re = h in seen; seen.add(h)
        if re: reuse_n += 1
        if h in lru: hits += re; lru.move_to_end(h)
        else:
            if len(lru) >= cap:
                v, _ = lru.popitem(last=False); stored.pop(v, None)
                if nu[last_acc[v]] < INF: premature.append((t - last_acc_t[v], acc[nu[last_acc[v]]][0] - t, use_cnt[v], j_of[v]))
            lru[h] = True
        last_acc[h] = i; use_cnt[h] += 1
        if "last_acc_t" not in dir(): last_acc_t = {}; j_of = {}
        last_acc_t[h] = t; j_of[h] = j
    prem[cap] = dict(cap_blocks=cap, cap_GB=cap * A.block_mb / 1024, reuse_hit_share=hits / max(1, reuse_n), premature_evictions=len(premature), share_of_reuses_missed=len(premature) / max(1, reuse_n),
                     lead_last_access_to_eviction_s=dict(p10=q([x[0] for x in premature], .1), p50=q([x[0] for x in premature], .5), p90=q([x[0] for x in premature], .9)),
                     eviction_to_reuse_s=dict(p10=q([x[1] for x in premature], .1), p50=q([x[1] for x in premature], .5), p90=q([x[1] for x in premature], .9)),
                     past_uses_at_eviction=dict((str(k), v) for k, v in sorted(collections.Counter(min(x[2], 5) for x in premature).items())),
                     share_with_past_reuse=sum(1 for x in premature if x[2] >= 2) / max(1, len(premature)))
out["lru_premature_evictions"] = {str(c): v for c, v in prem.items()}
json.dump(out, open(f"{A.out}/{A.tag}-history.json", "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k not in ("prefix_groups_by_depth", "cond_by_request_length", "cond_by_position_bucket", "cond_by_continuation_depth", "cond_by_time_since_previous_turn", "cond_by_root", "cond_by_task", "lru_premature_evictions")}, indent=1))
for k in ("cond_by_root", "cond_by_time_since_previous_turn", "cond_by_continuation_depth"):
    if k in out: print(k, "base", round(out[k]["base"], 3), {c: (v["n"], round(v["rate"], 3)) for c, v in out[k]["cells"].items()})
for c, v in prem.items(): print("LRU", v["cap_GB"], "GiB: reuse-hit", round(v["reuse_hit_share"], 3), "premature", v["premature_evictions"], "share of reuses missed", round(v["share_of_reuses_missed"], 3), "with past reuse", round(v["share_with_past_reuse"], 2), "lead last->evict p50", round(v["lead_last_access_to_eviction_s"]["p50"], 1), "evict->reuse p50", round(v["eviction_to_reuse_s"]["p50"], 1))
# figure: inter-reuse intervals, popularity persistence, premature eviction lead
fig, axs = plt.subplots(1, 3, figsize=(15, 4.2))
xs = sorted(x for x in iv_all if x > 0); axs[0].plot(xs, [i / len(xs) for i in range(1, len(xs) + 1)]); axs[0].set_xscale("log"); axs[0].set_xlabel("inter-reuse interval, s"); axs[0].set_ylabel("CDF"); axs[0].set_title(f"{A.tag}: time between uses of a block", fontsize=10)
axs[1].plot(range(len(rho_b)), rho_b, marker="o", label="Spearman of block popularity, window w vs w+1"); axs[1].plot(range(len(top_keep)), top_keep, marker="s", label="share of top-100 blocks still top-100 next window"); axs[1].set_xlabel(f"window ({W:.0f} s)"); axs[1].set_ylim(-0.1, 1.05); axs[1].legend(fontsize=8); axs[1].set_title("Popularity persistence", fontsize=10)
for cap, v in prem.items():
    pass
c0 = caps[len(caps) // 2]
lead = []
lru = collections.OrderedDict(); seen = set(); last_t = {}
for i, (t, h, ri, j) in enumerate(acc):
    if h in lru: lru.move_to_end(h)
    else:
        if len(lru) >= c0:
            v, _ = lru.popitem(last=False)
            if nu[last_i[v]] < INF: lead.append((t - last_t[v], acc[nu[last_i[v]]][0] - t))
        lru[h] = True
    if "last_i" not in dir(): last_i = {}
    last_i[h] = i; last_t[h] = t
if lead:
    xs = sorted(x for x, _ in lead); axs[2].plot(xs, [i / len(xs) for i in range(1, len(xs) + 1)], label="last access → eviction (the warning a predictor gets)")
    xs = sorted(y for _, y in lead if y > 0); axs[2].plot(xs, [i / len(xs) for i in range(1, len(xs) + 1)], label="eviction → the missed reuse")
axs[2].set_xscale("log"); axs[2].set_xlabel("seconds"); axs[2].set_ylabel("CDF"); axs[2].legend(fontsize=8); axs[2].set_title(f"LRU at {c0 * A.block_mb / 1024:.0f} GiB: premature evictions ({len(lead)})", fontsize=10)
fig.tight_layout(); fig.savefig(f"{A.out}/fig-history-{A.tag}.png", dpi=200); fig.savefig(f"{A.out}/fig-history-{A.tag}.svg"); print("wrote", f"{A.out}/fig-history-{A.tag}.png")
