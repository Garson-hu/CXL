#!/usr/bin/env python3
"""Tables and the budget selection for the joint benefit analysis (2026-10-21).
usage: kv_joint_tables.py <dir> select|grid|reg|sens|pressure [filters]
select: from sel-*-joint.csv (first half), per trace × model × speed × neighbour choose (B, d) for the budget policies by one rule —
        the pair with the highest usable hit share of `indep` among the pairs whose estimated neighbour p99 is ≤ 6% for indep,
        cost_budget AND joint (a 1-point margin below the 7% SLO); writes chosen.json and prints selection.md.
grid:   the test-half comparison per configuration. reg: the regime runs. sens: thresholds. pressure: write-pressure table."""
import csv, glob, json, os, sys
D, mode = sys.argv[1], sys.argv[2]
def load(pattern):
    rows = []
    for f in sorted(glob.glob(f"{D}/{pattern}")):
        for r in csv.DictReader(open(f)): r["_f"] = os.path.basename(f).replace("-joint.csv", ""); rows.append(r)
    return rows
def fl(r, k, d=0.0):
    try: return float(r.get(k) or d)
    except (ValueError, TypeError): return d
LAB = {"split_lru": "static split + LRU", "split_slru": "static split + SLRU", "value_split": "reuse-aware only (RQ1 admission, static split)", "cost_budget": "cost-aware only (admit all, budget-gated split, drop)", "indep": "independent combination", "indep_nodrop": "independent, no drop", "joint": "joint value × cost", "joint_hash": "joint, hash placement", "joint_nodrop": "joint, no drop", "joint_2nd": "joint with plain second touch", "oracle_cost": "ORACLE value, same costs", "oracle_joint": "ORACLE value + oracle placement, same costs", "oracle_free": "ORACLE, no bandwidth limit"}
def gain(r, lru, orc): g = fl(orc, "usable") - fl(lru, "usable"); return 100 * (fl(r, "usable") - fl(lru, "usable")) / g if g > 0 else float("nan")
if mode == "select":
    rows = load("sel-*-joint.csv"); groups = {}
    for r in rows:
        f = r["_f"]  # sel-<tr>-<m>-<sp>x-<nb>-B<B>-d<d>
        parts = f.split("-"); tr, m, sp, nb = parts[1], parts[2], parts[3][:-1], parts[4]; B = float(parts[5][1:]); d = float(parts[6][1:])
        groups.setdefault((tr, m, sp, nb), {}).setdefault((B, d), {})[r["policy"]] = r
    chosen = {}; lines = ["| trace | model | speed | neighbour | chosen B (GB/s) / depth | indep hit (sel) | indep p99 | cost_budget hit / p99 | joint hit / p99 | feasible pairs |", "|---|---|---|---|---|---|---|---|---|---|"]
    for key in sorted(groups):
        feas = []
        for (B, d), pols in groups[key].items():
            if all(p in pols for p in ("indep", "cost_budget", "joint")) and all(fl(pols[p], "neighbour_p99_pct") <= 6.0 for p in ("indep", "cost_budget", "joint")): feas.append((fl(pols["indep"], "usable_hit_share"), B, d))
        if not feas:   # nothing inside the margin: the smallest budget
            B, d = min(groups[key]); feas = [(fl(groups[key][(B, d)]["indep"], "usable_hit_share"), B, d)]
        hit, B, d = max(feas); pols = groups[key][(B, d)]; chosen["|".join(key)] = [B, d]
        lines.append(f"| {key[0]} | {key[1]} | {key[2]}× | {key[3]} | {B:g} / {d:g} | {hit:.3f} | {fl(pols['indep'], 'neighbour_p99_pct'):.1f}% | {fl(pols['cost_budget'], 'usable_hit_share'):.3f} / {fl(pols['cost_budget'], 'neighbour_p99_pct'):.1f}% | {fl(pols['joint'], 'usable_hit_share'):.3f} / {fl(pols['joint'], 'neighbour_p99_pct'):.1f}% | {len(feas)} of {len(groups[key])} |")
    json.dump(chosen, open(f"{D}/chosen.json", "w"), indent=1)
    print("**Budget selection on the FIRST half (requests 25–50%)** — rule: the (B, depth) pair with the highest usable hit share of the independent combination among the pairs whose estimated neighbour p99 is ≤ 6% for the independent, the cost-only and the joint policy; the same pair is used by all three on the test half.\n")
    print("\n".join(lines))
