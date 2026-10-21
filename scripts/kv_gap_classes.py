#!/usr/bin/env python3
"""Oracle-gap categories for the adaptive admission study (2026-10-21). From the hit bitmaps of kv_admission_sim.py
(--dump-hits: one byte per scored access, 1 hit, 0 miss on a never-seen block, 2 miss after a bypass, 3 miss after an
eviction) of the oracle and a model policy, every scored access that the ORACLE hits and the MODEL misses is put into
one category, using only the block's past at that access (touch count, gap since the previous touch, request type,
sharing across requests) plus the model's miss reason; "cold -> hot" additionally uses the FUTURE (characterization
only, marked). For each category: count, share of the oracle's extra hits, and the hindsight rate at which blocks of
that (touch count, gap bucket, request type) class that the model refused were re-looked-up within the model's
residence (how learnable the refusal was: close to the base rate = missing information, high = model limitation).
usage: kv_gap_classes.py <trace> <dump_prefix> <cap> <model> [--mooncake] [--residence S]"""
import collections, json, sys
trace, prefix, cap, model = sys.argv[1:5]; mc = "--mooncake" in sys.argv
RES = float(sys.argv[sys.argv.index("--residence") + 1]) if "--residence" in sys.argv else 150.0
R = []
for l in open(trace):
    r = json.loads(l)
    if mc: R.append((r["timestamp"] / 1000.0, [str(h) for h in r["hash_ids"]]))
    elif r.get("task", 0) >= 0: R.append((r["t_lookup"], list(r["hashes"])))
R.sort(key=lambda r: r[0]); half = len(R) // 2
orc = open(f"{prefix}-oracle-{cap}.bin", "rb").read(); mod = open(f"{prefix}-{model}-{cap}.bin", "rb").read()
acc = [(t, h, ri) for ri, (t, hs) in enumerate(R) for h in hs]
nxt = [None] * len(acc); last = {}
for i in range(len(acc) - 1, -1, -1):
    nxt[i] = last.get(acc[i][1]); last[acc[i][1]] = i
touches = collections.Counter(); last_t = {}; reqs_of = collections.defaultdict(set); seen0 = set()
cat = collections.Counter(); cat_ex = collections.Counter(); cls_ref = collections.defaultdict(lambda: [0, 0])   # class -> [refused touches, of which re-looked-up within RES]
k = 0; extra = 0; lost = 0; tot_or = 0; tot_mod = 0
ft = collections.defaultdict(lambda: [0, 0])                                            # first touches in the scored half by (request type, position bucket): [n, re-looked-up within RES]
def gapb(g): return "none" if g is None else "<R" if g <= RES else "R-2R" if g <= 2 * RES else ">2R"
for i, (t, h, ri) in enumerate(acc):
    old = None
    if ri >= half:
        if k >= min(len(orc), len(mod)): break
        o, m = orc[k], mod[k]; k += 1
        c = touches[h]; g = (t - last_t[h]) if h in last_t else None; share = len(reqs_of[h])
        old_req = sum(1 for x in R[ri][1][:8] if x in seen0) if True else 0
        fresh = "fresh" if old_req < 8 else "cont"
        tot_or += (o == 1); tot_mod += (m == 1)
        if c == 0:
            fk = (fresh, "pos0-7" if R[ri][1].index(h) < 8 else "pos8+"); ft[fk][0] += 1; nj = nxt[i]
            if nj is not None and acc[nj][0] - t <= RES: ft[fk][1] += 1
        if m in (2, 0) and c >= 1:                                                      # the model had refused this block at its last opportunity: hindsight learnability of that refusal
            cl = (min(3, c), gapb(g), fresh); cls_ref[cl][0] += 1
            nj = nxt[i]
            if nj is not None and acc[nj][0] - t <= RES: cls_ref[cl][1] += 1
        if o == 1 and m != 1:
            extra += 1
            if m == 2 or m == 0:
                if c == 1: key = "A first-touch block refused, now its second touch" + (" (fresh request)" if fresh == "fresh" else " (continuation)")
                elif c <= 4: key = f"B refused at touch {c + 1} (few samples), gap {gapb(g)}"
                else: key = f"C refused at touch 5+ (shared by {'5+' if share >= 5 else '2-4' if share >= 2 else '1'} requests), gap {gapb(g)}"
            else:
                key = f"D admitted, evicted before this reuse: gap {gapb(g)}, touches {'1' if c == 1 else '2-4' if c <= 4 else '5+'}"
            cat[key] += 1
            # cold -> hot (FUTURE information, characterization only): previous gap > 600 s and >= 3 further touches within 300 s
            if g is not None and g > 600:
                n3 = 0; j = nxt[i]
                while j is not None and acc[j][0] - t <= 300 and n3 < 3: n3 += 1; j = nxt[j]
                if n3 >= 3: cat_ex["cold->hot (prev gap > 600 s, >= 3 touches in the next 300 s) [uses the future]"] += 1
        if o != 1 and m == 1: lost += 1
    touches[h] += 1; last_t[h] = t; reqs_of[h].add(ri)
    if ri + 1 == len(R) or acc[min(i + 1, len(acc) - 1)][2] != ri: seen0.update(R[ri][1])
print(f"{model} vs oracle at cap {cap}: oracle hits {tot_or}, model hits {tot_mod}, oracle-only hits {extra} ({100 * extra / max(1, tot_or - tot_mod + extra):.0f}% of the gap), model-only hits {lost}")
for key, n in sorted(cat.items()): print(f"  {key}: {n} ({100 * n / max(1, extra):.1f}% of the oracle-only hits)")
for key, n in cat_ex.items(): print(f"  {key}: {n} ({100 * n / max(1, extra):.1f}%)")
print(f"hindsight: blocks the model refused at their last opportunity, by (touches before, gap bucket vs residence {RES:.0f} s, request type): refused -> re-looked-up within the residence")
for cl, (n, r) in sorted(cls_ref.items(), key=lambda kv: -kv[1][0])[:16]: print(f"  touches {cl[0]}{'+' if cl[0] == 3 else ''}, gap {cl[1]}, {cl[2]}: {n} refused, {100 * r / max(1, n):.0f}% re-looked-up within {RES:.0f} s")
print(f"first touches in the scored half (what a first-touch admission would buy), by request type and position: n, re-looked-up within {RES:.0f} s")
for fk, (n, r) in sorted(ft.items()): print(f"  {fk[0]}, {fk[1]}: {n} first touches, {100 * r / max(1, n):.0f}% re-looked-up within {RES:.0f} s")
