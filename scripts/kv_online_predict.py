#!/usr/bin/env python3
"""Continually updated online reuse prediction with strict chronological (prequential) evaluation (RQ1-B historical
learning round, 2026-10-18). OFFLINE PREDICTION STUDY on a KV trace (Mooncake jsonl or an agent trace jsonl).

The trace is processed once in time order. At every access the models predict with their state at that moment, then
the access updates the state. Labels ("used again within H seconds") are resolved later: a prediction is scored 1 when
the block is next used before t + H (the models learn from it at that moment), 0 when the deadline t + H passes
(processed as time advances). No statistic of the whole trace is used; the first `--tune` fraction of the trace may be
used to pick decay rates / thresholds, the rest is the evaluation period, reported in 5 equal time segments.

Two prediction problems, kept apart:
  NEW      at a block's first access: will it be used again within H?   (admission / bypass)
  OBSERVED at an access of a block that was used before: will it be used again within H?   (retention)
Models (all online, O(1) per access):
  base      running reuse rate (prior)
  root      per prefix-root (first block) decayed rate, with backoff to base below 50 samples          [NEW]
  ctx       per (root, position bucket, continuation-depth bucket) decayed rate, backoff to root       [NEW]
  cnt       per past-use-count bucket rate                                                            [OBSERVED]
  cntrec    per (count bucket, last-interval bucket) rate                                             [OBSERVED]
  interval  P(next interval <= H) from the block's own intervals (>= 2) else the root's online interval histogram [OBSERVED]
  pop       decayed popularity of the block (uses with exp decay tau), mapped through an online rate table      [OBSERVED]
  olr       online logistic regression (SGD, standardized features, lazy labels)                      [both]
Metrics per model and segment: average precision (PR-AUC), precision at recall 0.5, calibration error (10 bins), base
rate; for OBSERVED also next-interval prediction error of the `interval` model (median |log ratio|, within-2x share).
usage: kv_online_predict.py <trace> <out_dir> <tag> [--mooncake] [--H 60,300] [--tau 300] [--tune 0.2] [--max-pred 2000000]"""
import argparse, bisect, collections, json, math, os, random
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser(); ap.add_argument("trace"); ap.add_argument("out"); ap.add_argument("tag"); ap.add_argument("--mooncake", action="store_true")
ap.add_argument("--H", default="60,300"); ap.add_argument("--tau", type=float, default=300.0); ap.add_argument("--tune", type=float, default=0.2); ap.add_argument("--lr", type=float, default=0.05)
A = ap.parse_args(); os.makedirs(A.out, exist_ok=True); INF = float("inf")
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.grid": True, "grid.color": "#e6e6e6", "legend.frameon": False, "svg.fonttype": "none"})

R = []
for l in open(A.trace):
    r = json.loads(l)
    if A.mooncake: R.append((r["timestamp"] / 1000.0, [str(h) for h in r["hash_ids"]], r["input_length"]))
    elif r.get("task", 0) >= 0: R.append((r["t_lookup"], list(r["hashes"]), len(r["hashes"]) * 256))
R.sort(key=lambda r: r[0]); T0 = R[0][0]; T1 = R[-1][0]; SPAN = T1 - T0; TUNE_END = T0 + A.tune * SPAN
acc = [(t, h, ri, j) for ri, (t, hs, L) in enumerate(R) for j, h in enumerate(hs)]
print(f"{A.tag}: {len(R)} requests, {len(acc)} accesses, span {SPAN:.0f} s; tuning on the first {100 * A.tune:.0f}%, evaluating the rest in 5 segments")
Hs = [float(x) for x in A.H.split(",")]

# ------------------------------------------------------------------ online state
first_seen = {}; cnt = collections.Counter(); last_t = {}; last_iv = {}; ivs = collections.defaultdict(list); pos0 = {}; root_of = {}; dep0 = {}; L0 = {}
pop = {}; pop_t = {}
def popularity(h, t):
    if h not in pop: return 0.0
    return pop[h] * math.exp(-(t - pop_t[h]) / A.tau)
class Rate:
    """decayed Beta-like rate: (reused, total) with exponential forgetting per time."""
    __slots__ = ("a", "n", "t")
    def __init__(self): self.a = 0.0; self.n = 0.0; self.t = None
    def decay(self, t):
        if self.t is not None and t > self.t: f = math.exp(-(t - self.t) / (4 * A.tau)); self.a *= f; self.n *= f
        self.t = t if self.t is None else max(self.t, t)
    def update(self, t, y): self.decay(t); self.a += y; self.n += 1
    def p(self, t, prior, k=20.0): self.decay(t); return (self.a + k * prior) / (self.n + k)
