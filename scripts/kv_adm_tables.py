#!/usr/bin/env python3
"""Markdown tables for the adaptive admission study (2026-10-21) from kv_admission_sim.py CSVs.
usage: kv_adm_tables.py <dir> grid|ghost|ablation|tune|mix|agents|gpu|fifths [trace]
Shares of the oracle's gain are computed on USABLE hits (prefix-aware) over LRU of the same trace / capacity / scoring range."""
import csv, glob, os, sys
D, mode = sys.argv[1], sys.argv[2]; tr = sys.argv[3] if len(sys.argv) > 3 else None
def load(pattern):
    rows = []
    for f in sorted(glob.glob(f"{D}/{pattern}")):
        for r in csv.DictReader(open(f)): r["_f"] = os.path.basename(f).replace("-replay.csv", ""); rows.append(r)
    return rows
def fl(r, k, d=0.0):
    try: return float(r.get(k) or d)
    except ValueError: return d
LAB = {"lru": "LRU (first touch)", "slru": "SLRU 1/3", "2q": "2Q", "arc": "ARC", "tinylfu": "TinyLFU (adapted, no window)", "wtinylfu": "W-TinyLFU", "2nd": "second touch", "2nd_int": "second touch + gap ≤ residence", "adapt2": "adapt2 (first touch on/off)", "adaptive": "adaptive (class tables)", "lhd": "learned class (2026-10-20)", "oracle": "oracle"}
ORDER = ["lru", "slru", "2q", "arc", "tinylfu", "wtinylfu", "2nd", "2nd_int", "adapt2", "adaptive", "lhd", "oracle"]
def ref(rows, cap):
    G = {(int(r["cap"]), r["policy"]): r for r in rows}; return G.get((cap, "lru")), G.get((cap, "oracle"))
def share(r, lru, orc):
    g = fl(orc, "usable") - fl(lru, "usable"); return 100 * (fl(r, "usable") - fl(lru, "usable")) / g if g > 0 else float("nan")
if mode == "grid":
    rows = load(f"g-{tr}-c*-replay.csv"); G = {(int(r["cap"]), r["policy"]): r for r in rows}; caps = sorted({int(r["cap"]) for r in rows})
    pols = [p for p in ORDER if (caps[0], p) in G]
    print(f"**{tr}** — usable-prefix hit share / TB written (scored half) / share of the oracle's usable-hit gain over LRU\n")
    print("| capacity | " + " | ".join(LAB[p] for p in pols) + " |"); print("|---|" + "---|" * len(pols))
    for c in caps:
        lru, orc = ref(rows, c); cells = []
        for p in pols:
            r = G[(c, p)]; cells.append(f"{fl(r, 'usable_hit_share'):.3f} / {fl(r, 'written_TB'):.1f}" + ("" if p in ("lru", "oracle") else f" / {share(r, lru, orc):.0f}%"))
        print(f"| {c} blocks = {c * 67.1 / 1024:.0f} GiB | " + " | ".join(cells) + " |")
    print("\nAdmission quality (scored half): admissions / useful-admission rate / refused (reused later; within 300 s) / misses after refusal / after eviction / residence p50 / residence estimate / dead occupancy share / recomputed tokens (M)\n")
    print("| capacity | policy | admissions | useful % | refused (reused; ≤ 300 s) | miss after refusal / eviction / new | residence p50 / est. (s) | dead occ. | recompute Mtok |"); print("|---|---|---|---|---|---|---|---|---|")
    for c in caps:
        for p in pols:
            r = G[(c, p)]; w = fl(r, "written_chunks"); useful = 100 * (1 - fl(r, "admitted_never_reused") / max(1, w))
            print(f"| {c * 67.1 / 1024:.0f} GiB | {LAB[p]} | {int(w)} | {useful:.0f}% | {int(fl(r, 'bypass_total'))} ({int(fl(r, 'bypass_reused_later'))}; {int(fl(r, 'bypass_reused_300s'))}) | {int(fl(r, 'miss_after_bypass'))} / {int(fl(r, 'miss_after_eviction'))} / {int(fl(r, 'miss_new'))} | {fl(r, 'residence_p50_s'):.0f} / {r.get('residence_est_end_s') or '–'} | {fl(r, 'dead_occupancy_share'):.2f} | {fl(r, 'recomputed_tokens') / 1e6:.1f} |")
