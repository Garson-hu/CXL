#!/usr/bin/env python3
"""Figures of the 2026-11-10 progress deck (GPU KV admission study + the reuse-distance question on CosmoFlow), drawn with matplotlib
(default colour cycle, white background) from the raw results; every figure also writes its data table (CSV) next to the PNG.
  f01_problem   one request alone (2026-11-04 study: 4k-token prompt, recompute vs load from host memory) and the same kinds of request
                on a busy server (this study, stock tool-agent replay at the sustainable load: median time to first token)
  f03_cause     where the waiting time of host hits goes (stock replays, sustainable load and overload) and the time to first token of a
                host hit by the state of the engine at its arrival
  f04_timeline  the controlled test (one 28k-token prompt, three host hits and a 4k miss behind it): stock against the prototype
  f05_results   trace replays: mean time to first token by request type, stock against prototype, at the sustainable load and under
                overload (with the oracle hits-first priority baseline); KV stored in the host cache with and without the store fix
  f06_reuse     CosmoFlow (the group's real run of 2026-10-27: 61,440 files, 3 epochs): when twelve files are read, and the reuse distance
                of all 122,880 re-reads
Meaning of the colours in the comparisons: C0 = stock, C1 = prototype, C2 = priority scheduling with perfect knowledge.
usage: scripts/figs_deck_2026-11-10.py     (from the repo root; writes docs/slides/2026-11-10-kv-admission-progress/figs/)"""
import csv, json, os, re, subprocess
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "docs", "slides", "2026-11-10-kv-admission-progress", "figs"); os.makedirs(OUT, exist_ok=True)
RES = os.path.join(ROOT, "experimental_results", "2026-11-10-gpu-kv-admission"); REPLAY = os.path.join(RES, "replay")
C1C = os.path.join(RES, "E16", "c1c") if os.path.isdir(os.path.join(RES, "E16", "c1c")) else "/mnt/beegfs/ghu4/kvadm/results/c1c"
COSMO = ("explore/reuse-window-prefetch", "experimental_results/2026-10-27-reuse-window-prefetch/train/run-61440/reads.txt")
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False})
SOURCES = []
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def q(v, p):
    v = sorted(x for x in v if x is not None); return v[min(len(v) - 1, int(p * len(v)))] if v else None
def mean(v):
    v = [x for x in v if x is not None]; return sum(v) / len(v) if v else None
