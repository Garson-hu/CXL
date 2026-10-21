#!/usr/bin/env python3
"""Markdown tables for the admission study (2026-10-20) from kv_agent_replay.py CSVs (prefix-aware, with the admission
decomposition columns). usage: kv_admission_tables.py <dir> grid|variants|fifths|agents [trace]"""
import csv, glob, os, sys
D, mode = sys.argv[1], sys.argv[2]; tr = sys.argv[3] if len(sys.argv) > 3 else None
def load(pattern):
    rows = []
    for f in sorted(glob.glob(f"{D}/{pattern}")):
        for r in csv.DictReader(open(f)): r["_file"] = os.path.basename(f); rows.append(r)
    return rows
def fl(r, k, d=0.0):
    try: return float(r.get(k) or d)
    except ValueError: return d
LAB = {"lru": "LRU", "slru": "SLRU", "static_d8": "static: position ≥ 8", "static_p8": "static: prefix ≥ 8", "static_n8": "static: 8th+ new block", "static_dp8_8": "static: pos ≥ 8 & prefix ≥ 8", "lhd": "learned class (lhd)", "cond": "learned root (cond)", "oracle": "oracle", "static_2nd1": "static: second touch", "static_2nd8": "static: second touch, first 8 free", "static_2nd4": "static: second touch, first 4 free", "event_cont": "agent continue", "static_n4": "static: 4th+ new", "static_d6": "static: position ≥ 6"}
if mode == "grid":
    rows = load(f"g-{tr}-c*-replay.csv") + load(f"s2-{tr}-c*-replay.csv"); G = {(int(r["cap"]), r["policy"]): r for r in rows}; caps = sorted({int(r["cap"]) for r in rows})
    pols = [p for p in ("lru", "slru", "static_d8", "static_p8", "static_n8", "static_dp8_8", "static_2nd1", "static_2nd8", "lhd", "cond", "oracle") if (caps[0], p) in G]
    print(f"**{tr}** — usable-prefix hit share | TB written (scored half) | share of the oracle's hit gain over LRU | net hits vs LRU\n")
    print("| capacity | " + " | ".join(LAB.get(p, p) for p in pols) + " |"); print("|---|" + "---|" * len(pols))
    for c in caps:
        lru, orc = G[(c, "lru")], G[(c, "oracle")]; gain = fl(orc, "hits") - fl(lru, "hits"); cells = []
        for p in pols:
            r = G[(c, p)]; sh = 100 * (fl(r, "hits") - fl(lru, "hits")) / gain if gain > 0 else float("nan")
            cells.append(f"{fl(r, 'usable_hit_share'):.3f} / {fl(r, 'written_chunks') * 67.1 / 1e6:.1f} TB" + ("" if p in ("lru", "oracle") else f" / {sh:.0f}% / {int(fl(r, 'hits') - fl(lru, 'hits')):+d}"))
        print(f"| {c} blocks = {c * 67.1 / 1024:.0f} GiB | " + " | ".join(cells) + " |")
    print("\nDecomposition (scored half): bypassed total / of which reused later (within 60 s, 300 s) | admitted never reused | misses after bypass / after eviction / on new blocks | feedback delay p50 / p90 s | online residence estimate at the end\n")
    print("| capacity | policy | bypassed (reused later; ≤ 60 s; ≤ 300 s) | admitted, never reused | misses: after bypass / after eviction / new | feedback delay p50 / p90 | residence est. |"); print("|---|---|---|---|---|---|---|")
    for c in caps:
        for p in pols:
            r = G[(c, p)]
            print(f"| {c * 67.1 / 1024:.0f} GiB | {LAB.get(p, p)} | {int(fl(r, 'bypass_total'))} ({int(fl(r, 'bypass_reused_later'))}; {int(fl(r, 'bypass_reused_60s'))}; {int(fl(r, 'bypass_reused_300s'))}) | {int(fl(r, 'admitted_never_reused'))} | {int(fl(r, 'miss_after_bypass'))} / {int(fl(r, 'miss_after_eviction'))} / {int(fl(r, 'miss_new'))} | {r.get('feedback_delay_p50_s') or '–'} / {r.get('feedback_delay_p90_s') or '–'} | {r.get('residence_est_end_s') or '–'} |")