elif mode == "grid":
    rows = load("test-*-joint.csv"); groups = {}
    for r in rows: groups.setdefault(r["_f"], {})[r["policy"]] = r
    print("**Test half (requests 50–100%)** — usable-prefix hit share / share of the gain of `oracle_free` over `split_lru` / DRAM write rate during neighbour-on phases (GB/s) / estimated neighbour p99 (SLO 7%; * = extrapolated beyond the measured range) / CXL backlog max (GB) / drops / recomputed tokens (M)\n")
    pols = ["split_lru", "split_slru", "value_split", "cost_budget", "indep", "joint", "joint_hash", "joint_2nd", "indep_nodrop", "joint_nodrop", "oracle_cost", "oracle_joint", "oracle_free"]
    for f in sorted(groups):
        G = groups[f]; lru, orc = G.get("split_lru"), G.get("oracle_free")
        if not lru or not orc: continue
        r0 = G["split_lru"]; print(f"**{f.replace('test-', '')}** (block {fl(r0, 'block_mb'):.0f} MB, speed {fl(r0, 'speed'):g}×, budget {fl(r0, 'budget'):g} GB/s depth {fl(r0, 'depth'):g}, neighbour {r0['neighbour']}; wall span {fl(r0, 'wall_span_s'):.0f} s)\n")
        print("| policy | usable | oracle gain | DRAM GB/s | p99 | SLO | backlog GB | drops | recompute Mtok | bypassed (value) |"); print("|---|---|---|---|---|---|---|---|---|---|")
        for p in pols:
            r = G.get(p)
            if not r: continue
            print(f"| {LAB[p]} | {fl(r, 'usable_hit_share'):.3f} | {gain(r, lru, orc):.0f}% | {fl(r, 'dram_rate_on_GBps'):.2f} | {fl(r, 'neighbour_p99_pct'):.1f}%{'*' if r['p99_extrapolated'] == 'True' else ''} | {'ok' if r['slo_ok'] == 'True' else 'FAIL'} | {fl(r, 'cxl_backlog_max_GB'):.0f} | {int(fl(r, 'bypass_drop'))} | {fl(r, 'recomputed_tokens') / 1e6:.1f} | {int(fl(r, 'bypass_value'))} |")
        print()
elif mode == "reg":
    rows = load("reg-*-joint.csv"); groups = {}
    for r in rows: groups.setdefault(r["_f"], {})[r["policy"]] = r
    print("**Regime runs (test half)** — usable share / DRAM GB/s on / p99 / backlog GB / drops / checkpoint completion max s (unfinished)\n")
    for f in sorted(groups):
        G = groups[f]; r0 = next(iter(G.values()))
        print(f"**{f.replace('reg-', '')}** (speed {fl(r0, 'speed'):g}×, block {fl(r0, 'block_mb'):.0f} MB, DRAM {r0['dram_blocks']} + CXL {r0['cxl_blocks']} blocks, budget {fl(r0, 'budget'):g}/{fl(r0, 'depth'):g}, ckpt '{r0['ckpt']}', phases '{r0['phases']}')\n")
        print("| policy | usable | DRAM GB/s | p99 | backlog GB | drops | bypassed | ckpt max s (unfinished) |"); print("|---|---|---|---|---|---|---|---|")
        for p in ("split_slru", "value_split", "cost_budget", "indep", "joint", "oracle_cost"):
            r = G.get(p)
            if not r: continue
            print(f"| {LAB[p]} | {fl(r, 'usable_hit_share'):.3f} | {fl(r, 'dram_rate_on_GBps'):.2f} | {fl(r, 'neighbour_p99_pct'):.1f}%{'*' if r['p99_extrapolated'] == 'True' else ''} | {fl(r, 'cxl_backlog_max_GB'):.0f} | {int(fl(r, 'bypass_drop'))} | {int(fl(r, 'bypass_value'))} | {r['ckpt_completion_max_s'] or '–'} ({r['ckpt_unfinished']}) |")
        print()
