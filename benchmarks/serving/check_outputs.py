#!/usr/bin/env python3
"""CXL-vs-NVMe study (2026-11-12): do the tiers change what the model generates? For runs that send the same requests (same driver,
same seeds; temperature 0), compare the SHA-1 of the generated text of every request with the reference run's (client.jsonl `out_sha`;
the request id without its run tag is the key). Differences are expected only from vLLM's batching (requests that run in different
batches can differ in the last bits), not from the medium the KV came from: a loaded chunk is the stored chunk, byte for byte.
usage: check_outputs.py <dir> <reference tag> <tag> [<tag> ...] [case=<case>[,<case>...]]"""
import json, sys
args = [a for a in sys.argv[1:] if not a.startswith("case=")]; cases = next((a[5:].split(",") for a in sys.argv[1:] if a.startswith("case=")), None)
d, ref, tags = args[0], args[1], args[2:]
def load(tag):
    out = {}
    for l in open(f"{d}/{tag}-client.jsonl"):
        c = json.loads(l)
        if c["status"] != 200 or (cases and c["case"] not in cases): continue
        out[c["rid"][len(tag) + 1:]] = (c.get("out_sha"), c.get("out_tokens"), c["case"])
    return out
R = load(ref)
for t in tags:
    T = load(t); common = [k for k in R if k in T]; same = sum(1 for k in common if R[k][0] == T[k][0]); ntok = sum(1 for k in common if R[k][1] == T[k][1])
    print(f"{t} vs {ref}: {len(common)} common requests, identical output text {same} ({100.0 * same / max(1, len(common)):.1f} %), same output length {ntok}")