base = {H: Rate() for H in Hs}; root_rate = {H: collections.defaultdict(Rate) for H in Hs}; ctx_rate = {H: collections.defaultdict(Rate) for H in Hs}
cnt_rate = {H: collections.defaultdict(Rate) for H in Hs}; cntrec_rate = {H: collections.defaultdict(Rate) for H in Hs}; pop_rate = {H: collections.defaultdict(Rate) for H in Hs}
root_ivs = collections.defaultdict(list)                                   # online interval samples per root (capped)
def bucket(x, edges): return bisect.bisect_right(edges, x)
CNT_E = [1, 2, 4, 8]; IV_E = [10, 60, 300, 900]; POP_E = [0.5, 1, 2, 4, 8]; POS_E = [1, 4, 16, 64]; DEP_E = [1, 8, 32]
class OLR:
    """online logistic regression with per-feature running standardization and lazy labels."""
    def __init__(self, d): self.w = [0.0] * (d + 1); self.m = [0.0] * d; self.v = [1.0] * d; self.n = 0
    def z(self, x):
        self.n += 1
        if self.n <= 2000:
            for i, xi in enumerate(x): self.m[i] += (xi - self.m[i]) / self.n; self.v[i] += ((xi - self.m[i]) ** 2 - self.v[i]) / self.n
        return [(xi - self.m[i]) / math.sqrt(self.v[i] + 1e-6) for i, xi in enumerate(x)]
    def p(self, z): s = self.w[0] + sum(w * zi for w, zi in zip(self.w[1:], z)); return 1 / (1 + math.exp(-max(-30, min(30, s))))
    def update(self, z, y):
        p = self.p(z); g = p - y; self.w[0] -= A.lr * g
        for i, zi in enumerate(z): self.w[i + 1] -= A.lr * (g * zi + 1e-4 * self.w[i + 1])
olr_new = {H: OLR(8) for H in Hs}; olr_obs = {H: OLR(9) for H in Hs}
def feats_new(h, t, j, dep, L, root):
    rr = root_rate[Hs[0]][root]; return [math.log1p(j), math.log1p(dep), math.log1p(L / 512), rr.p(t, 0.25) if rr.n > 0 else 0.25, math.log1p(rr.n), math.log1p(popularity(root, t)), 1.0 if j < 1 else 0.0, math.log1p(t - first_seen.get(root, t))]
def feats_obs(h, t):
    c = cnt[h]; age = t - first_seen[h]; li = last_iv.get(h, age); mi = (sum(ivs[h]) / len(ivs[h])) if ivs[h] else li
    return [math.log1p(c), math.log1p(age), math.log1p(li), math.log1p(mi), math.log1p(popularity(h, t)), math.log1p(pos0[h]), math.log1p(dep0[h]), math.log1p(L0[h] / 512), math.log1p(t - last_t[h])]

# predictions awaiting labels: heap by deadline; and the per-block list of open predictions (for early positive labels)
import heapq
pending = []                                                               # (deadline, idx)
open_by_block = collections.defaultdict(list)
P = []                                                                     # records: dict(kind, H, t, h, scores{model: p}, y, z_new/z_obs for olr updates, keys for table updates)
NEXT_IV = []                                                               # (predicted next interval, actual) for the interval model (evaluation period only)
def resolve(idx, y, t_now):
    rec = P[idx]
    if rec["y"] is not None: return
    rec["y"] = y; H = rec["H"]
    if rec["kind"] == "new":
        base[H].update(t_now, y); root_rate[H][rec["root"]].update(t_now, y); ctx_rate[H][rec["ctx"]].update(t_now, y); olr_new[H].update(rec["z"], y)
    else:
        cnt_rate[H][rec["cb"]].update(t_now, y); cntrec_rate[H][rec["cr"]].update(t_now, y); pop_rate[H][rec["pb"]].update(t_now, y); olr_obs[H].update(rec["z"], y)
def process_deadlines(t_now):
    while pending and pending[0][0] <= t_now:
        dl, idx = heapq.heappop(pending); resolve(idx, 0, dl)
        rec = P[idx]; lst = open_by_block.get(rec["h"])
        if lst and idx in lst: lst.remove(idx)

