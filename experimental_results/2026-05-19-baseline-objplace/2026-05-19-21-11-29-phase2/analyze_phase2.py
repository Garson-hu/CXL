import csv, sys, itertools

PHASE2 = "/home/ghu4/CXL/benchmarks/results/2026-05-19-21-11-29-phase2"

def load(node):
    rows = {}
    path = f"{PHASE2}/matrix-node{node}.csv"
    with open(path) as f:
        for line in f:
            parts = line.strip().split(",")
            if parts[0].startswith("tag") or parts[0].startswith("header:tag"):
                continue
            tag = parts[0].replace("header:", "")
            # tag form: v<victim>-a<agg>-node<N>
            # victim/agg modes contain hyphens (stream-read) so parse carefully.
            assert tag.startswith("v")
            body = tag[1:]
            # split on "-a" that precedes the aggressor; aggressor ends at -node
            idx = body.rfind("-node")
            body = body[:idx]
            # now body = <victim>-a<agg>
            ai = body.find("-a")
            victim = body[:ai]
            agg = body[ai+2:]
            mode = parts[2]
            lat = float(parts[10])      # victim_latency_ns
            bw = float(parts[12])       # total_bandwidth_gib_s
            rows[(victim, agg)] = {"mode": mode, "lat": lat, "bw": bw}
    return rows

def slowdown(rows, victim, agg):
    """Return slowdown factor (>1 = worse) of victim under aggressor vs NONE."""
    base = rows[(victim, "NONE")]
    cur = rows[(victim, agg)]
    if victim == "latency":
        return cur["lat"] / base["lat"]   # higher latency = worse
    else:
        return base["bw"] / cur["bw"]     # lower bw = worse

for node, label in [(0, "DRAM"), (1, "CXL")]:
    rows = load(node)
    print(f"\n===== node {node} ({label}) — victim slowdown vs idle =====")
    victims = ["latency", "random-read", "stream-read", "mixed"]
    aggs = ["stream-read", "stream-write", "random-read", "mixed"]
    hdr = f"{'victim':<14}" + "".join(f"{a:>14}" for a in aggs)
    print(hdr)
    for v in victims:
        line = f"{v:<14}"
        for a in aggs:
            try:
                s = slowdown(rows, v, a)
                line += f"{s:>14.2f}"
            except KeyError:
                line += f"{'-':>14}"
        print(line)

# Asymmetry among modes that appear as BOTH victim and aggressor.
both = ["stream-read", "random-read", "mixed"]
print("\n===== asymmetry (modes that are both victim & aggressor) =====")
print(f"{'pair':<28}{'node':>6}{'sd(X|Y)':>10}{'sd(Y|X)':>10}{'asymmetry':>12}")
results = {}
for node, label in [(0, "DRAM"), (1, "CXL")]:
    rows = load(node)
    for x, y in itertools.combinations(both, 2):
        sxy = slowdown(rows, x, y)   # x victim, y aggressor
        syx = slowdown(rows, y, x)   # y victim, x aggressor
        asym = max(sxy/syx, syx/sxy)
        results[(label, x, y)] = (sxy, syx, asym)
        print(f"{x+' vs '+y:<28}{label:>6}{sxy:>10.2f}{syx:>10.2f}{asym:>12.2f}")

# Max asymmetry pair on CXL
cxl_pairs = {k: v for k, v in results.items() if k[0] == "CXL"}
maxp = max(cxl_pairs.items(), key=lambda kv: kv[1][2])
print(f"\nMax-asymmetry CXL pair: {maxp[0][1]} vs {maxp[0][2]}  asymmetry={maxp[1][2]:.2f}")
print(f"  any CXL pair > 1.5x asymmetry? {'YES' if any(v[2] > 1.5 for v in cxl_pairs.values()) else 'no'}")
# Compare to same pair on DRAM
for (lbl, x, y), v in results.items():
    if lbl == "CXL" and (x, y) == (maxp[0][1], maxp[0][2]):
        dram = results[("DRAM", x, y)]
        print(f"  same pair on DRAM asymmetry={dram[2]:.2f} "
              f"({'weaker on DRAM' if dram[2] < v[2] else 'not weaker on DRAM'})")

# Also report the single worst victim/aggressor slowdown per node
print("\n===== worst single slowdown per node =====")
for node, label in [(0, "DRAM"), (1, "CXL")]:
    rows = load(node)
    worst = None
    for v in ["latency", "random-read", "stream-read", "mixed"]:
        for a in ["stream-read", "stream-write", "random-read", "mixed"]:
            if (v, a) in rows:
                s = slowdown(rows, v, a)
                if worst is None or s > worst[2]:
                    worst = (v, a, s)
    print(f"{label}: victim={worst[0]} aggressor={worst[1]} slowdown={worst[2]:.2f}x")
