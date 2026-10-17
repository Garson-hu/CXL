#!/usr/bin/env python3
"""Phase 1, Step 1 of the research charter (2026-10-17): reuse structure and predictability of KV blocks in the Mooncake
traces (conversation, toolagent, synthetic; 512-token hash blocks). TRACE SIMULATION on exact trace counts; the only
model assumption is the block size used to express stack distances in GiB (Llama-3.1-8B: 64 MiB per block).

Per trace, in order:
  blocks      distinct blocks; never reused (by count and bytes; also for blocks created in the first half of the span,
              which removes most of the end-of-trace effect); reuse-count classes and the share of reuses they carry;
              concentration (share of reuses on the top 0.1 / 1 / 10% of blocks by reuse count)
  timing      time between consecutive uses of a block; time from creation to second use; lifetime (first to last use);
              horizon = share of reuses whose next use lies within 60 / 300 / 900 / 1800 / 3600 s
  distance    exact LRU stack distance of every reuse (distinct blocks touched since the previous use), in blocks and GiB
  creation    P(reused later | feature known when the block is created): position of the block in the request, request
              length in blocks, continuation depth (leading blocks of the request that already existed = a continued
              conversation), number of new blocks the request creates; each with the share of blocks in the bucket, so
              the lift over the base rate is visible; fitted on the first half of the requests, checked on the second half
  resident    P(used again | past reuse count) and P(used again | time since last use) — what eviction can know
Outputs (out_dir): characterization-<trace>.json (all numbers), characterization-summary.txt, figures fig-*.png/.svg.
usage: kv_reuse_characterization.py [out_dir=experimental_results/2026-10-17-kv-reuse-oracle-study]
"""
import bisect, collections, json, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "experimental_results", "2026-10-17-kv-reuse-oracle-study")
os.makedirs(OUT, exist_ok=True)
TRACES = ["conversation", "toolagent", "synthetic"]; BLOCK_MIB = 64; HORIZONS = [60, 300, 900, 1800, 3600]
COL = {"conversation": "#1f77b4", "toolagent": "#2ca02c", "synthetic": "#9467bd"}
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.grid": True, "grid.color": "#e6e6e6", "legend.frameon": False, "svg.fonttype": "none"})
SUM = open(os.path.join(OUT, "characterization-summary.txt"), "w")
def say(s=""): print(s); SUM.write(s + "\n")
def q(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else float("nan")
def bucket(v, edges, labels): return labels[bisect.bisect_left(edges, v)]   # edges = inclusive upper bounds of the first len(edges) buckets
def save(fig, name):
    fig.tight_layout(); fig.savefig(os.path.join(OUT, name + ".png"), dpi=200); fig.savefig(os.path.join(OUT, name + ".svg")); plt.close(fig)

def load(trace):
    reqs = []
    for l in open(os.path.join(REPO, "workloads", f"mooncake_{trace}_trace.jsonl")):
        r = json.loads(l); reqs.append((r["timestamp"] / 1000.0, r["hash_ids"], r["input_length"], r["output_length"]))
    return reqs

class Fenwick:
    def __init__(self, n): self.n = n; self.t = [0] * (n + 1)
    def add(self, i, v):
        i += 1
        while i <= self.n: self.t[i] += v; i += i & -i
    def sum(self, i):                       # sum of [0, i)
        s = 0
        while i > 0: s += self.t[i]; i -= i & -i
        return s

R = {}
for trace in TRACES:
    reqs = load(trace); span = reqs[-1][0] - reqs[0][0]; half = reqs[0][0] + span / 2
    uses = collections.defaultdict(list)                       # block -> [(time, access index)]
    acc = []                                                   # (time, block, req index, position, req_len)
    seen = set(); cont_depth = []; new_blocks = []
    for ri, (t, hs, il, ol) in enumerate(reqs):
        d = 0
        for h in hs:
            if h in seen: d += 1
            else: break
        cont_depth.append(d); nb = sum(1 for h in hs if h not in seen); new_blocks.append(nb)
        for pos, h in enumerate(hs):
            uses[h].append((t, len(acc))); acc.append((t, h, ri, pos, len(hs))); seen.add(h)
    N = len(acc); nblk = len(uses)
    # --- blocks
    cnt = {h: len(u) for h, u in uses.items()}; never = sum(1 for c in cnt.values() if c == 1)
    first_half = [h for h, u in uses.items() if u[0][0] < half]; never_fh = sum(1 for h in first_half if cnt[h] == 1)
    reuses = N - nblk
    classes = [("1 (never reused)", 1, 1), ("2", 2, 2), ("3–4", 3, 4), ("5–9", 5, 9), ("10–99", 10, 99), ("100+", 100, 10**9)]
    cls = {lab: (sum(1 for c in cnt.values() if lo <= c <= hi), sum(c - 1 for c in cnt.values() if lo <= c <= hi)) for lab, lo, hi in classes}
    by_cnt = sorted(cnt.values(), reverse=True)
    conc = {p: sum(c - 1 for c in by_cnt[: max(1, int(p * nblk))]) / max(1, reuses) for p in (0.001, 0.01, 0.1)}
    # --- timing
    gaps, first_gap, life = [], [], []
    for h, u in uses.items():
        if len(u) > 1:
            first_gap.append(u[1][0] - u[0][0]); life.append(u[-1][0] - u[0][0])
            for a, b in zip(u, u[1:]): gaps.append(b[0] - a[0])
    horizon = {H: sum(1 for g in gaps if g <= H) / max(1, len(gaps)) for H in HORIZONS}
    # --- stack distance (exact) for every reuse
    fw = Fenwick(N); last = {}; sd = []
    for i, (t, h, ri, pos, L) in enumerate(acc):
        if h in last:
            p = last[h]; sd.append(fw.sum(i) - fw.sum(p + 1)); fw.add(p, -1)
        fw.add(i, 1); last[h] = i
    sd_gib = [d * BLOCK_MIB / 1024 for d in sd]
    # --- creation-time features: P(reused later | bucket), fitted on the first half of the requests, checked on the second
    pos_edges, pos_lab = [0, 3, 15, 63], ["0", "1–3", "4–15", "16–63", "64+"]
    len_edges, len_lab = [8, 32, 64], ["≤8", "9–32", "33–64", "65+"]
    dep_edges, dep_lab = [0, 7, 31], ["0 (fresh)", "1–7", "8–31", "32+"]
    nb_edges, nb_lab = [1, 4, 16], ["1", "2–4", "5–16", "17+"]
    feats = {"position in request": (pos_edges, pos_lab), "request length (blocks)": (len_edges, len_lab), "continuation depth (leading old blocks)": (dep_edges, dep_lab), "new blocks in the request": (nb_edges, nb_lab)}
    creation = {}
    for fname, (edges, labs) in feats.items():
        tab = {lab: [0, 0, 0, 0] for lab in labs}                  # [n_first, reused_first, n_second, reused_second]
        for h, u in uses.items():
            t0, i0 = u[0]; t_, h_, ri, pos, L = acc[i0]
            v = pos if fname.startswith("position") else L if fname.startswith("request length") else cont_depth[ri] if fname.startswith("continuation") else new_blocks[ri]
            b = bucket(v, edges, labs); k = 0 if t0 < half else 2
            tab[b][k] += 1; tab[b][k + 1] += (cnt[h] > 1)
        creation[fname] = {lab: dict(n1=v[0], p1=v[1] / v[0] if v[0] else None, n2=v[2], p2=v[3] / v[2] if v[2] else None) for lab, v in tab.items()}
    # --- conversation-chain features at request time (ONLINE: a serving system knows its sessions). previous turn = the request
    #     that created the last old block of this request's prefix; "fresh" = no prefix beyond the shared system block(s)
    creator = {}; turns = []; prev_gap = []; shared_first = {h for h, n in collections.Counter(r[1][0] for r in reqs if r[1]).items() if n >= 100}
    for ri, (t, hs, il, ol) in enumerate(reqs):
        d = cont_depth[ri]; k = d
        while k > 0 and hs[k - 1] in shared_first: k -= 1              # ignore shared system blocks for the chain
        if k == 0: turns.append(0); prev_gap.append(None)
        else:
            pr = creator[hs[k - 1]]; turns.append(turns[pr] + 1); prev_gap.append(t - reqs[pr][0])
        for h in hs:
            if h not in creator: creator[h] = ri
    newblk_reused = {}                                                   # request -> (n_new, n_new reused later, n_new reused within 300 s)
    for h, u in uses.items():
        ri = creator[h]; a = newblk_reused.setdefault(ri, [0, 0, 0]); a[0] += 1; a[1] += (len(u) > 1); a[2] += (len(u) > 1 and u[1][0] - u[0][0] <= 300)
    chain = {}
    for fname, edges, labs, val in [("turns so far", [0, 1, 2, 4], ["0 (fresh)", "1", "2", "3–4", "5+"], lambda ri: turns[ri]),
                                    ("time since previous turn", [30, 120, 300, 900], ["<30 s", "30–120 s", "120–300 s", "300–900 s", ">900 s"], lambda ri: prev_gap[ri]),
                                    ("answer length (tokens; known after the request)", [50, 200, 500], ["≤50", "51–200", "201–500", "500+"], lambda ri: reqs[ri][3]),
                                    ("prompt length (tokens)", [2000, 8000, 16000], ["≤2k", "2–8k", "8–16k", "16k+"], lambda ri: reqs[ri][2])]:
        tab = {lab: [0, 0, 0, 0, 0, 0] for lab in labs}                 # n_new blocks first/second half, reused, reused within 300 s
        for ri, (t, hs, il, ol) in enumerate(reqs):
            v = val(ri)
            if v is None or ri not in newblk_reused: continue
            b = bucket(v, edges, labs); k = 0 if t < half else 3; nn, nr, nr3 = newblk_reused[ri]
            tab[b][k] += nn; tab[b][k + 1] += nr; tab[b][k + 2] += nr3
        chain[fname] = {lab: dict(n1=v[0], p1=v[1] / v[0] if v[0] else None, p1_300=v[2] / v[0] if v[0] else None, n2=v[3], p2=v[4] / v[3] if v[3] else None, p2_300=v[5] / v[3] if v[3] else None) for lab, v in tab.items()}
    # --- resident-block features: P(used again | past reuse count), P(used again | time since last use)
    k_edges, k_lab = [0, 1, 2, 4], ["0", "1", "2", "3–4", "5+"]
    again_k = {lab: [0, 0] for lab in k_lab}
    for h, u in uses.items():
        for j in range(len(u)): again_k[bucket(j, k_edges, k_lab)][0] += 1; again_k[bucket(j, k_edges, k_lab)][1] += (j + 1 < len(u))
    a_edges, a_lab = [60, 300, 900, 1800], ["<60 s", "60–300 s", "300–900 s", "900–1800 s", ">1800 s"]
    again_a = {lab: [0, 0] for lab in a_lab}        # for every use, evaluate at ages after it: the block is "resident with age a"; used again later?
    for h, u in uses.items():
        for j, (t, i) in enumerate(u):
            nxt = u[j + 1][0] - t if j + 1 < len(u) else None
            for a, lab in ((30, "<60 s"), (180, "60–300 s"), (600, "300–900 s"), (1350, "900–1800 s"), (2700, ">1800 s")):
                if t + a > reqs[-1][0]: break                    # the trace ends before the block reaches that age
                if nxt is None or nxt > a: again_a[lab][0] += 1; again_a[lab][1] += (nxt is not None)
    res = dict(trace=trace, requests=len(reqs), span_s=span, accesses=N, blocks=nblk, reuses=reuses,
               never_share=never / nblk, never_share_first_half=never_fh / len(first_half), never_bytes_share=never / nblk,
               classes={lab: dict(blocks=v[0], block_share=v[0] / nblk, reuses=v[1], reuse_share=v[1] / max(1, reuses)) for lab, v in cls.items()},
               concentration=conc, gap_p=(q(gaps, .1), q(gaps, .5), q(gaps, .9)), first_gap_p=(q(first_gap, .1), q(first_gap, .5), q(first_gap, .9)), life_p=(q(life, .5), q(life, .9)),
               horizon=horizon, stack_gib_p=(q(sd_gib, .1), q(sd_gib, .5), q(sd_gib, .9)), stack_within_200=sum(1 for d in sd_gib if d < 200) / max(1, len(sd_gib)),
               creation=creation, chain=chain, again_k={lab: dict(n=v[0], p=v[1] / v[0] if v[0] else None) for lab, v in again_k.items()}, again_age={lab: dict(n=v[0], p=v[1] / v[0] if v[0] else None) for lab, v in again_a.items()})
    R[trace] = dict(res=res, gaps=gaps, first_gap=first_gap, sd_gib=sd_gib)
    json.dump(res, open(os.path.join(OUT, f"characterization-{trace}.json"), "w"), indent=1)
    say(f"## {trace}: {len(reqs)} requests over {span:.0f} s, {N} block accesses, {nblk} distinct blocks, {reuses} reuses")
    say(f"  never reused: {100 * res['never_share']:.1f}% of blocks ({100 * res['never_share_first_half']:.1f}% of blocks created in the first half of the span)")
    say("  reuse-count classes: " + "; ".join(f"{lab}: {v['block_share'] * 100:.1f}% of blocks, {v['reuse_share'] * 100:.1f}% of reuses" for lab, v in res["classes"].items()))
    say(f"  concentration: top 0.1% of blocks carry {100 * conc[0.001]:.1f}% of reuses, top 1% {100 * conc[0.01]:.1f}%, top 10% {100 * conc[0.1]:.1f}%")
    say(f"  time between uses p10/p50/p90: {res['gap_p'][0]:.0f} / {res['gap_p'][1]:.0f} / {res['gap_p'][2]:.0f} s; creation to second use p50 {res['first_gap_p'][1]:.0f} s; lifetime of reused blocks p50 {res['life_p'][0]:.0f} s, p90 {res['life_p'][1]:.0f} s")
    say("  share of reuses whose next use is within " + ", ".join(f"{H} s: {100 * horizon[H]:.0f}%" for H in HORIZONS))
    say(f"  stack distance of reuses (8B, GiB) p10/p50/p90: {res['stack_gib_p'][0]:.0f} / {res['stack_gib_p'][1]:.0f} / {res['stack_gib_p'][2]:.0f}; within 200 GiB: {100 * res['stack_within_200']:.1f}%")
    for fname, tab in creation.items():
        say(f"  P(reused later | {fname}) first half -> second half: " + "; ".join(f"{lab}: {100 * v['p1']:.0f}% -> {100 * v['p2']:.0f}% (n {v['n1']}/{v['n2']})" for lab, v in tab.items() if v["p1"] is not None and v["p2"] is not None))
    for fname, tab in chain.items():
        say(f"  P(new blocks reused later | {fname}) first half -> second half [within 300 s]: " + "; ".join(f"{lab}: {100 * v['p1']:.0f}% -> {100 * v['p2']:.0f}% [{100 * v['p2_300']:.0f}%] (n {v['n1']}/{v['n2']})" for lab, v in tab.items() if v["p1"] is not None and v["p2"] is not None and v["n1"] >= 200 and v["n2"] >= 200))
    say("  P(used again | past reuse count): " + "; ".join(f"{lab}: {100 * v['p']:.0f}% (n {v['n']})" for lab, v in res["again_k"].items() if v["p"] is not None))
    say("  P(used again | time since last use): " + "; ".join(f"{lab}: {100 * v['p']:.0f}% (n {v['n']})" for lab, v in res["again_age"].items() if v["p"] is not None))
    say()

# ---------------------------------------------------------------- figures
fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
labs = [c[0] for c in [("1 (never reused)", 1, 1), ("2", 2, 2), ("3–4", 3, 4), ("5–9", 5, 9), ("10–99", 10, 99), ("100+", 100, 10**9)]]
w = 0.27
for k, (key, yl, ax) in enumerate([("block_share", "share of blocks", axs[0]), ("reuse_share", "share of reuses", axs[1])]):
    for j, tr in enumerate(TRACES):
        vals = [100 * R[tr]["res"]["classes"][l][key] for l in labs]
        b = ax.bar([x + (j - 1) * w for x in range(len(labs))], vals, w * 0.92, color=COL[tr], label=tr)
        for r, v in zip(b, vals):
            if v >= 3: ax.annotate(f"{v:.0f}", (r.get_x() + r.get_width() / 2, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=8.5)
    ax.set_xticks(range(len(labs))); ax.set_xticklabels(labs, fontsize=10); ax.set_ylabel(yl + ", %"); ax.set_xlabel("uses of the block in the trace")
axs[0].legend(loc="upper right"); axs[0].set_title("Most blocks are used once; reuses concentrate on few blocks", fontsize=12)
save(fig, "fig-reuse-classes")
fig, axs = plt.subplots(1, 3, figsize=(12.5, 3.9))
for tr in TRACES:
    for ax, (key, xl) in zip(axs, [("gaps", "time between consecutive uses, s"), ("first_gap", "time from creation to second use, s"), ("sd_gib", "LRU stack distance of a reuse, GiB (8B)")]):
        xs = sorted(R[tr][key]); ax.plot(xs, [i / len(xs) for i in range(1, len(xs) + 1)], color=COL[tr], label=tr, lw=1.8)
        ax.set_xscale("log"); ax.set_xlabel(xl); ax.set_ylim(0, 1)
axs[0].set_ylabel("CDF"); axs[0].legend(loc="lower right"); axs[2].axvline(200, color="#d62728", ls=":", lw=1.2); axs[2].text(210, 0.05, "200 GiB", color="#d62728", fontsize=10)
save(fig, "fig-reuse-timing-distance")
fig, axs = plt.subplots(1, 4, figsize=(14, 3.9))
for ax, fname in zip(axs, ["position in request", "request length (blocks)", "continuation depth (leading old blocks)", "new blocks in the request"]):
    labs = list(R[TRACES[0]]["res"]["creation"][fname].keys())
    for j, tr in enumerate(TRACES):
        tab = R[tr]["res"]["creation"][fname]
        ok = lambda l: tab[l]["n1"] >= 200 and tab[l]["n2"] >= 200
        ax.plot([i for i, l in enumerate(labs) if ok(l)], [100 * tab[l]["p1"] for l in labs if ok(l)], marker="o", color=COL[tr], label=f"{tr}, first half")
        ax.plot([i for i, l in enumerate(labs) if ok(l)], [100 * tab[l]["p2"] for l in labs if ok(l)], marker="o", ls="--", color=COL[tr], alpha=0.6, label=f"{tr}, second half")
        base = 100 * (1 - R[tr]["res"]["never_share"]); ax.axhline(base, color=COL[tr], lw=0.8, ls=":")
    ax.set_xticks(range(len(labs))); ax.set_xticklabels(labs, fontsize=9.5); ax.set_xlabel(fname, fontsize=10.5); ax.set_ylim(0, 100)
axs[0].set_ylabel("P(block is reused later), %"); axs[0].legend(fontsize=8, loc="upper right"); axs[0].set_title("What is known when a block is created (dotted = base rate)", fontsize=11, loc="left")
save(fig, "fig-creation-features")
fig, axs = plt.subplots(1, 4, figsize=(14, 3.9))
for ax, fname in zip(axs, ["turns so far", "time since previous turn", "answer length (tokens; known after the request)", "prompt length (tokens)"]):
    labs = list(R[TRACES[0]]["res"]["chain"][fname].keys())
    for tr in TRACES:
        tab = R[tr]["res"]["chain"][fname]; ok = lambda l: tab[l]["n1"] >= 200 and tab[l]["n2"] >= 200
        ax.plot([i for i, l in enumerate(labs) if ok(l)], [100 * tab[l]["p1"] for l in labs if ok(l)], marker="o", color=COL[tr], label=f"{tr}, first half")
        ax.plot([i for i, l in enumerate(labs) if ok(l)], [100 * tab[l]["p2"] for l in labs if ok(l)], marker="o", ls="--", color=COL[tr], alpha=0.6, label=f"{tr}, second half")
        ax.axhline(100 * (1 - R[tr]["res"]["never_share"]), color=COL[tr], lw=0.8, ls=":")
    ax.set_xticks(range(len(labs))); ax.set_xticklabels(labs, fontsize=9); ax.set_xlabel(fname, fontsize=10.5); ax.set_ylim(0, 100)
axs[0].set_ylabel("P(the request's new blocks are reused), %"); axs[0].legend(fontsize=8, loc="upper right"); axs[0].set_title("Conversation state at request time (dotted = base rate)", fontsize=11, loc="left")
save(fig, "fig-chain-features")
fig, axs = plt.subplots(1, 3, figsize=(12.5, 3.9))
for tr in TRACES:
    r = R[tr]["res"]; labs = list(r["again_k"].keys()); axs[0].plot(range(len(labs)), [100 * (r["again_k"][l]["p"] or 0) for l in labs], marker="o", color=COL[tr], label=tr)
    labs2 = list(r["again_age"].keys()); axs[1].plot(range(len(labs2)), [100 * (r["again_age"][l]["p"] or 0) for l in labs2], marker="o", color=COL[tr], label=tr)
    axs[2].plot(HORIZONS, [100 * r["horizon"][H] for H in HORIZONS], marker="o", color=COL[tr], label=tr)
axs[0].set_xticks(range(5)); axs[0].set_xticklabels(labs); axs[0].set_xlabel("reuses the block already had"); axs[0].set_ylabel("P(used again), %"); axs[0].set_ylim(0, 100); axs[0].legend()
axs[1].set_xticks(range(5)); axs[1].set_xticklabels(labs2, fontsize=9.5); axs[1].set_xlabel("time since the block's last use"); axs[1].set_ylabel("P(used again), %"); axs[1].set_ylim(0, 100)
axs[2].set_xscale("log"); axs[2].set_xlabel("horizon, s"); axs[2].set_ylabel("share of reuses with next use within horizon, %"); axs[2].set_ylim(0, 100)
save(fig, "fig-resident-features-horizon")
SUM.close(); print("done")