elif mode == "ghost":
    g = load(f"g-{tr}-c*-replay.csv"); rows = load(f"gh-{tr}-c*-replay.csv")
    print(f"**{tr}** — bounded ghost history: usable-prefix hit share / share of the oracle's gain / TB written / re-lookups the ghost had forgotten / ghost entries (max) / ghost bytes / Bloom false-positive admissions\n")
    print("| capacity | ghost | policy | hit share | oracle gain | TB | forgotten re-lookups | entries | bytes | Bloom FP |"); print("|---|---|---|---|---|---|---|---|---|---|")
    for r in sorted(rows, key=lambda r: (int(r["cap"]), r["_f"], r["policy"])):
        c = int(r["cap"]); lru, orc = ref(g, c)
        spec = r["_f"].split("-")[-1]; spec = spec.replace("bloom", "Bloom ").replace("_", ",").replace("ttl", "TTL ").replace("g", "", 1) if spec.startswith("g") and not spec.startswith("gh") else spec
        print(f"| {c * 67.1 / 1024:.0f} GiB | {r['_f'].split('-')[-1]} | {LAB[r['policy']]} | {fl(r, 'usable_hit_share'):.3f} | {share(r, lru, orc) if lru else float('nan'):.0f}% | {fl(r, 'written_TB'):.1f} | {int(fl(r, 'ghost_forgotten_relookups'))} | {int(fl(r, 'ghost_entries_max'))} | {int(fl(r, 'ghost_bytes')) / 1e6:.2f} MB | {int(fl(r, 'bloom_false_positives'))} |")
elif mode == "ablation":
    g = load(f"g-{tr}-c*-replay.csv"); rows = load(f"ab-{tr}-c*-replay.csv")
    print(f"**{tr}** — adaptive ablations: usable-prefix hit share / share of the oracle's gain / TB written / final threshold / classes\n")
    print("| capacity | variant | policy | hit share | oracle gain | TB | threshold | classes |"); print("|---|---|---|---|---|---|---|---|")
    for c in sorted({int(r["cap"]) for r in rows}):
        lru, orc = ref(g, c)
        for p in ("adaptive", "adapt2", "2nd", "2nd_int"):
            r0 = next((r for r in g if int(r["cap"]) == c and r["policy"] == p), None)
            if r0: print(f"| {c * 67.1 / 1024:.0f} GiB | (reference, main grid) | {LAB[p]} | {fl(r0, 'usable_hit_share'):.3f} | {share(r0, lru, orc):.0f}% | {fl(r0, 'written_TB'):.1f} | {r0['threshold_end']} | {r0['classes']} |")
        for r in sorted((r for r in rows if int(r["cap"]) == c), key=lambda r: (r["_f"], r["policy"])):
            print(f"| {c * 67.1 / 1024:.0f} GiB | {r['_f'].split('-', 3)[-1]} | {LAB[r['policy']]} | {fl(r, 'usable_hit_share'):.3f} | {share(r, lru, orc) if lru else float('nan'):.0f}% | {fl(r, 'written_TB'):.1f} | {r['threshold_end']} | {r['classes']} |")
elif mode == "tune":
    rows = load(f"tune-{tr}-c*-replay.csv")
    print(f"**{tr}** — parameter selection on the FIRST half (scored requests 25–50%, cache warmed on 0–25%): usable-prefix hit share of `adaptive` / share of that half's oracle gain over LRU\n")
    caps = sorted({int(r["cap"]) for r in rows}); print("| capacity | " + " | ".join(f"τ {tau} / prior {pr}" for tau in (150, 300, 600) for pr in (2, 10, 50)) + " | chosen |"); print("|---|" + "---|" * 10)
    for c in caps:
        G = {(r["_f"], r["policy"]): r for r in rows if int(r["cap"]) == c}; cells = []; best = None
        for tau in (150, 300, 600):
            for pr in (2, 10, 50):
                f = f"tune-{tr}-c{c}-tau{tau}-pr{pr}"; r = G.get((f, "adaptive")); lru = G.get((f, "lru")); orc = G.get((f, "oracle"))
                if r is None: cells.append("–"); continue
                s = share(r, lru, orc); cells.append(f"{fl(r, 'usable_hit_share'):.3f} / {s:.0f}%")
                if best is None or s > best[0]: best = (s, tau, pr)
        print(f"| {c * 67.1 / 1024:.0f} GiB | " + " | ".join(cells) + f" | τ {best[1]} / prior {best[2]} |")
