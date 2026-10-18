#!/usr/bin/env python3
"""Markdown tables for the RQ1-B reuse-horizon validation (2026-10-17) from kv_agent_replay.py CSVs (with the pressure
metrics). One table per CSV: capacity rows (chunks, GB, C / W_live), columns = policies with reuse-hit share, Δhits vs
global LRU (absolute), and the LRU regime numbers (residence, evictions before reuse, dead occupancy).
usage: kv_horizon_tables.py <label=replay.csv> [...] [--caps 24,32,48,64,96,128,192,384] [--pols lru,slru,ttl30,event_cont,event_end,event_both,oracle]"""
import argparse, csv
ap = argparse.ArgumentParser(); ap.add_argument("items", nargs="+"); ap.add_argument("--caps", default="24,32,48,64,96,128,192,384"); ap.add_argument("--pols", default="lru,slru,ttl30,event_cont,event_end,event_both,oracle"); ap.add_argument("--coverage", action="store_true")
A = ap.parse_args(); caps = [int(c) for c in A.caps.split(",")]; pols = A.pols.split(",")
for item in A.items:
    label, path = item.split("=", 1); R = list(csv.DictReader(open(path))); G = {(int(r["cap"]), r["policy"]): r for r in R}
    r0 = R[0]; W = float(r0["W_live_mean"]); print(f"**{label}** — W_live {W:.0f} chunks (p90 {float(r0['W_live_p90']):.0f}), production {float(r0['P_agent_chunks_s']):.1f} agent + {float(r0.get('P_bg_chunks_s', 0) or 0):.1f} real background + {float(r0['churn']):.1f} synthetic churn chunks/s, reuse horizon of own chunks p50 {float(r0['H_p50_s']):.1f} s / p90 {float(r0['H_p90_s']):.1f} s\n")
    print("| capacity (C / W_live) | LRU residence | LRU evictions before reuse | LRU dead occupancy | " + " | ".join(pols) + " |"); print("|---|---|---|---|" + "---|" * len(pols))
    for c in caps:
        if (c, "lru") not in G: continue
        lru = G[(c, "lru")]; cells = []
        for p in pols:
            r = G.get((c, p))
            if r is None: cells.append("–"); continue
            v = float(r["reuse_hit_share"]); d = int(float(r.get("hits_vs_lru", 0) or 0)) if p != "lru" else 0
            cov = f", {100 * float(r['hits_under_protection']) / max(1, float(r['reuse'])):.0f}% of reuses under protection" if p == "event_cont" and A.coverage else ""
            cells.append(f"{v:.3f}" + ("" if p == "lru" else f" ({d:+d}{cov})"))
        print(f"| {c} = {float(lru['cap_GB']):.2f} GB ({c / W:.1f}) | {float(lru['residence_p50_s']):.1f} s | {100 * float(lru['evict_before_reuse_share']):.0f}% | {100 * float(lru['dead_occupancy_share']):.0f}% | " + " | ".join(cells) + " |")
    print()
