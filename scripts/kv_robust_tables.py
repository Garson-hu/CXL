#!/usr/bin/env python3
"""Markdown tables for the robust-admission study (2026-10-21, second round) from kv_admission_sim.py outputs.
usage: kv_robust_tables.py <dir> grid|regime|est|dyn|meta|agents|dec [trace]
Shares of the oracle's gain are on USABLE hits over LRU of the same run / capacity / scoring range."""
import csv, glob, json, os, sys
D, mode = sys.argv[1], sys.argv[2]; tr = sys.argv[3] if len(sys.argv) > 3 else None
def load(pattern):
    rows = []
    for f in sorted(glob.glob(f"{D}/{pattern}")):
        for r in csv.DictReader(open(f)): r["_f"] = os.path.basename(f).replace("-replay.csv", ""); rows.append(r)
    return rows
def fl(r, k, d=0.0):
    try: return float(r.get(k) or d)
    except (ValueError, TypeError): return d
LAB = {"lru": "LRU (first touch)", "slru": "SLRU 1/3", "2nd": "second touch", "2nd_int": "2nd_int (gap ≤ residence)", "2nd_int_auto": "2nd_int + regime switch", "tinylfu": "TinyLFU (adapted)", "oracle": "oracle"}
def share(r, lru, orc):
    g = fl(orc, "usable") - fl(lru, "usable"); return 100 * (fl(r, "usable") - fl(lru, "usable")) / g if g > 0 else float("nan")
def cell(r, lru, orc, tb=True):
    return f"{fl(r, 'usable_hit_share'):.3f}" + ("" if r["policy"] in ("lru", "oracle") else f" / {share(r, lru, orc):.0f}%") + (f" / {fl(r, 'written_TB'):.1f}" if tb else "")
if mode == "grid":
    rows = load(f"g-{tr}-c*-replay.csv"); G = {(int(r["cap"]), r["policy"], r["_f"].endswith("g64k")): r for r in rows}; caps = sorted({int(r["cap"]) for r in rows})
    cols = [("lru", False), ("slru", False), ("2nd", False), ("2nd", True), ("2nd_int", False), ("2nd_int", True), ("2nd_int_auto", False), ("2nd_int_auto", True), ("tinylfu", False), ("oracle", False)]
    print(f"**{tr}** — usable-prefix hit share / share of the oracle's usable-hit gain over LRU / TB written (scored half); 64k = bounded ghost of 64k entries, else unbounded\n")
    print("| capacity | " + " | ".join(LAB[p] + (" (64k)" if b else "") for p, b in cols) + " |"); print("|---|" + "---|" * len(cols))
    for c in caps:
        lru, orc = G.get((c, "lru", False)), G.get((c, "oracle", False))
        print(f"| {c} = {c * 67.1 / 1024:.0f} GiB | " + " | ".join(cell(G[(c, p, b)], lru, orc) if (c, p, b) in G else "–" for p, b in cols) + " |")
    print("\nRegime switches of `2nd_int_auto` (default rule: res, q 0.5, hold 30 s): final regime, number of switches, switch times (s since trace start : n = to normal, f = to filter)\n")
    for c in caps:
        for b in (False, True):
            r = G.get((c, "2nd_int_auto", b))
            if r: print(f"- {c * 67.1 / 1024:.0f} GiB{' (64k ghost)' if b else ''}: end {r['regime_end']}, {r['regime_switches']} switches, {r['switch_times'] or '–'}; residence p50 {fl(r, 'residence_p50_s'):.0f} s, admissions {int(fl(r, 'written_chunks'))}")
elif mode == "regime":
    for tag in ("sel", "test"):
        rows = load(f"reg-{tr}-c*-{tag}-*-replay.csv"); caps = sorted({int(r["cap"]) for r in rows})
        print(f"**{tr}, {'SELECTION half (requests 25–50%)' if tag == 'sel' else 'TEST half (requests 50–100%)'}** — share of that half's oracle gain over LRU (usable hits) / TB / switches\n")
        variants = sorted({r["_f"].split(f"-{tag}-")[1] for r in rows if r["policy"] == "2nd_int_auto"})
        print("| capacity | 2nd_int (no switch) | SLRU | " + " | ".join(variants) + " |"); print("|---|---|---|" + "---|" * len(variants))
        for c in caps:
            ref = {r["policy"]: r for r in rows if int(r["cap"]) == c and r["_f"].endswith("-ref")}; lru, orc = ref.get("lru"), ref.get("oracle")
            if not lru: continue
            cells = [f"{share(ref['2nd_int'], lru, orc):.0f}% / {fl(ref['2nd_int'], 'written_TB'):.1f}", f"{share(ref['slru'], lru, orc):.0f}%"]
            for v in variants:
                r = next((r for r in rows if int(r["cap"]) == c and r["policy"] == "2nd_int_auto" and r["_f"].endswith(f"-{tag}-{v}")), None)
                cells.append(f"{share(r, lru, orc):.0f}% / {fl(r, 'written_TB'):.1f} / {r['regime_switches']}→{r['regime_end'][0]}" if r else "–")
            print(f"| {c * 67.1 / 1024:.0f} GiB (LRU {fl(lru, 'usable_hit_share'):.3f}, oracle {fl(orc, 'usable_hit_share'):.3f}) | " + " | ".join(cells) + " |")
        print()