elif mode == "mix":
    for mx in ("mix-interleave", "mix-phase"):
        rows = load(f"m-{mx}-replay.csv") + load(f"m-{mx}-cold-replay.csv") + load(f"m-{mx}-frozen-replay.csv") + load(f"m-{mx}-g16k-replay.csv")
        lru, orc = ref(rows, 3200)
        print(f"**{mx} (CONSTRUCTED from the two real traces), 3200 blocks = 210 GiB** — usable-prefix hit share / share of the oracle's gain / TB written / usable hits per fifth\n")
        print("| run | policy | hit share | oracle gain | TB | hits per fifth |"); print("|---|---|---|---|---|---|")
        for r in rows: print(f"| {r['_f']} | {LAB[r['policy']]} | {fl(r, 'usable_hit_share'):.3f} | {share(r, lru, orc):.0f}% | {fl(r, 'written_TB'):.1f} | {r['hits_by_fifth']} |")
        print()
elif mode == "agents":
    for t in ("a-short-k16", "a-lt-k16-bg2"):
        rows = load(f"{t}-replay.csv"); G = {(int(r["cap"]), r["policy"]): r for r in rows}; caps = sorted({int(r["cap"]) for r in rows}); pols = [p for p in ORDER if (caps[0], p) in G]
        print(f"**{t} (REAL agent trace)** — usable-prefix hit share / written chunks / share of the oracle's gain\n"); print("| capacity | " + " | ".join(LAB[p] for p in pols) + " |"); print("|---|" + "---|" * len(pols))
        for c in caps:
            lru, orc = ref(rows, c)
            print(f"| {c} chunks | " + " | ".join(f"{fl(G[(c, p)], 'usable_hit_share'):.3f} / {int(fl(G[(c, p)], 'written_chunks'))}" + ("" if p in ("lru", "oracle") else f" / {share(G[(c, p)], lru, orc):.0f}%") for p in pols) + " |")
        print()
elif mode == "gpu":
    for t in ("conversation", "toolagent"):
        g = load(f"g-{t}-c3200-replay.csv"); rows = load(f"gpu-{t}-c3200-*-replay.csv")
        print(f"**{t}, 210 GiB host cache with a GPU prefix cache in front** — served share (GPU or host, usable prefix) / host-hit share / share of the oracle's gain (served) / TB written\n")
        print("| GPU blocks | ghost source | " + " | ".join(LAB[p] for p in ("lru", "2nd", "2nd_int", "adapt2", "adaptive", "oracle")) + " |"); print("|---|---|" + "---|" * 6)
        r0 = {r["policy"]: r for r in g}; lru, orc = r0.get("lru"), r0.get("oracle")
        if lru: print("| 0 (every lookup reaches the host) | – | " + " | ".join(f"{fl(r0[p], 'usable_hit_share'):.3f} / {fl(r0[p], 'reuse_hit_share'):.3f}" + ("" if p in ("lru", "oracle") else f" / {share(r0[p], lru, orc):.0f}%") + f" / {fl(r0[p], 'written_TB'):.1f}" for p in ("lru", "2nd", "2nd_int", "adapt2", "adaptive", "oracle") if p in r0) + " |")
        for f in sorted({r["_f"] for r in rows}):
            G = {r["policy"]: r for r in rows if r["_f"] == f}; lru, orc = G.get("lru"), G.get("oracle"); gb, src = f.split("-")[-2][1:], f.split("-")[-1]
            print(f"| {gb} ({int(gb) * 67.1 / 1024:.0f} GiB) | {src} | " + " | ".join(f"{fl(G[p], 'usable_hit_share'):.3f} / {fl(G[p], 'reuse_hit_share'):.3f}" + ("" if p in ("lru", "oracle") else f" / {share(G[p], lru, orc):.0f}%") + f" / {fl(G[p], 'written_TB'):.1f}" for p in ("lru", "2nd", "2nd_int", "adapt2", "adaptive", "oracle") if p in G) + " |")
        print()