def rows(tag, d=REPLAY): return list(csv.DictReader(open(os.path.join(d, f"{tag}-adm-requests.csv"))))
def save(fig, name, table, header, src):
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=200); fig.savefig(os.path.join(OUT, name + ".svg")); plt.close(fig)
    with open(os.path.join(OUT, name + ".csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(table)
    SOURCES.append((name, src)); print("wrote", name)
def label(ax, bars, fmt, dy=0.0, size=11):
    for b in bars:
        v = b.get_height(); ax.text(b.get_x() + b.get_width() / 2, v + dy, fmt(v), ha="center", va="bottom", fontsize=size)
CAT = {"host≥50%": "host hit", "GPU≥50%": "GPU hit", "miss<10%": "miss"}

# ---------------------------------------------------------------- f01: the problem
def f01():
    R = rows("tool04-320-base")
    p50 = {c: q([fl(r["ttft"]) for r in R if r["cat"] == c], .5) for c in CAT}; n = {c: sum(1 for r in R if r["cat"] == c) for c in CAT}
    fig, ax = plt.subplots(1, 2, figsize=(12.3, 3.7), gridspec_kw=dict(width_ratios=[1, 1.35]))
    a = ax[0]; v = [651, 34.8]; b = a.bar(["miss: compute\nthe prompt again", "host hit: load the saved KV\nfrom host memory"], v, 0.5, color="C0"); label(a, b, lambda x: f"{x:.0f} ms", 8); a.tick_params(axis="x", labelsize=10.5)
    a.set_ylabel("time to first token (ms)"); a.set_ylim(0, 760); a.set_title("(a) One request alone, 4,000-token prompt", fontsize=12.5)
    a = ax[1]; order = ["GPU≥50%", "host≥50%", "miss<10%"]
    names = [f"GPU hit: KV is\nstill in GPU memory\n({n['GPU≥50%']} requests)", f"host hit: KV is loaded\nfrom host memory\n({n['host≥50%']} requests)", f"miss: nothing saved,\ncompute everything\n({n['miss<10%']} requests)"]
    b = a.bar(names, [p50[c] for c in order], 0.5, color="C0"); label(a, b, lambda x: f"{x:.1f} s", 0.08); a.tick_params(axis="x", labelsize=10.5)
    a.set_ylabel("time to first token, median (s)"); a.set_ylim(0, 6.0); a.set_title("(b) The same kinds of request on a busy server (real trace)", fontsize=12.5)
    fig.tight_layout(w_pad=3)
    save(fig, "f01_problem", [["alone, 4k prompt", "recompute", 651, "ms"], ["alone, 4k prompt", "host hit", 34.8, "ms"]] + [["busy server (tool04-320-base)", CAT[c], round(p50[c], 3), "s (median)"] for c in order],
         ["panel", "request", "time to first token", "unit"], "experimental_results/2026-11-04-cxl-serving-scheduling-gap/SUMMARY.md (651 ms, 34.8 ms); replay/tool04-320-base-adm-requests.csv")

# ---------------------------------------------------------------- f03: the cause
def f03():
    CA = [("Step budget used up\nby a long prompt:\nqueue not looked at", ("budget", "budget_adm")), ("Not enough free GPU\nmemory: first request\nin line blocks the rest", ("hol:full", "own:full")),
          ("Cache lookup\nstill pending", ("pending",)), ("Memory reservation\nfor the saved prefix\n(the cause we suspected)", ("hol:resv", "own:resv"))]
    S = {}
    for tag in ("tool04-320-base", "tool08-320-base"):
        H = [r for r in rows(tag) if r["cat"] == "host≥50%"]
        tot = {}
        for r in H:
            for k, v in r.items():
                if k.startswith("w_") and not k.startswith(("w_pre_", "w_lookup_", "w_admit_", "w_promote_")): tot[k[2:]] = tot.get(k[2:], 0.0) + (fl(v) or 0.0)
        allw = sum(tot.values()); S[tag] = [100 * sum(tot.get(k, 0.0) for k in keys) / allw for _, keys in CA]
    H = [r for r in rows("tool04-320-base") if r["cat"] == "host≥50%" and fl(r.get("arr_infl")) is not None]
    quiet = [fl(r["ttft"]) for r in H if fl(r["arr_infl"]) == 0]; busy = [fl(r["ttft"]) for r in H if fl(r["arr_infl"]) > 0]
    fig, ax = plt.subplots(1, 2, figsize=(12.3, 3.7), gridspec_kw=dict(width_ratios=[2.25, 1]))
    a = ax[0]; x = np.arange(len(CA)); w = 0.36
    b1 = a.bar(x - w / 2, S["tool04-320-base"], w, color="C0", label="normal load"); b2 = a.bar(x + w / 2, S["tool08-320-base"], w, color="C4", label="overload")
    for b in (b1, b2): label(a, b, lambda v: f"{v:.0f} %" if v >= 1 else (f"{v:.1f} %" if v >= 0.1 else "< 0.1 %"), 1.0, 10.5)
    a.set_xticks(x); a.set_xticklabels([c for c, _ in CA], fontsize=10); a.set_ylabel("share of the waiting time\nof host hits (%)"); a.set_ylim(0, 75); a.legend(frameon=False, loc="upper right")
    a.set_title("(a) Where the waiting time of host hits goes (stock server)", fontsize=12.5)
    a = ax[1]; b = a.bar([f"no long prompt\nis being read\n(n = {len(quiet)})", f"a long prompt\nis being read\n(n = {len(busy)})"], [q(quiet, .5), q(busy, .5)], 0.5, color="C0"); label(a, b, lambda v: f"{v:.1f} s", 0.15)
    a.set_ylabel("time to first token\nof a host hit, median (s)"); a.set_ylim(0, 12.5); a.set_title("(b) A host hit that arrives when ...", fontsize=12.5)
    fig.tight_layout(w_pad=2.5)
    save(fig, "f03_cause", [[c.replace("\n", " "), round(S["tool04-320-base"][i], 2), round(S["tool08-320-base"][i], 2)] for i, (c, _) in enumerate(CA)] + [["TTFT p50 of a host hit, no prefill in flight at arrival (s)", round(q(quiet, .5), 3), ""], ["TTFT p50 of a host hit, prefill in flight at arrival (s)", round(q(busy, .5), 3), ""]],
         ["cause (share of the waiting time of host-dominant hits, %)", "normal load (tool04-320-base)", "overload (tool08-320-base)"], "replay/tool04-320-base-adm-requests.csv, replay/tool08-320-base-adm-requests.csv (columns w_*, arr_infl, ttft)")

# ---------------------------------------------------------------- f04: the controlled test
def f04():
    PH = [("unvisited", "in the queue, not looked at", "0.75"), ("lookup", "cache lookup", "C4"), ("admit", "waiting to be admitted", "C3"), ("load", "loading the saved KV", "C1"),
          ("promote", "loaded, waiting for a step", "C5"), ("prefill", "reading the prompt (prefill)", "C0"), ("decode", "writing the answer", "C2")]
    NAMES = {0: "long request (28,000 tokens)", 1: "host hit, sent at 0.5 s", 2: "miss (4,000 tokens), at 1.5 s", 3: "host hit, sent at 2.5 s", 4: "host hit, sent at 4.5 s"}
    fig, axes = plt.subplots(2, 1, figsize=(8.7, 4.9), sharex=True); table = []; seen = set()      # placed at this size beside the text
    for ax, tag, ttl in ((axes[0], "c1c-base", "Stock server"), (axes[1], "c1c-tokfast512-sync", "With the prototype")):
        R = {}
        for r in rows(tag, C1C):
            m = re.match(rf"{re.escape(tag)}-c1-B28000-r0-p(\d+)-(host|cold)-L(\d+)$", r["rid"])
            if m: R[int(m.group(1))] = r
        t0 = fl(R[0]["send"])
        for pos in sorted(R):
            r = R[pos]; g = lambda k: (fl(r[k]) - t0) if fl(r[k]) is not None else None
            send = g("send"); tv = g("t_visit"); tr = g("t_res"); ta = g("t_adm"); tar = g("t_arr"); trn = g("t_run"); tf = g("t_ft"); te = send + fl(r["total"])
            seg = [("unvisited", send, tv), ("lookup", tv, tr), ("admit", tr, ta)] + ([("load", ta, tar), ("promote", tar, trn)] if tar is not None else []) + [("prefill", trn, tf), ("decode", tf, te)]
            for name, x0, x1 in seg:
                if x0 is None or x1 is None or x1 - x0 < 0.02: continue
                lab, col = next((l, c) for n, l, c in PH if n == name)
                ax.barh(pos, x1 - x0, left=x0, height=0.62, color=col, edgecolor="white", linewidth=0.4, label=lab if name not in seen else None); seen.add(name)
            ax.plot([tf], [pos], marker="|", color="k", markersize=13, markeredgewidth=1.6)
            ax.text(te + 0.12, pos, f"{fl(r['ttft']):.1f} s", va="center", fontsize=10.5)
            table.append([ttl, NAMES[pos].replace("\n", " "), round(send, 2), round(fl(r["ttft"]), 2), round(fl(r["total"]), 2)])
        ax.set_yticks(sorted(R)); ax.set_yticklabels([NAMES[p] for p in sorted(R)], fontsize=10); ax.invert_yaxis(); ax.set_title(ttl + "   (number at the end of a row = time to first token)", fontsize=11, loc="left")
    axes[1].set_xlabel("time since the long request was sent (seconds); black tick = first token", fontsize=11); axes[0].set_xlim(0, 10.6)
    h, l = [], []
    for ax in axes:
        for hh, ll in zip(*ax.get_legend_handles_labels()):
            if ll not in l: h.append(hh); l.append(ll)
    order = [n for _, n, _ in PH]; hl = sorted(zip(h, l), key=lambda x: order.index(x[1]))
    fig.tight_layout(rect=(0, 0.12, 1, 1)); fig.legend([x[0] for x in hl], [x[1] for x in hl], fontsize=10, frameon=False, loc="lower center", ncol=3, columnspacing=1.5, handlelength=1.4)
    save(fig, "f04_timeline", table, ["server", "request", "sent at (s)", "time to first token (s)", "request time (s)"], f"{C1C}/c1c-base-adm-requests.csv, c1c-tokfast512-sync-adm-requests.csv (repetition 0, blocker 28,000 tokens)")

# ---------------------------------------------------------------- f05: trace replays
def f05():
    # (revised 2026-11-11) panel (a): stock, prototype (token reserve), hits first with perfect knowledge; panel (b): stock, prototype (small requests may
    # pass a blocked one for up to 30 s), the existing option "shortest prompt first", hits first with perfect knowledge; panel (c): KV saved
    proto04 = "tool04-320-p2" if os.path.exists(os.path.join(REPLAY, "tool04-320-p2-adm-requests.csv")) else "tool04-320-tokfast11"
    TOT = {}; MAX = {}
    def classes(stock, others):
        S = {r["rid"][len(stock) + 1:]: r for r in rows(stock)}; out = {}
        for tag in [stock] + others:
            D = {r["rid"][len(tag) + 1:]: r for r in rows(tag)}
            out[tag] = [mean([fl(D[k]["ttft"]) for k, r in S.items() if (c is None or r["cat"] == c) and k in D]) for c in ("host≥50%", "GPU≥50%", "miss<10%", None)]
            TOT[tag] = mean([fl(r["total"]) for r in D.values()]); MAX[tag] = max(fl(r["ttft"]) for r in D.values())
        return out, [sum(1 for r in S.values() if c is None or r["cat"] == c) for c in ("host≥50%", "GPU≥50%", "miss<10%", None)]
    ex = lambda t: os.path.exists(os.path.join(REPLAY, t + "-adm-requests.csv"))
    sa = [("tool04-320-base", "stock", "C0"), (proto04, "prototype: keep part of each step\nfor short work", "C1")] + ([("tool04-320-priohits", "hits first, with perfect knowledge", "C2")] if ex("tool04-320-priohits") else [])
    sb = [("tool08-320-base", "stock", "C0")] + [(t, l, c) for t, l, c in (("tool08-320-skip30", "prototype: requests that fit may pass\na blocked one, for up to 30 s", "C1"),
          ("tool08-320-priohits", "hits first, with perfect knowledge", "C2"), ("tool08-320-priolen", "shortest prompt first\n(an option vLLM already has)", "C3")) if ex(t)]
    A, nA = classes(sa[0][0], [t for t, _, _ in sa[1:]]); B, nB = classes(sb[0][0], [t for t, _, _ in sb[1:]] + (["tool08-320-p2"] if ex("tool08-320-p2") else []))
    st = {t: sum(fl(r["store_bytes"]) or 0 for r in rows(t)) / 1e9 for t in ("tool08-320-base", "tool08-320-storefix")}
    fig, ax = plt.subplots(1, 3, figsize=(12.3, 3.7), gridspec_kw=dict(width_ratios=[1.3, 1.7, 0.62])); table = []
    names = lambda n: [f"host hits\n(n = {n[0]})", f"GPU hits\n(n = {n[1]})", f"misses\n(n = {n[2]})", f"all requests\n(n = {n[3]})"]
    x = np.arange(4)
    for a, series, D, n, ttl, ymax, fs in ((ax[0], sa, A, nA, "(a) Normal load: the server keeps up", 13.5, 9.5), (ax[1], sb, B, nB, "(b) Overload: requests arrive twice as fast", 39, 8.5)):
        w = 0.84 / len(series)
        for j, (t, lab, col) in enumerate(series):
            b = a.bar(x + (j - (len(series) - 1) / 2) * w, D[t], w, color=col, label=lab); label(a, b, lambda v: f"{v:.1f}", 0.15, fs)
        a.set_xticks(x); a.set_xticklabels(names(n), fontsize=10); a.set_ylabel("time to first token, mean (s)"); a.set_ylim(0, ymax); a.legend(frameon=False, loc="upper left", fontsize=8.6, ncol=1, labelspacing=0.35)
        a.set_title(ttl, fontsize=12.5)
    a = ax[2]; b = a.bar(["stock", "with the\nstore fix"], [st["tool08-320-base"], st["tool08-320-storefix"]], 0.55, color=["C0", "C1"]); label(a, b, lambda v: f"{v:.0f} GB", 1.5, 10.5)
    a.set_ylabel("KV saved to host memory (GB)"); a.set_ylim(0, 135); a.set_title("(c) KV saved, overload", fontsize=12.5)
    fig.tight_layout(w_pad=1.4)
    for load, D, n in (("normal load", A, nA), ("overload", B, nB)):
        for t, v in D.items(): table.append([load, t] + [round(z, 3) for z in v] + n + [round(TOT[t], 3), round(MAX[t], 1)])
    table += [["overload, KV stored (GB)", t, round(v, 1)] for t, v in st.items()]
    save(fig, "f05_results", table, ["load", "run", "host hits: mean TTFT (s)", "GPU hits", "misses", "all requests", "n host", "n GPU", "n miss", "n all", "mean request time, all requests (s)", "longest TTFT (s)"],
         "replay/" + ", ".join(t for t, _, _ in sa + sb) + ", tool08-320-p2, tool08-320-storefix (-adm-requests.csv); request classes fixed by the stock run")
    return proto04

# ---------------------------------------------------------------- f06: CosmoFlow reuse distance
def f06():
    txt = subprocess.run(["git", "-C", ROOT, "show", f"{COSMO[0]}:{COSMO[1]}"], capture_output=True, text=True, check=True).stdout
    T, E, F = [], [], []
    for l in txt.splitlines():
        p = l.split()
        if p and p[0] == "R": T.append(float(p[1])); E.append(int(p[2])); F.append(int(p[4]))
    o = np.argsort(np.array(T), kind="stable"); E = np.array(E)[o]; F = np.array(F)[o]; N = len(set(F.tolist())); last = {}; D = []
    for i, f in enumerate(F.tolist()):
        if f in last: D.append(i - last[f] - 1)
        last[f] = i
    D = np.array(D); rep = [int(sum(1 for c in np.bincount(F[E == e], minlength=N) if c > 1)) for e in sorted(set(E.tolist()))]
    # stack distance = number of DISTINCT other files read since the last read of the same file: an LRU cache of C files serves the read iff it is < C
    n = len(F); tree = [0] * (n + 1); lastpos = {}; SD = []
    def add(i, v):
        i += 1
        while i <= n: tree[i] += v; i += i & -i
    def pref(i):
        t = 0
        while i > 0: t += tree[i]; i -= i & -i
        return t
    for i, f in enumerate(F.tolist()):
        j = lastpos.get(f)
        if j is not None: SD.append(pref(i) - pref(j + 1)); add(j, -1)
        add(i, 1); lastpos[f] = i
    SD = np.array(SD); lru = {c: float((SD < c * N).mean()) for c in (0.25, 0.5, 0.75)}
    fig, ax = plt.subplots(1, 2, figsize=(12.3, 3.6), gridspec_kw=dict(width_ratios=[1.15, 1]))
    a = ax[0]; rng = np.random.RandomState(3); pick = sorted(rng.choice(N, 12, replace=False).tolist()); pos = {f: np.nonzero(F == f)[0] for f in pick}
    for k, f in enumerate(pick): a.scatter(pos[f] / 1000, [k] * len(pos[f]), s=42, color="C0", zorder=3); a.plot(pos[f] / 1000, [k] * len(pos[f]), color="C0", linewidth=0.8, alpha=0.5)
    for e in (1, 2): a.axvline(e * N / 1000, color="0.4", linestyle="--", linewidth=1)
    for e in range(3): a.text((e + 0.5) * N / 1000, 12.1, f"epoch {e + 1}", ha="center", fontsize=11)
    a.set_yticks(range(12)); a.set_yticklabels([f"file {f}" for f in pick], fontsize=9); a.set_ylim(-0.7, 13.0); a.set_xlim(0, 3 * N / 1000)
    a.set_xlabel("position in the run: number of files read so far (thousands)"); a.set_title("(a) When twelve files are read: once in every epoch", fontsize=12.5)
    a = ax[1]; a.hist(D / 1000, bins=60, color="C0"); a.axvline(N / 1000, color="0.4", linestyle="--", linewidth=1)
    a.text(0.63, 0.97, f"dashed line: one pass\nover the data\n= {N:,} files", transform=a.transAxes, fontsize=10, va="top")
    a.set_xlabel("reuse distance: other files read before the same file\nis read again (thousands)"); a.set_ylabel("number of re-reads"); a.set_title(f"(b) Reuse distance of all {len(D):,} re-reads", fontsize=12.5)
    a.text(0.02, 0.95, f"smallest {D.min():,}\nmean {D.mean():,.0f}\nlargest {D.max():,}", transform=a.transAxes, va="top", fontsize=10.5)
    fig.tight_layout(w_pad=2.5)
    stats = dict(files=N, epochs=3, re_reads=len(D), min=int(D.min()), p5=float(np.percentile(D, 5)), median=float(np.median(D)), mean=float(D.mean()), p95=float(np.percentile(D, 95)), max=int(D.max()),
                 share_below_half_pass=float((D < 0.5 * N).mean()), share_below_one_pass=float((D < N).mean()), files_read_twice_in_an_epoch=rep,
                 lru_hit_share_cache_25pct=lru[0.25], lru_hit_share_cache_50pct=lru[0.5], lru_hit_share_cache_75pct=lru[0.75])
    json.dump(stats, open(os.path.join(OUT, "f06_reuse-stats.json"), "w"), indent=1)
    save(fig, "f06_reuse", [[k, v] for k, v in stats.items()], ["quantity", "value"], f"git show {COSMO[0]}:{COSMO[1]} (the group's CosmoFlow run of 2026-10-27 on c33: 61,440 files, 3 epochs)")
    return stats

if __name__ == "__main__":
    f01(); f03(); f04(); p = f05(); s = f06()
    with open(os.path.join(OUT, "SOURCES.md"), "w") as f:
        f.write("# Figures of the 2026-11-10 deck: figure -> raw files\n\n| figure | raw data |\n|---|---|\n" + "".join(f"| {n} | {s_} |\n" for n, s_ in SOURCES))
        f.write(f"\nPrototype run used for the normal-load panel of f05: `{p}`.\n")
    print("prototype run of f05 (a):", p); print("reuse stats:", s)