elif mode == "variants":
    rows = load(f"v-{tr}-*-replay.csv") + [r for r in load(f"g-{tr}-c3200-replay.csv")]
    print(f"**{tr}, 200 GiB variants** — usable-prefix hit share | TB written | net hits vs LRU | bypassed (reused later) | explored | feedback delay p50\n")
    lru = next(r for r in rows if r["policy"] == "lru" and r["_file"].startswith("g-")); orc = next(r for r in rows if r["policy"] == "oracle" and r["_file"].startswith("g-")); gain = fl(orc, "hits") - fl(lru, "hits")
    print("| variant (file, policy) | hit share | TB written | share of oracle gain | net hits | bypassed (reused later) | explored | feedback delay p50 s |"); print("|---|---|---|---|---|---|---|---|")
    for r in sorted(rows, key=lambda r: (r["_file"], r["policy"])):
        if int(r["cap"]) != 3200: continue
        sh = 100 * (fl(r, "hits") - fl(lru, "hits")) / gain
        print(f"| {r['_file'].replace('-replay.csv', '')}, {r['policy']} (th {r.get('admit_th', '')}, freeze {r.get('freeze_at', '')}, explore {r.get('explore', '')}, bypass-fb {r.get('bypass_feedback', '')}) | {fl(r, 'usable_hit_share'):.3f} | {fl(r, 'written_chunks') * 67.1 / 1e6:.2f} | {sh:.0f}% | {int(fl(r, 'hits') - fl(lru, 'hits')):+d} | {int(fl(r, 'bypass_total'))} ({int(fl(r, 'bypass_reused_later'))}) | {int(fl(r, 'explored'))} | {r.get('feedback_delay_p50_s') or '–'} |")
elif mode == "fifths":
    rows = load(f"g-{tr}-c3200-replay.csv") + load(f"v-{tr}-frozen-replay.csv")
    print(f"**{tr}, 200 GiB — hits per chronological fifth of the scored half (walk-forward)**\n")
    print("| policy | fifth 1 | 2 | 3 | 4 | 5 | accesses per fifth |"); print("|---|---|---|---|---|---|---|")
    for r in rows:
        if int(r["cap"]) != 3200: continue
        print(f"| {r['_file'].replace('-replay.csv', '')} {r['policy']} | " + " | ".join(r["hits_by_fifth"].split("/")) + f" | {r['acc_by_fifth']} |")
elif mode == "mix":
    for mx in ("mix-interleave", "mix-phase"):
        rows = load(f"m-{mx}-replay.csv") + load(f"m-{mx}-frozen-replay.csv") + load(f"s2-m-{mx}-replay.csv")
        lru = next(r for r in rows if r["policy"] == "lru"); orc = next(r for r in rows if r["policy"] == "oracle"); gain = fl(orc, "hits") - fl(lru, "hits")
        print(f"**{mx} (CONSTRUCTED from the two real traces), 200 GiB** — hit share | TB written | share of oracle gain | net hits | hits per fifth\n")
        print("| policy | hit share | TB written | share of oracle gain | net hits | hits per fifth |"); print("|---|---|---|---|---|---|")
        for r in rows: print(f"| {r['_file'].replace('-replay.csv', '')} {r['policy']} | {fl(r, 'usable_hit_share'):.3f} | {fl(r, 'written_chunks') * 67.1 / 1e6:.2f} | {100 * (fl(r, 'hits') - fl(lru, 'hits')) / gain:.0f}% | {int(fl(r, 'hits') - fl(lru, 'hits')):+d} | {r['hits_by_fifth']} |")
        print()
elif mode == "agents":
    for t in ("a-short-k16", "a-lt-k16-bg2"):
        rows = load(f"{t}-replay.csv") + load(f"s2-{t}-replay.csv"); G = {(int(r["cap"]), r["policy"]): r for r in rows}; caps = sorted({int(r["cap"]) for r in rows})
        pols = [p for p in ("lru", "slru", "event_cont", "static_n4", "static_d6", "static_2nd1", "static_2nd4", "lhd", "cond", "oracle") if (caps[0], p) in G]
        print(f"**{t}** — usable-prefix hit share | written chunks | share of oracle gain\n"); print("| capacity | " + " | ".join(LAB.get(p, p) for p in pols) + " |"); print("|---|" + "---|" * len(pols))
        for c in caps:
            lru, orc = G[(c, "lru")], G[(c, "oracle")]; gain = fl(orc, "hits") - fl(lru, "hits")
            print(f"| {c} chunks | " + " | ".join(f"{fl(G[(c, p)], 'usable_hit_share'):.3f} / {int(fl(G[(c, p)], 'written_chunks'))}" + ("" if p in ("lru", "oracle") else f" / {100 * (fl(G[(c, p)], 'hits') - fl(lru, 'hits')) / gain:.0f}%") for p in pols) + " |")
        print()