for i, (t, h, ri, j) in enumerate(acc):
    process_deadlines(t)
    hs = R[ri][1]; L = R[ri][2]; root = hs[0]
    # positive labels for open predictions of this block
    for idx in open_by_block.pop(h, []):
        rec = P[idx]
        if t <= rec["t"] + rec["H"]: resolve(idx, 1, t)
        else: resolve(idx, 0, t)
    if h not in first_seen:
        first_seen[h] = t; pos0[h] = j; dep0[h] = sum(1 for x in hs[:j] if x in first_seen and first_seen[x] < t); L0[h] = L; root_of[h] = root
        if root not in first_seen: first_seen[root] = t
        for H in Hs:
            fx = feats_new(h, t, j, dep0[h], L, root); z = olr_new[H].z(fx) if H == Hs[0] else olr_new[H].z(fx)
            rr = root_rate[H][root]; pb = base[H].p(t, 0.25) if base[H].n > 0 else 0.25
            ctx = (root, bucket(j, POS_E), bucket(dep0[h], DEP_E)); cr_ = ctx_rate[H][ctx]
            scores = dict(base=pb, root=rr.p(t, pb) if rr.n >= 50 else pb, ctx=cr_.p(t, rr.p(t, pb) if rr.n >= 50 else pb) if cr_.n >= 50 else (rr.p(t, pb) if rr.n >= 50 else pb), olr=olr_new[H].p(z))
            P.append(dict(kind="new", H=H, t=t, h=h, root=root, ctx=ctx, z=z, scores=scores, y=None, unseen_root=(rr.n < 50))); idx = len(P) - 1
            heapq.heappush(pending, (t + H, idx)); open_by_block[h].append(idx)
    else:
        c = cnt[h]; iv = t - last_t[h]; ivs[h].append(iv) if len(ivs[h]) < 50 else None; last_iv[h] = iv
        if len(root_ivs[root]) < 5000: root_ivs[root].append(iv)
        for H in Hs:
            fx = feats_obs(h, t); z = olr_obs[H].z(fx)
            cb = bucket(c, CNT_E); cr = (cb, bucket(iv, IV_E)); pb_ = bucket(popularity(h, t), POP_E)
            pb = base[H].p(t, 0.25) if base[H].n > 0 else 0.25
            own = [x for x in ivs[h]]; ri_ = root_ivs[root]
            if len(own) >= 2: p_iv = sum(1 for x in own if x <= H) / len(own)
            elif len(ri_) >= 50: p_iv = sum(1 for x in ri_ if x <= H) / len(ri_)
            else: p_iv = pb
            scores = dict(base=pb, cnt=cnt_rate[H][cb].p(t, pb) if cnt_rate[H][cb].n >= 50 else pb, cntrec=cntrec_rate[H][cr].p(t, pb) if cntrec_rate[H][cr].n >= 50 else pb,
                          interval=p_iv, pop=pop_rate[H][pb_].p(t, pb) if pop_rate[H][pb_].n >= 50 else pb, olr=olr_obs[H].p(z))
            P.append(dict(kind="obs", H=H, t=t, h=h, cb=cb, cr=cr, pb=pb_, z=z, scores=scores, y=None, pred_iv=(sum(own) / len(own)) if len(own) >= 2 else (sorted(ri_)[len(ri_) // 2] if len(ri_) >= 50 else None))); idx = len(P) - 1
            heapq.heappush(pending, (t + H, idx)); open_by_block[h].append(idx)
    cnt[h] += 1; last_t[h] = t; pop[h] = popularity(h, t) + 1.0; pop_t[h] = t; pop[root] = popularity(root, t) + 1.0; pop_t[root] = t
process_deadlines(T1 + max(Hs) + 1)
# next-interval evaluation: for obs predictions with pred_iv, the actual next interval if the block was used again
nxt = {}
for i in range(len(acc) - 1, -1, -1):
    t, h, ri, j = acc[i]; nxt_t = nxt.get(h); acc_next = nxt_t; nxt[h] = t
    if acc_next is not None: pass
# recompute actual next intervals per access index
last_next = {}; actual_next = [INF] * len(acc)
for i in range(len(acc) - 1, -1, -1):
    t, h, ri, j = acc[i]
    if h in last_next: actual_next[i] = last_next[h] - t
    last_next[h] = t
obs_idx = 0
for rec in P:
    pass

# ------------------------------------------------------------------ evaluation
def ap_score(pairs):
    """average precision for (score, label) pairs."""
    pairs = sorted(pairs, key=lambda x: -x[0]); npos = sum(y for _, y in pairs)
    if npos == 0: return float("nan")
    tp = 0; s = 0.0
    for k, (sc, y) in enumerate(pairs, 1):
        if y: tp += 1; s += tp / k
    return s / npos
def prec_at_recall(pairs, r=0.5):
    pairs = sorted(pairs, key=lambda x: -x[0]); npos = sum(y for _, y in pairs); tp = 0
    for k, (sc, y) in enumerate(pairs, 1):
        if y: tp += 1
        if tp >= r * npos: return tp / k
    return float("nan")
def calib(pairs):
    bins = collections.defaultdict(lambda: [0.0, 0.0, 0])
    for sc, y in pairs: b = min(9, int(sc * 10)); bins[b][0] += sc; bins[b][1] += y; bins[b][2] += 1
    n = sum(v[2] for v in bins.values()); return sum(abs(v[0] / v[2] - v[1] / v[2]) * v[2] for v in bins.values()) / max(1, n)
res = {}
segs = [(TUNE_END + k * (T1 - TUNE_END) / 5, TUNE_END + (k + 1) * (T1 - TUNE_END) / 5) for k in range(5)]
for kind in ("new", "obs"):
    for H in Hs:
        recs = [r for r in P if r["kind"] == kind and r["H"] == H and r["y"] is not None and r["t"] >= TUNE_END]
        if not recs: continue
        models = list(recs[0]["scores"].keys()); key = f"{kind}_H{int(H)}"; res[key] = dict(n=len(recs), base_rate=sum(r["y"] for r in recs) / len(recs), models={})
        for m in models:
            pairs = [(r["scores"][m], r["y"]) for r in recs]
            seg_ap = [ap_score([(r["scores"][m], r["y"]) for r in recs if a <= r["t"] < b]) for a, b in segs]
            d = dict(ap=ap_score(pairs), prec_at_recall50=prec_at_recall(pairs), calib_err=calib(pairs), ap_by_segment=seg_ap)
            if kind == "new":
                un = [(r["scores"][m], r["y"]) for r in recs if r.get("unseen_root")]; d["ap_unseen_root"] = ap_score(un) if un else float("nan"); d["n_unseen_root"] = len(un)
            res[key]["models"][m] = d
        res[key]["ap_random"] = res[key]["base_rate"]
# next-interval error (interval model): for obs records with pred_iv and a finite actual next use
errs = []
acc_i = 0
# map records back to accesses: records were appended in access order (per access: len(Hs) records); rebuild by walking
ptr = 0
for i, (t, h, ri, j) in enumerate(acc):
    nrec = len(Hs)
    while ptr < len(P) and P[ptr]["t"] < t: ptr += 1
    # records of this access start at ptr (same t, same h)
    k = ptr
    while k < len(P) and P[k]["t"] == t and P[k]["h"] != h: k += 1
    if k < len(P) and P[k]["t"] == t and P[k]["h"] == h and P[k]["kind"] == "obs" and P[k].get("pred_iv") and actual_next[i] < INF and t >= TUNE_END:
        errs.append((P[k]["pred_iv"], actual_next[i]))
    ptr = k
if errs:
    lr = sorted(abs(math.log((p + 1) / (a + 1))) for p, a in errs)
    res["next_interval"] = dict(n=len(errs), median_abs_log_ratio=lr[len(lr) // 2], within_2x=sum(1 for x in lr if x <= math.log(2)) / len(lr), within_5x=sum(1 for x in lr if x <= math.log(5)) / len(lr), median_pred_s=sorted(p for p, _ in errs)[len(errs) // 2], median_actual_s=sorted(a for _, a in errs)[len(errs) // 2])
json.dump(res, open(f"{A.out}/{A.tag}-predict.json", "w"), indent=1)
for key, v in res.items():
    if key == "next_interval": print("next-interval", {k: round(x, 3) for k, x in v.items()}); continue
    print(f"== {key}: n={v['n']}, base rate {v['base_rate']:.3f}")
    for m, d in v["models"].items(): print(f"   {m:9s} AP {d['ap']:.3f}  P@R50 {d['prec_at_recall50']:.3f}  calib {d['calib_err']:.3f}  AP by segment {[round(x, 3) for x in d['ap_by_segment']]}" + (f"  unseen-root AP {d['ap_unseen_root']:.3f} (n={d['n_unseen_root']})" if "ap_unseen_root" in d else ""))
# figure: AP per model (new / obs) and per segment
fig, axs = plt.subplots(1, 2, figsize=(13, 4.4))
for ax, kind in zip(axs, ("new", "obs")):
    key = f"{kind}_H{int(Hs[0])}"
    if key not in res: continue
    v = res[key]; ms = list(v["models"].keys())
    for m in ms: ax.plot(range(1, 6), v["models"][m]["ap_by_segment"], marker="o", label=m)
    ax.axhline(v["base_rate"], color="#7f7f7f", ls=":", label=f"random (base rate {v['base_rate']:.2f})"); ax.set_ylim(0, 1); ax.set_xlabel("evaluation segment (chronological fifths after the tuning period)"); ax.set_ylabel("average precision"); ax.legend(fontsize=8)
    ax.set_title(f"{A.tag}: {'NEW blocks' if kind == 'new' else 'OBSERVED blocks'}, reuse within {int(Hs[0])} s (n={v['n']})", fontsize=10)
fig.tight_layout(); fig.savefig(f"{A.out}/fig-predict-{A.tag}.png", dpi=200); fig.savefig(f"{A.out}/fig-predict-{A.tag}.svg"); print("wrote", f"{A.out}/fig-predict-{A.tag}.png")
