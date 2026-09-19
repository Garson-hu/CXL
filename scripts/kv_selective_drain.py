#!/usr/bin/env python3
"""Trace analysis: what does a selective KV drain cost in hit rate, and save in NVMe writes?

Two-tier simulation over a Mooncake trace (512-token blocks, hash_ids = prefix chain).
Memory tier (the CXL/DRAM pool) and SSD tier are both LRU with a capacity in blocks.
On each request, blocks are matched as a PREFIX: the first block found in neither tier
ends the match; the remaining blocks are recomputed and written into the memory tier.
A block evicted from the memory tier is handled by the policy:
  all       - always written to the SSD tier (today's layered KV stores)
  none      - always dropped
  read>=N   - written to SSD only if it was read at least N times while resident
  ctx>=N    - read>=1, OR the request that wrote the block matched >= N prefix blocks
              (the writer was continuing an existing conversation / shared context)
  ctxfrac   - read>=1, OR the writer request matched >= half of its blocks
  oracle    - written to SSD only if it will be needed again (upper bound, uses the future)
"""
import json, sys
from collections import OrderedDict

def load(path):
    reqs = []
    for line in open(path):
        r = json.loads(line)
        reqs.append((r["timestamp"], r["hash_ids"]))
    return reqs

def simulate(reqs, mem_cap, ssd_cap, policy):
    mem, ssd = OrderedDict(), OrderedDict()   # block -> reads while resident (mem) / True (ssd)
    ctx = {}                                   # block -> writer request looked like a continuing context
    future = None
    if policy == "oracle":
        future = {}
        for i, (_, hs) in enumerate(reqs):
            for h in hs:
                future.setdefault(h, []).append(i)
    thr = int(policy.split(">=")[1]) if policy.startswith("read>=") else None
    st = dict(blocks=0, hit_mem=0, hit_ssd=0, miss=0, ssd_writes=0, mem_writes=0)

    def evict_mem(now):
        h, reads = mem.popitem(last=False)
        if policy == "all": keep = True
        elif policy == "none": keep = False
        elif thr is not None: keep = reads >= thr
        elif policy.startswith('ctx'): keep = reads >= 1 or ctx.get(h, False)
        else:
            f = future[h]
            keep = any(i > now for i in f)
        if keep and ssd_cap > 0:
            if h in ssd: ssd.move_to_end(h)
            else:
                ssd[h] = True; st["ssd_writes"] += 1
                if len(ssd) > ssd_cap: ssd.popitem(last=False)

    def put_mem(h, reads, now):
        mem[h] = reads
        while len(mem) > mem_cap: evict_mem(now)

    cthr = int(policy.split('>=')[1]) if policy.startswith('ctx>=') else None
    for i, (_, hs) in enumerate(reqs):
        matching = True
        nhit = 0
        for h in hs:
            if h in mem or h in ssd: nhit += 1
            else: break
        cont = (nhit >= cthr) if cthr is not None else (nhit * 2 >= len(hs))
        for h in hs:
            st["blocks"] += 1
            if matching and h in mem:
                st["hit_mem"] += 1; mem[h] += 1; mem.move_to_end(h)
            elif matching and h in ssd:
                st["hit_ssd"] += 1; ssd.move_to_end(h)
                put_mem(h, 1, i); st["mem_writes"] += 1      # loaded back into the memory tier
            else:
                matching = False
                st["miss"] += 1
                if h in mem: mem.move_to_end(h)               # present but unusable: prefix broken
                else:
                    ctx[h] = cont
                    put_mem(h, 0, i); st["mem_writes"] += 1
    return st

if __name__ == "__main__":
    GiB = 1 << 30
    models = {"8B": 512 * 128 * 1024, "70B": 512 * 320 * 1024}      # bytes per 512-token block
    mems = {"DRAM-pool 64GiB": 64 * GiB, "CXL 512GiB": 512 * GiB}
    ssd_bytes = 3200 * GiB                                          # c28 NVMe, 3.3 TB free
    policies = ["all", "none", "read>=1", "ctx>=2", "ctx>=8", "ctxfrac", "oracle"]
    for path in sys.argv[1:]:
        reqs = load(path)
        dur = reqs[-1][0] / 1000.0
        print(f"\n=== {path.split('/')[-1]}  requests={len(reqs)}  duration={dur:.0f}s")
        for mname, bpb in models.items():
            for memname, mb in mems.items():
                mem_cap, ssd_cap = mb // bpb, ssd_bytes // bpb
                print(f"-- model {mname} ({bpb>>20} MiB/block)  memory tier {memname} = {mem_cap} blocks  SSD 3200GiB = {ssd_cap} blocks")
                print(f"   {'policy':8s} {'hit%':>6s} {'mem%':>6s} {'ssd%':>6s} {'SSD writes':>11s} {'SSD GiB':>9s} {'vs all':>7s}")
                base = None
                for pol in policies:
                    s = simulate(reqs, mem_cap, ssd_cap, pol)
                    hit = 100.0 * (s["hit_mem"] + s["hit_ssd"]) / s["blocks"]
                    if pol == "all": base = s["ssd_writes"]
                    rel = f"{100.0*s['ssd_writes']/base:5.1f}%" if base else "   -  "
                    print(f"   {pol:8s} {hit:6.2f} {100.0*s['hit_mem']/s['blocks']:6.2f} {100.0*s['hit_ssd']/s['blocks']:6.2f} {s['ssd_writes']:11d} {s['ssd_writes']*bpb/GiB:9.0f} {rel:>7s}")
