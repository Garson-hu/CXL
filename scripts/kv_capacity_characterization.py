#!/usr/bin/env python3
"""KV-cache capacity characterization from the Mooncake traces (2026-10-09).

Question: how much host memory does a KV cache need, and how much does extra capacity (DRAM added to CXL as a
second region holding different blocks, instead of holding copies of CXL blocks) raise the share of reuses that
find their block in host memory?

Three kinds of numbers, kept apart in the output:
  [TRACE]      exact counts from the traces; no hardware or model assumption (blocks = 512-token hash blocks).
  [MODEL]      the same counts converted to bytes with the KV size of a model (bytes per token from the model's
               published configuration: layers x KV heads x head size x 2 (K and V) x 2 bytes for fp16/bf16).
  [LRU-SIM]    an exact LRU stack-distance simulation over the block accesses: the share of reuses that hit an
               LRU cache of a given capacity. It assumes every block is stored in host memory when it is first
               computed, every later request that contains the block reads it from host memory (no GPU-side
               prefix cache in front), uniform block size, and request order = trace order (within a request,
               blocks in prefix order, each once).
No hardware performance is estimated here; the experiment file states the external and measured speeds separately.

usage: kv_capacity_characterization.py [out_dir]   (traces from <repo>/workloads)
"""
import collections, json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACES = ["conversation", "toolagent", "synthetic"]
TOKENS_PER_BLOCK = 512
# bytes of K+V per token: layers x kv_heads x head_dim x 2 (K,V) x 2 bytes (bf16); from the models' config.json
MODELS = {"Llama-3.1-8B": 32 * 8 * 128 * 2 * 2,      # 131072 B = 128 KiB per token -> 64 MiB per block
          "Llama-3.1-70B": 80 * 8 * 128 * 2 * 2}     # 327680 B = 320 KiB per token -> 160 MiB per block
CAPS_GIB = [16, 40, 80, 128, 242.5, 256, 512, 592, 768, 1024, 1536, 2048, 4096]
# host-memory configurations on c28 (CXL pair c1+e1 = dax0.0 242.5 GiB + dax1.0 269.5 GiB) with a DRAM region D:
#   copies   = DRAM holds copies of CXL blocks -> distinct capacity = CXL only
#   distinct = DRAM holds blocks that are not in CXL -> distinct capacity = CXL + D
CONFIGS = [(512, 0), (512, 80), (512, 256), (242.5, 80), (242.5, 256)]


def load(name):
    reqs = []
    for line in open(os.path.join(REPO, "workloads", f"mooncake_{name}_trace.jsonl")):
        r = json.loads(line)
        reqs.append((r["timestamp"] / 1000.0, list(dict.fromkeys(r["hash_ids"]))))
    return reqs


def stack_distances(accesses):
    """LRU stack distance (distinct blocks touched since the previous access to the same block) for every reuse."""
    n = len(accesses); tree = [0] * (n + 1); last = {}; out = []
    def add(i, v):
        i += 1
        while i <= n: tree[i] += v; i += i & -i
    def prefix(i):
        s = 0
        while i > 0: s += tree[i]; i -= i & -i
        return s
    for i, b in enumerate(accesses):
        j = last.get(b)
        if j is not None:
            out.append(prefix(i) - prefix(j + 1)); add(j, -1)
        add(i, 1); last[b] = i
    return out


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out_dir, exist_ok=True)
    txt = open(os.path.join(out_dir, "kv-capacity.txt"), "w")
    csvf = open(os.path.join(out_dir, "kv-capacity.csv"), "w")
    csvf.write("trace,model,capacity_gib,capacity_blocks,lru_hit_share\n")
    def say(s=""): print(s); txt.write(s + "\n")
    say("# KV-cache capacity characterization, Mooncake traces; see the docstring of scripts/kv_capacity_characterization.py")
    say(f"# tokens per block {TOKENS_PER_BLOCK}; models: " + ", ".join(f"{m} {b // 1024} KiB/token = {b * TOKENS_PER_BLOCK / 2**20:.0f} MiB/block" for m, b in MODELS.items()))
    for name in TRACES:
        reqs = load(name)
        span = max(t for t, _ in reqs) - min(t for t, _ in reqs)
        first, count = {}, collections.Counter()
        accesses = []
        for t, hs in reqs:
            for h in hs:
                count[h] += 1; first.setdefault(h, t); accesses.append(h)
        distinct = len(count); reuses = sum(c - 1 for c in count.values())
        never = sum(1 for c in count.values() if c == 1) / distinct
        early = [h for h, t in first.items() if t < span / 2]
        never_early = sum(1 for h in early if count[h] == 1) / len(early)
        buckets = collections.Counter(min(c - 1, 10) for c in count.values())
        def share_blocks(lo, hi): return sum(v for k, v in buckets.items() if lo <= k <= hi) / distinct
        def share_reuses(lo, hi): return sum((c - 1) for c in count.values() if lo <= c - 1 <= hi) / reuses
        say(f"\n## {name}")
        say(f"[TRACE] requests {len(reqs)}, span {span:.0f} s, block accesses {len(accesses)}, distinct blocks {distinct} "
            f"({distinct / span:.1f} new blocks/s), reuses {reuses} ({reuses / span:.1f}/s)")
        say(f"[TRACE] blocks never reused: {never:.1%} of all; {never_early:.1%} of the {len(early)} blocks first seen in the first half of the span (end-of-trace effect)")
        say(f"[TRACE] blocks by later reuses: 0 -> {share_blocks(0, 0):.1%}, 1 -> {share_blocks(1, 1):.1%}, 2 -> {share_blocks(2, 2):.1%}, "
            f"3-9 -> {share_blocks(3, 9):.1%}, >=10 -> {share_blocks(10, 10):.2%}; share of all reuses that go to blocks reused >=10 times: {share_reuses(10, 10**9):.1%}")
        d = stack_distances(accesses)
        for model, bpt in MODELS.items():
            bb = bpt * TOKENS_PER_BLOCK; gib = bb / 2**30
            say(f"[MODEL {model}] distinct KV {distinct * gib:.0f} GiB; new KV {distinct * gib / span:.2f} GiB/s; reuse reads {reuses * gib / span:.2f} GiB/s (averages over the span)")
            hits = []
            for c in CAPS_GIB:
                blocks = int(c * 2**30 // bb); h = sum(1 for x in d if x < blocks) / len(d); hits.append((c, h))
                csvf.write(f"{name},{model},{c},{blocks},{h:.4f}\n")
            say(f"[LRU-SIM {model}] reuse hit share by host capacity: " + " ".join(f"{c:g}GiB:{h:.2f}" for c, h in hits))
            def hit(cap):
                blocks = int(cap * 2**30 // bb); return sum(1 for x in d if x < blocks) / len(d)
            for cxl, dram in CONFIGS:
                if dram == 0: say(f"[LRU-SIM {model}] CXL {cxl:g} GiB alone: {hit(cxl):.2f}"); continue
                say(f"[LRU-SIM {model}] CXL {cxl:g} GiB + DRAM {dram} GiB: DRAM holds copies -> {hit(cxl):.2f}; DRAM holds other blocks -> {hit(cxl + dram):.2f} (+{hit(cxl + dram) - hit(cxl):.2f})")
    txt.close(); csvf.close()


if __name__ == "__main__":
    main()
