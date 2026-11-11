#!/usr/bin/env python3
"""Figures of the 2026-11-10 GPU-KV admission study, part A (matplotlib defaults, white background).
  figA1-wait-by-reason       where the waiting time between queueing and RUNNING goes, per request category, for the given replays
  figA2-ttft-by-arrival      TTFT p50 per category split by the engine state at arrival (prefill in flight or not)
  fig1-occupancy-vs-wait     (required figure 1) left: free GPU KV blocks at the first admission attempt, relative to the request's need,
                             against the time from lookup result to admission: controlled probes (A3), external hit vs miss; right:
                             the replays' host-dominant hits, used share of the pool at arrival against the wait from queueing to
                             admission, split by whether a prefill was in flight at arrival
  fig2-length-vs-wait        (required figure 2) prefix length against TTFT and admission wait: A3 part 1, hit vs miss, by free-block level
usage: figs_adm.py <fig_dir> replay=<dir>:<tag>[,<tag>...] a3=<dir>:<tag>"""
import csv, os, re, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white", "font.size": 9, "axes.grid": True, "grid.alpha": 0.3, "grid.linewidth": 0.5})
FIG = sys.argv[1]; KW = dict(a.split("=", 1) for a in sys.argv[2:]); os.makedirs(FIG, exist_ok=True)
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def q(v, p):
    v = sorted(x for x in v if x is not None); return v[min(len(v) - 1, int(p * len(v)))] if v else None
def save(fig, name):
    fig.tight_layout(); fig.savefig(f"{FIG}/{name}.png", dpi=150, bbox_inches="tight"); fig.savefig(f"{FIG}/{name}.pdf", bbox_inches="tight"); plt.close(fig); print("wrote", name)
def nice(tag):
    """run tag -> panel title: <trace><speed>-<host tier GB>-base"""
    m = re.match(r"(tool|conv)(\d\d)-(\d+)-", tag)
    if not m: return tag
    return f"{'tool-agent' if m.group(1) == 'tool' else 'conversation'} trace at 0.{m.group(2)}× ({'sustainable load' if m.group(2) == '04' else 'overload'}), stock"
CATS = [("host≥50%", "host-dominant hit"), ("GPU≥50%", "GPU-prefix hit"), ("10–50%", "partial hit"), ("miss<10%", "miss")]
REASONS = [("budget", "token budget used by running requests\n(queue not scanned)"), ("budget_adm", "budget used by earlier admissions in the scan"),
           ("hol", "another request refused: scan stopped"), ("own", "own refusal (block gates)"), ("pending", "lookup pending"), ("other", "other")]
def reason_sums(d):
    out = {k: 0.0 for k, _ in REASONS}
    for k, v in d.items():
        if not k.startswith("w_") or k.startswith(("w_pre_", "w_lookup_", "w_admit_", "w_promote_")): continue
        x = fl(v) or 0.0; r = k[2:]
        key = "hol" if r.startswith("hol:") else "own" if r.startswith("own:") else r if r in out else "other"
        out[key] += x
    return out

if "replay" in KW:
    rdir, tags = KW["replay"].split(":"); tags = tags.split(",")
    fig, axes = plt.subplots(1, len(tags), figsize=(4.3 * len(tags) + 2.2, 3.6), sharey=False, squeeze=False)
    for ax, tag in zip(axes[0], tags):
        R = list(csv.DictReader(open(f"{rdir}/{tag}-adm-requests.csv"))); bottom = [0.0] * len(CATS)
        for rk, rl in REASONS:
            vals = []
            for ck, _ in CATS:
                v = [reason_sums(d)[rk] for d in R if d["cat"] == ck]; vals.append(sum(v) / len(v) if v else 0.0)
            ax.bar(range(len(CATS)), vals, 0.62, bottom=bottom, label=rl, edgecolor="white", linewidth=0.8); bottom = [b + x for b, x in zip(bottom, vals)]
        ax.set_xticks(range(len(CATS))); ax.set_xticklabels([f"{cl.replace(' hit', chr(10) + 'hit')}\n(n = {sum(1 for d in R if d['cat'] == ck)})" for ck, cl in CATS], fontsize=8)
        ax.set_title(nice(tag), fontsize=9); ax.grid(axis="x", visible=False)
    axes[0][0].set_ylabel("waiting time before RUNNING,\nmean per request (s)")
    axes[0][-1].legend(fontsize=7, frameon=False, loc="center left", bbox_to_anchor=(1.01, 0.5))
    save(fig, "figA1-wait-by-reason")
    fig, axes = plt.subplots(1, len(tags), figsize=(4.3 * len(tags) + 1.8, 3.4), squeeze=False)
    for ax, tag in zip(axes[0], tags):
        R = list(csv.DictReader(open(f"{rdir}/{tag}-adm-requests.csv"))); w = 0.36
        for j, (lab, sel) in enumerate((("no prefill in flight at arrival", lambda d: fl(d.get("arr_infl")) == 0), ("a prefill in flight at arrival", lambda d: (fl(d.get("arr_infl")) or 0) > 0))):
            vals = [q([fl(d["ttft"]) for d in R if d["cat"] == ck and sel(d)], .5) or 0 for ck, _ in CATS]
            ns = [sum(1 for d in R if d["cat"] == ck and sel(d)) for ck, _ in CATS]
            bars = ax.bar([i + (j - 0.5) * w for i in range(len(CATS))], vals, w, label=lab, edgecolor="white", linewidth=0.8)
            for b, v, n in zip(bars, vals, ns): ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.2f}\n[{n}]", ha="center", va="bottom", fontsize=6.5)
        ax.set_xticks(range(len(CATS))); ax.set_xticklabels([cl.replace(" hit", "\nhit") for _, cl in CATS], fontsize=8); ax.set_title(nice(tag), fontsize=9); ax.grid(axis="x", visible=False)
        ax.set_ylim(0, max(ax.get_ylim()[1], 1) * 1.15)
    axes[0][0].set_ylabel("TTFT p50 (s); [number of requests]"); axes[0][-1].legend(fontsize=7, frameon=False, loc="center left", bbox_to_anchor=(1.01, 0.5))
    save(fig, "figA2-ttft-by-arrival")