elif mode == "fifths":
    rows = load(f"g-{tr}-c3200-replay.csv") + load(f"ab-{tr}-c3200-frozen-replay.csv") + load(f"ab-{tr}-c3200-cold-replay.csv")
    print(f"**{tr}, 210 GiB — usable hits per chronological fifth of the scored half (walk-forward)**\n"); print("| run | policy | fifth 1 | 2 | 3 | 4 | 5 | accesses per fifth |"); print("|---|---|---|---|---|---|---|---|")
    for r in rows: print(f"| {r['_f']} | {LAB[r['policy']]} | " + " | ".join(r["hits_by_fifth"].split("/")) + f" | {r['acc_by_fifth']} |")
elif mode == "sel":
    LABS = {"A": "A: adaptive, classes = touch count, fixed threshold 0.5, τ 300 (selected: best first-half mean)", "B": "B: adaptive, classes = touch count × gap, replanned threshold, τ 150 (runner-up)", "C": "C: adapt2, τ 150", "D": "D: second touch + gap ≤ residence, 64k-entry ghost", "D2": "D: second touch, 64k-entry ghost"}
    for tr in ("conversation", "toolagent", "synthetic"):
        g = load(f"g-{tr}-c*-replay.csv"); rows = load(f"sel-{tr}-c*-replay.csv"); caps = sorted({int(r["cap"]) for r in rows})
        print(f"**{tr}** — TEST half, configurations selected on the first half: usable-prefix hit share / share of the oracle's gain / TB written\n")
        print("| capacity | " + " | ".join(LABS[k] for k in ("A", "B", "C", "D", "D2")) + " | reference: 2nd_int unbounded ghost (main grid) |"); print("|---|" + "---|" * 6)
        for c in caps:
            lru, orc = ref(g, c); cells = []
            for k in ("A", "B", "C", "D", "D2"):
                tag = k if k != "D2" else "D"; pol = {"A": "adaptive", "B": "adaptive", "C": "adapt2", "D": "2nd_int", "D2": "2nd"}[k]
                r = next((r for r in rows if int(r["cap"]) == c and r["_f"].endswith(f"-{tag}") and r["policy"] == pol), None)
                cells.append(f"{fl(r, 'usable_hit_share'):.3f} / {share(r, lru, orc):.0f}% / {fl(r, 'written_TB'):.1f}" if r else "–")
            r0 = next((r for r in g if int(r["cap"]) == c and r["policy"] == "2nd_int"), None)
            cells.append(f"{fl(r0, 'usable_hit_share'):.3f} / {share(r0, lru, orc):.0f}% / {fl(r0, 'written_TB'):.1f}" if r0 else "–")
            print(f"| {c * 67.1 / 1024:.0f} GiB | " + " | ".join(cells) + " |")
        print()
    for mx in ("mix-interleave", "mix-phase"):
        g = load(f"m-{mx}-replay.csv"); rows = load(f"sel-m-{mx}-*-replay.csv"); lru, orc = ref(g, 3200)
        if not rows: continue
        print(f"**{mx} (CONSTRUCTED), 210 GiB** — " + "; ".join(f"{LABS[k].split(':')[0]} {fl(r, 'usable_hit_share'):.3f} / {share(r, lru, orc):.0f}% / {fl(r, 'written_TB'):.1f} TB" for k in ("A", "B", "C", "D", "D2") for r in rows if r["_f"].endswith("-" + (k if k != "D2" else "D")) and r["policy"] == {"A": "adaptive", "B": "adaptive", "C": "adapt2", "D": "2nd_int", "D2": "2nd"}[k]) + "\n")
