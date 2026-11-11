#!/usr/bin/env python3
"""KV that should have been stored in the host tier and was not (2026-11-10 admission study, §A5). A request stores its new 256-token
chunks (tokens beyond what was served from a cache) when it runs; LMCache 0.5.5's connector adds the LMCache hit length to the request's
stored-token counter at EVERY poll that returns a result (lmcache_mp_connector.py:1065), and the store path starts at that counter
(lmcache_mp_metadata.py:252), so a request that the scheduler polls again after a refused admission skips its new chunks.
Per run: requests with at least one new chunk, split by the number of polls with a result (admission stream; '-' for runs without it),
how many stored nothing, bytes stored against bytes expected (new full chunks x chunk tokens x KV bytes per token).
Reads <dir>/<tag>-requests.csv (analyze_b.py) and, if present, <dir>/<tag>-adm-requests.csv (analyze_adm.py).
usage: store_loss.py [bpt=36864] [chunk=256] <dir>:<tag> [<dir>:<tag> ...]"""
import csv, os, sys
kv = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a and ":" not in a); specs = [a for a in sys.argv[1:] if ":" in a]
BPT = int(kv.get("bpt", 36 * 1024)); CH = int(kv.get("chunk", 256))
def fl(x):
    try: return float(x)
    except (TypeError, ValueError): return 0.0
print("| run | requests | with ≥ 1 new chunk | stored nothing | GB stored | GB expected | missing | polled once: n / stored nothing | polled ≥ 2 times: n / stored nothing / GB stored of expected |"); print("|---|---|---|---|---|---|---|---|---|")
for spec in specs:
    d, tag = spec.split(":")
    R = [r for r in csv.DictReader(open(f"{d}/{tag}-requests.csv")) if r["case"] == "trace" and r["status"] == "200"]
    newc = lambda r: int(fl(r["prompt_tokens"])) // CH - int(max(0, fl(r["cached_tokens"]))) // CH
    w = [r for r in R if newc(r) >= 1]; exp = sum(newc(r) * CH * BPT for r in w); got = sum(fl(r["store_bytes"]) for r in R)
    none = [r for r in w if fl(r["store_bytes"]) == 0]; once = twice = "–"
    ap = f"{d}/{tag}-adm-requests.csv"
    if os.path.exists(ap):
        npoll = {r["rid"]: fl(r["n_polls_result"]) for r in csv.DictReader(open(ap))}
        a = [r for r in w if npoll.get(r["rid"], 0) <= 1]; b = [r for r in w if npoll.get(r["rid"], 0) >= 2]
        once = f"{len(a)} / {sum(1 for r in a if fl(r['store_bytes']) == 0)}"
        twice = f"{len(b)} / {sum(1 for r in b if fl(r['store_bytes']) == 0)} / {sum(fl(r['store_bytes']) for r in b) / 1e9:.1f} of {sum(newc(r) * CH * BPT for r in b) / 1e9:.1f}"
    print(f"| `{tag}` | {len(R)} | {len(w)} | {len(none)} | {got / 1e9:.1f} | {exp / 1e9:.1f} | {100 * max(0, exp - got) / exp:.0f} % | {once} | {twice} |")