if "a3" in KW:
    adir, tag = KW["a3"].split(":"); P = []
    for r in csv.DictReader(open(f"{adir}/{tag}-adm-requests.csv")):
        m = re.match(rf"{re.escape(tag)}-(p\d)-(.+)-r(\d+)-p(\d+)-(host|cold)-L(\d+)$", r["rid"])
        if not m: continue
        P.append(dict(part=m.group(1), tr=m.group(2), ty=m.group(5), L=int(m.group(6)), ttft=fl(r["ttft"]), free=fl(r["first_free"]), full=fl(r["first_full"]),
                      wait=(fl(r["t_adm"]) - fl(r["t_res"])) if (fl(r["t_adm"]) is not None and fl(r["t_res"]) is not None) else None))
    P1 = [p for p in P if p["part"] in ("p1", "p2") and p["free"] and p["full"]]
    two = "replay" in KW
    fig, axs = plt.subplots(1, 2 if two else 1, figsize=(10.6 if two else 5.4, 3.7), squeeze=False); ax = axs[0][0]
    for ty, lab, mk in (("host", "external hit", "o"), ("cold", "miss of the same length", "x")):
        v = [p for p in P1 if p["ty"] == ty]
        ax.scatter([p["free"] / p["full"] for p in v], [p["wait"] for p in v], s=22, marker=mk, label=f"{lab} (n = {len(v)})", alpha=0.85, linewidths=1.0)
    ax.axvline(1.0, color="0.4", linewidth=0.8, linestyle="--"); ax.text(1.02, ax.get_ylim()[1] * 0.55, "free blocks = blocks\nof the full sequence", fontsize=7, color="0.3")
    ax.set_xscale("log"); ax.set_xticks([0.6, 1, 1.5, 2, 3]); ax.set_xticklabels(["0.6", "1", "1.5", "2", "3"]); ax.minorticks_off()
    ax.set_xlabel("free GPU KV blocks at the first admission attempt / blocks the request needs"); ax.set_ylabel("lookup result → admitted (s)")
    ax.set_title("Controlled probes (holders released 3 s after the probe when it does not fit)", fontsize=8); ax.legend(fontsize=7, frameon=False, loc="center right")
    if two:
        ax = axs[0][1]; rdir, tags = KW["replay"].split(":"); H = []
        for tag in tags.split(","):
            for d in csv.DictReader(open(f"{rdir}/{tag}-adm-requests.csv")):
                if d["cat"] == "host≥50%" and fl(d.get("arr_free")) is not None and fl(d.get("t_adm")) is not None and fl(d.get("t_q")) is not None:
                    H.append((1 - fl(d["arr_free"]), max(fl(d["t_adm"]) - fl(d["t_q"]), 1e-3), (fl(d.get("arr_infl")) or 0) > 0))
        for infl, lab, mk, col in ((False, "no prefill in flight at arrival", "o", "C0"), (True, "a prefill in flight at arrival", "^", "C3")):
            v = [h for h in H if h[2] == infl]
            ax.scatter([h[0] for h in v], [h[1] for h in v], s=14, marker=mk, color=col, alpha=0.6, linewidths=0, label=f"{lab} (n = {len(v)})")
        ax.set_yscale("log"); ax.set_xlabel("GPU KV blocks in use at arrival (share of the pool)"); ax.set_ylabel("queued → load admitted (s)")
        ax.set_title(f"Host-dominant hits of the stock replays ({len(tags.split(chr(44)))} runs)", fontsize=8); ax.legend(fontsize=7, frameon=False, loc="upper left")
    save(fig, "fig1-occupancy-vs-wait")
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.4))
    Ls = sorted({p["L"] for p in P if p["part"] == "p1"})
    for ax, key, yl in ((axes[0], "wait", "lookup result → admitted (s)"), (axes[1], "ttft", "TTFT (s)")):
        for ty, lab, mk in (("host", "external hit", "o"), ("cold", "miss", "x")):
            for lvl, ls, ll in (("f3", "-", "free = 3.0 × need"), ("f1.5", "--", "free = 1.5 × need"), ("f0.6", ":", "free = 0.6 × need (release after 3 s)")):
                ys = [q([p[key] for p in P if p["part"] == "p1" and p["ty"] == ty and p["L"] == L and p["tr"].split("-")[1] == lvl], .5) for L in Ls]
                ax.plot(Ls, ys, marker=mk, linestyle=ls, linewidth=1.2, markersize=5, color="C0" if ty == "host" else "C1", label=f"{lab}, {ll}")
        ax.set_xscale("log", base=2); ax.set_xticks(Ls); ax.set_xticklabels([f"{L // 1024}k" for L in Ls]); ax.set_xlabel("prefix length (tokens; + 256 fresh tokens)"); ax.set_ylabel(yl)
    axes[1].legend(fontsize=7, frameon=False, loc="center left", bbox_to_anchor=(1.01, 0.5))
    save(fig, "fig2-length-vs-wait")