elif mode == "stress":
    rows = load("stress-*-joint.csv"); groups = {}
    for r in rows: groups.setdefault(r["_f"], {})[r["policy"]] = r
    print("**CONSTRUCTED stress (70B 8×, Adam, test half): where would value × cost couple?** — usable share / DRAM GB/s on / p99 / CXL backlog max GB / drops / bypassed (value) / pending misses / checkpoint completion max s\n")
    for f in sorted(groups):
        G = groups[f]; r0 = next(iter(G.values()))
        print(f"**{f.replace('stress-', '')}** (CXL {fl(r0, 'cxl_gbps'):g} GB/s, budget {fl(r0, 'budget'):g}/{fl(r0, 'depth'):g}, ckpt '{r0['ckpt']}')\n")
        print("| policy | usable | DRAM GB/s | p99 | backlog GB | drops | bypassed | pending misses | ckpt max s |"); print("|---|---|---|---|---|---|---|---|---|")
        for p in ("split_slru", "value_split", "cost_budget", "indep", "indep_nodrop", "joint", "joint_hash", "joint_nodrop", "oracle_cost", "oracle_joint"):
            r = G.get(p)
            if not r: continue
            print(f"| {LAB[p]} | {fl(r, 'usable_hit_share'):.3f} | {fl(r, 'dram_rate_on_GBps'):.2f} | {fl(r, 'neighbour_p99_pct'):.1f}%{'*' if r['p99_extrapolated'] == 'True' else ''} | {fl(r, 'cxl_backlog_max_GB'):.0f} | {int(fl(r, 'bypass_drop'))} | {int(fl(r, 'bypass_value'))} | {int(fl(r, 'miss_pending'))} | {r['ckpt_completion_max_s'] or '–'} |")
        print()
elif mode == "sens":
    rows = load("sens-*-joint.csv"); print("**Sensitivity (conversation, Adam, test half)** — usable share / p99 / backlog / drops\n"); print("| run | policy | usable | p99 | backlog GB | drops |"); print("|---|---|---|---|---|---|")
    for r in rows: print(f"| {r['_f'].replace('sens-', '')} | {LAB[r['policy']]} | {fl(r, 'usable_hit_share'):.3f} | {fl(r, 'neighbour_p99_pct'):.1f}% | {fl(r, 'cxl_backlog_max_GB'):.0f} | {int(fl(r, 'bypass_drop'))} |")
elif mode == "pressure":
    rows = load("test-*-none-joint.csv") + load("test-*-adam-joint.csv"); groups = {}
    for r in rows: groups.setdefault(r["_f"], {})[r["policy"]] = r
    print("**Write pressure after RQ1 filtering (test half; no neighbour runs where present, else Adam)** — offered stream = split_lru's writes; GB/s mean over the scored wall span; worst minute (DRAM, on phases); CXL backlog max\n")
    print("| config | policy | DRAM GB/s | CXL GB/s | total GB/s | DRAM worst minute | backlog GB | written blocks (DRAM + CXL) |"); print("|---|---|---|---|---|---|---|---|")
    for f in sorted(groups):
        G = groups[f]
        for p in ("split_lru", "value_split", "indep", "joint"):
            r = G.get(p)
            if r: print(f"| {f.replace('test-', '')} | {LAB[p]} | {fl(r, 'dram_rate_GBps'):.2f} | {fl(r, 'cxl_rate_GBps'):.2f} | {fl(r, 'dram_rate_GBps') + fl(r, 'cxl_rate_GBps'):.2f} | {fl(r, 'dram_worst_minute_GBps'):.2f} | {fl(r, 'cxl_backlog_max_GB'):.0f} | {int(fl(r, 'written_dram_blocks'))} + {int(fl(r, 'written_cxl_blocks'))} |")