elif mode == "est":
    g = load(f"g-{tr}-c*-replay.csv"); rows = load(f"est-{tr}-c*-replay.csv"); caps = sorted({int(r["cap"]) for r in rows})
    print(f"**{tr}** — the estimator that drives the gap rule (test half): share of the oracle's gain / TB / residence p50 (all blocks; dead blocks) / estimate at the end\n")
    modes = ["evict", "evict50", "evict1000", "dead", "rate", "tail", "median"]
    for p in ("2nd_int", "2nd_int_auto"):
        print(f"`{p}`:\n\n| capacity | " + " | ".join(modes) + " |"); print("|---|" + "---|" * len(modes))
        for c in caps:
            lru = next((r for r in g if int(r["cap"]) == c and r["policy"] == "lru"), None); orc = next((r for r in g if int(r["cap"]) == c and r["policy"] == "oracle"), None)
            cells = []
            for m in modes:
                r = next((r for r in rows if int(r["cap"]) == c and r["policy"] == p and r["_f"].endswith(f"-{m}")), None)
                cells.append(f"{share(r, lru, orc):.0f}% / {fl(r, 'written_TB'):.1f} / {fl(r, 'residence_p50_s'):.0f}; {fl(r, 'residence_dead_p50_s'):.0f} / {r.get('residence_est_end_s') or '–'}" if r and lru else "–")
            print(f"| {c * 67.1 / 1024:.0f} GiB | " + " | ".join(cells) + " |")
        print()
    print("Estimator accuracy (from the `est-*` logs, estimator `evict` driving `2nd_int`): log10(estimate at admission / realized residence of that block when evicted without a hit), ages ≥ 1 s: bias, mean |.|, p50 |.|, p90 |.|, share within 2×\n")
    print("| capacity | estimator | n | bias (log10) | mean abs | p50 abs | p90 abs | within 2× |"); print("|---|---|---|---|---|---|---|---|")
    for c in caps:
        f = f"{D}/dump/est-{tr}-evict-2nd_int-{c}-res.json"
        if not os.path.exists(f): continue
        E = json.load(open(f))["errors"]
        for m in modes:
            e = E[m]
            if e["n"]: print(f"| {c * 67.1 / 1024:.0f} GiB | {m} | {e['n']} | {e['bias_log10']:+.2f} | {e['mean_abs_log10']:.2f} | {e['p50_abs_log10']:.2f} | {e['p90_abs_log10']:.2f} | {100 * e['within_2x']:.0f}% |")
elif mode == "dyn":
    for tr_ in ("conversation", "toolagent"):
        for cap in (3200, 12800):
            g = load(f"g-{tr_}-c{cap}-replay.csv"); rows = load(f"dyn-{tr_}-c{cap}-*-replay.csv")
            print(f"**{tr_}, {cap * 67.1 / 1024:.0f} GiB, CONSTRUCTED dynamic load** — usable share / share of the oracle's gain / TB / switches (the oracle and LRU of the same run)\n")
            scen = sorted({r["_f"].split("-")[-1] for r in rows}); pols = ["lru", "slru", "2nd", "2nd_int", "2nd_int_auto", "tinylfu", "oracle"]
            print("| scenario | " + " | ".join(LAB[p] for p in pols) + " |"); print("|---|" + "---|" * len(pols))
            G0 = {r["policy"]: r for r in g}
            if G0: print("| stable (main grid) | " + " | ".join(cell(G0[p], G0["lru"], G0["oracle"]) + (f" / {G0[p]['regime_switches']}sw" if p == "2nd_int_auto" else "") for p in pols if p in G0) + " |")
            for s_ in scen:
                G = {r["policy"]: r for r in rows if r["_f"].endswith("-" + s_)}
                if "lru" in G: print(f"| {s_} | " + " | ".join(cell(G[p], G["lru"], G["oracle"]) + (f" / {G[p]['regime_switches']}sw" if p == "2nd_int_auto" else "") for p in pols if p in G) + " |")
            print()
    for mx in ("mix-interleave", "mix-phase"):
        rows = load(f"dyn-m-{mx}-replay.csv")
        if not rows: continue
        G = {r["policy"]: r for r in rows}
        print(f"**{mx} (CONSTRUCTED), 210 GiB** — " + "; ".join(f"{LAB[p]} {cell(G[p], G['lru'], G['oracle'])}" + (f" / {G[p]['regime_switches']} switches" if p == "2nd_int_auto" else "") for p in ("lru", "slru", "2nd", "2nd_int", "2nd_int_auto", "tinylfu", "oracle") if p in G) + "\n")
