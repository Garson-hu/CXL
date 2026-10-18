#!/usr/bin/env python3
"""Markdown tables for the miss-cost feasibility round (2026-10-18) from kv_agent_replay.py CSVs that carry the
prefix-aware and TTFT-model columns. One table per CSV: rows = capacities, columns = policies with
usable-prefix hit share (chunk hit share), usable prompt-token share, modelled mean TTFT, bytes written and the
share of the oracle's TTFT benefit recovered over global LRU.
usage: kv_misscost_tables.py <label=replay.csv> [...] [--pols lru,slru,ttl30,event_cont,cost,event_cont+cost,oracle]"""
import argparse, csv
ap = argparse.ArgumentParser(); ap.add_argument("items", nargs="+"); ap.add_argument("--pols", default="lru,slru,ttl30,event_cont,cost,event_cont+cost,oracle")
A = ap.parse_args(); pols = A.pols.split(",")
for item in A.items:
    label, path = item.split("=", 1); R = list(csv.DictReader(open(path))); G = {(int(r["cap"]), r["policy"]): r for r in R}; caps = sorted({int(r["cap"]) for r in R})
    r0 = R[0]; print(f"**{label}** — order {r0.get('order', 'head')}; TTFT model r0 {1000 * float(r0.get('r0', 0) or 0):.3f} ms/tok (see file), scored requests {r0['requests']}, prompt tokens {float(r0['prompt_tokens']) / 1e6:.2f} M\n")
    print("| capacity | " + " | ".join(pols) + " |"); print("|---|" + "---|" * len(pols))
    for c in caps:
        if (c, "lru") not in G or (c, "oracle") not in G: continue
        lru, orc = G[(c, "lru")], G[(c, "oracle")]; gain = float(orc["ttft_saved_s"]) - float(lru["ttft_saved_s"]); cells = []
        for p in pols:
            r = G.get((c, p))
            if r is None: cells.append("–"); continue
            sh = 100 * (float(r["ttft_saved_s"]) - float(lru["ttft_saved_s"])) / gain if gain > 0 else float("nan")
            cells.append(f"{float(r['usable_hit_share']):.3f} ({float(r['reuse_hit_share']):.3f}), tok {100 * float(r['usable_token_share']):.1f}%, TTFT {float(r['ttft_mean_ms']):.0f} ms, w {float(r['written_chunks']) * float(r['cap_GB']) / c:.1f} GB" + ("" if p in ("lru", "oracle") else f", {sh:.0f}% of oracle TTFT gain"))
        print(f"| {c} chunks = {float(lru['cap_GB']):.1f} GB | " + " | ".join(cells) + " |")
    print()
