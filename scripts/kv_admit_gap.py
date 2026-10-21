#!/usr/bin/env python3
"""Oracle-gap decomposition of admission decisions (RQ1-B admission study, 2026-10-20). Reads the admission dumps written
by kv_agent_replay.py --dump-admit (one byte per NEW block of the scored half, 1 admitted / 0 bypassed, same order for
every policy) for the oracle and a model, walks the trace to attach each new block's features — position in the
request, existing-prefix length of the request, root, next-use time (s), next-use stack distance (distinct blocks
touched before the next use, in GiB) — and cross-tabulates the four decision classes:
  oracle admits & model admits, oracle admits & model bypasses, oracle bypasses & model admits, both bypass.
usage: kv_admit_gap.py <trace> <prefix> <cap> <model> [--mooncake] [--block-mb 67.1]"""
import collections, json, sys
trace, prefix, cap, model = sys.argv[1:5]; mc = "--mooncake" in sys.argv
block_mb = float(sys.argv[sys.argv.index("--block-mb") + 1]) if "--block-mb" in sys.argv else 67.1
R = []
for l in open(trace):
    r = json.loads(l)
    if mc: R.append((r["timestamp"] / 1000.0, [str(h) for h in r["hash_ids"]]))
    elif r.get("task", 0) >= 0: R.append((r["t_lookup"], list(r["hashes"])))
R.sort(key=lambda r: r[0]); half = len(R) // 2
acc = [(t, h, ri, j) for ri, (t, hs) in enumerate(R) for j, h in enumerate(hs)]
INF = float("inf"); nu = [INF] * len(acc); last = {}
for i in range(len(acc) - 1, -1, -1):
    h = acc[i][1]; nu[i] = last.get(h, INF); last[h] = i
# stack distance (distinct blocks between an access and the next use of the same block) via a Fenwick tree over last-access positions
n = len(acc); tree = [0] * (n + 1)
def add(i, v):
    i += 1
    while i <= n: tree[i] += v; i += i & -i
def pref(i):
    i += 1; s = 0
    while i > 0: s += tree[i]; i -= i & -i
    return s
lastpos = {}; dist = [INF] * n
for i, (t, h, ri, j) in enumerate(acc):
    if h in lastpos:
        p = lastpos[h]; dist[p] = pref(i - 1) - pref(p); add(p, -1)
    lastpos[h] = i; add(i, 1)
orc = open(f"{prefix}-oracle-{cap}.adm", "rb").read(); mod = open(f"{prefix}-{model}-{cap}.adm", "rb").read()
# existing-prefix length of every request (blocks that existed before the request started)
seen0 = set(); old_of = []
for t, hs in R: old_of.append(sum(1 for x in hs if x in seen0)); seen0.update(hs)
seen = set(); k = 0; cls = collections.defaultdict(lambda: dict(n=0, reused=0, within60=0, within300=0, nxt=[], sd=[], pos=collections.Counter(), old=collections.Counter(), hits_lost=0))
for i, (t, h, ri, j) in enumerate(acc):
    if h in seen: continue
    seen.add(h)
    if ri < half: continue
    if k >= min(len(orc), len(mod)): break
    o, m = orc[k], mod[k]; k += 1
    key = ("oracle admits" if o else "oracle bypasses") + " / " + ("model admits" if m else "model bypasses")
    c = cls[key]; c["n"] += 1; old = old_of[ri]
    c["pos"]["0-7" if j < 8 else "8-31" if j < 32 else "32+"] += 1; c["old"]["fresh" if old == 0 else "old<8" if old < 8 else "old8+"] += 1
    if nu[i] < INF:
        c["reused"] += 1; dt = acc[nu[i]][0] - t; c["within60"] += dt <= 60; c["within300"] += dt <= 300; c["nxt"].append(dt); c["sd"].append(dist[i] * block_mb / 1024)
def q(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else float("nan")
tot = sum(c["n"] for c in cls.values())
print(f"{model} vs oracle at cap {cap}: {tot} new blocks in the scored half")
for key in ("oracle admits / model admits", "oracle admits / model bypasses", "oracle bypasses / model admits", "oracle bypasses / model bypasses"):
    c = cls.get(key)
    if not c: continue
    print(f"  {key}: n={c['n']} ({100 * c['n'] / tot:.1f}%), reused later {100 * c['reused'] / max(1, c['n']):.0f}% (within 60 s {100 * c['within60'] / max(1, c['n']):.0f}%, 300 s {100 * c['within300'] / max(1, c['n']):.0f}%), next-use p50/p90 {q(c['nxt'], .5):.0f}/{q(c['nxt'], .9):.0f} s, stack distance p50/p90 {q(c['sd'], .5):.0f}/{q(c['sd'], .9):.0f} GiB, position {dict(c['pos'])}, request {dict(c['old'])}")