elif mode == "meta":
    for tr_ in ("conversation", "toolagent"):
        g = load(f"g-{tr_}-c3200-replay.csv"); rows = load(f"meta-{tr_}-c3200-*-replay.csv"); G0 = {r["policy"]: r for r in g}
        print(f"**{tr_}, 210 GiB — bounded history under a high unique-prefix arrival rate (SYNTHETIC churn of 50 never-reused blocks/s during the scored half; the scored requests are the real ones)** — usable share / share of the run's oracle gain / TB / ghost entries / forgotten re-lookups / Bloom FP\n")
        print("| run | policy | usable | TB | ghost entries max | forgotten re-lookups | Bloom FP admissions | residence p50 |"); print("|---|---|---|---|---|---|---|---|")
        for r in rows: print(f"| {r['_f'].replace(f'meta-{tr_}-c3200-', '')} | {LAB.get(r['policy'], r['policy'])} | {fl(r, 'usable_hit_share'):.3f} | {fl(r, 'written_TB'):.1f} | {int(fl(r, 'ghost_entries_max'))} | {int(fl(r, 'ghost_forgotten_relookups'))} | {int(fl(r, 'bloom_false_positives'))} | {fl(r, 'residence_p50_s'):.0f} |")
        if G0: print("| (no churn, main grid) | " + " / ".join(f"{LAB[p]} {fl(G0[p], 'usable_hit_share'):.3f}" for p in ("2nd", "2nd_int", "2nd_int_auto") if p in G0) + " | | | | | | |")
        print()
elif mode == "agents":
    for t in ("a-short-k16", "a-lt-k16-bg2"):
        rows = load(f"{t}-replay.csv"); G = {(int(r["cap"]), r["policy"]): r for r in rows}; caps = sorted({int(r["cap"]) for r in rows}); pols = [p for p in ("lru", "slru", "2nd", "2nd_int", "2nd_int_auto", "tinylfu", "oracle") if (caps[0], p) in G]
        print(f"**{t} (REAL agent trace)** — usable-prefix hit share / written chunks / share of the oracle's gain\n"); print("| capacity | " + " | ".join(LAB[p] for p in pols) + " |"); print("|---|" + "---|" * len(pols))
        for c in caps:
            lru, orc = G[(c, "lru")], G[(c, "oracle")]
            print(f"| {c} chunks | " + " | ".join(f"{fl(G[(c, p)], 'usable_hit_share'):.3f} / {int(fl(G[(c, p)], 'written_chunks'))}" + ("" if p in ("lru", "oracle") else f" / {share(G[(c, p)], lru, orc):.0f}%") + (f" / {G[(c, p)]['regime_switches']}sw→{G[(c, p)]['regime_end'][0]}" if p == "2nd_int_auto" else "") for p in pols) + " |")
        print()
elif mode == "dec":
    # per-decision accounting of the gap rule (estimator `evict`): what the residence estimate got wrong, using the block's future next-use gap for ACCOUNTING only
    for tr_ in ("conversation", "toolagent"):
        for cap in (800, 3200, 6400):
            f = f"{D}/dump/est-{tr_}-evict-2nd_int-{cap}-dec.csv"
            if not os.path.exists(f): continue
            n = adm = ref = 0; adm_hit = adm_dead = adm_dead_est_wrong = 0; ref_reuse_in_est = ref_reuse_in_real = 0; ref_no_reuse = 0; dead_ages = []
            rows = list(csv.DictReader(open(f)))
            real_res = [float(r["age"]) for r in rows if r["admitted"] == "1" and r["outcome"] == "dead" and r.get("age")]
            real_res.sort(); Rreal = real_res[len(real_res) // 2] if real_res else float("nan")
            for r in rows:
                n += 1; g = float(r["gap"]) if r["gap"] else None; est = float(r["residence_est"]) if r["residence_est"] else None; nxt = float(r["next_gap_future"]) if r["next_gap_future"] else None
                if r["admitted"] == "1":
                    adm += 1
                    if r["outcome"] == "hit": adm_hit += 1
                    elif r["outcome"] == "dead":
                        adm_dead += 1
                        if nxt is not None and est is not None and nxt <= est: adm_dead_est_wrong += 1       # the estimate said it would survive its (actual) next gap; it did not
                else:
                    ref += 1
                    if nxt is None: ref_no_reuse += 1
                    else:
                        if est is not None and nxt <= est: ref_reuse_in_est += 1                                   # refused by its last gap although its next use came within the estimated residence
                        if nxt <= Rreal: ref_reuse_in_real += 1
            print(f"**{tr_} {cap * 67.1 / 1024:.0f} GiB, `2nd_int` decisions on re-seen candidates (scored half, n = {n})**: admitted {adm} → hit before eviction {adm_hit} ({100 * adm_hit / max(1, adm):.0f}%), evicted dead {adm_dead} (of which {adm_dead_est_wrong} had their next use within the estimated residence = over-estimate cost, {100 * adm_dead_est_wrong / max(1, adm):.0f}% of admissions); refused {ref} → never reused {ref_no_reuse} ({100 * ref_no_reuse / max(1, ref):.0f}%), next use within the estimated residence {ref_reuse_in_est} ({100 * ref_reuse_in_est / max(1, ref):.0f}%: the last gap was a wrong predictor, not the estimate), within the realized dead residence ({Rreal:.0f} s) {ref_reuse_in_real}\n")
