import csv, itertools, os, glob

d = sorted(glob.glob("/home/ghu4/CXL/benchmarks/results/*-phase21"))[-1]
print("dir:", d, "\n")

# ---- saturation sweep ----
print("===== SATURATION SWEEP (slowdown vs idle, disjoint cores) =====")
sweep = list(csv.DictReader(open(f"{d}/sweep.csv")))
for node in ("0", "1"):
    lbl = "DRAM" if node == "0" else "CXL"
    print(f"\n-- node {node} ({lbl}) --")
    print(f"{'victim':<12}{'agg_t=1':>9}{'agg_t=2':>9}{'agg_t=4':>9}{'agg_t=8':>9}   (agg_bw@8)")
    victims = []
    for r in sweep:
        if r["node"]==node and r["victim"] not in victims:
            victims.append(r["victim"])
    for v in victims:
        rows = {r["agg_threads"]: r for r in sweep if r["node"]==node and r["victim"]==v}
        line = f"{v:<12}"
        for t in ("1","2","4","8"):
            line += f"{float(rows[t]['slowdown']):>9.2f}"
        line += f"     {float(rows['8']['aggressor_bw_gib_s']):.1f}"
        print(line)

# ---- asymmetry matrix ----
print("\n\n===== ASYMMETRY MATRIX (8-thread aggressor) =====")
asym = list(csv.DictReader(open(f"{d}/asym.csv")))
def sd(node, v, a):
    for r in asym:
        if r["node"]==node and r["victim"]==v and r["aggressor"]==a:
            return float(r["slowdown"])
    return None
modes = ["latency","random-read","stream-read"]
for node in ("0","1"):
    lbl = "DRAM" if node=="0" else "CXL"
    print(f"\n-- node {node} ({lbl}) slowdown[victim][aggressor] --")
    print(f"victim\\agg     " + "".join(f"{a:>14}" for a in modes))
    for v in modes:
        print(f"{v:<14}" + "".join(f"{sd(node,v,a):>14.2f}" for a in modes))

print("\n-- pairwise asymmetry = max(sd(X|Y)/sd(Y|X), inv) --")
print(f"{'pair':<28}{'node':>6}{'sd(X|Y)':>9}{'sd(Y|X)':>9}{'asym':>8}")
maxasym = {"0":0,"1":0}
maxpair = {"0":None,"1":None}
for node in ("0","1"):
    lbl = "DRAM" if node=="0" else "CXL"
    for x,y in itertools.combinations(modes,2):
        sxy, syx = sd(node,x,y), sd(node,y,x)
        a = max(sxy/syx, syx/sxy)
        print(f"{x+' vs '+y:<28}{lbl:>6}{sxy:>9.2f}{syx:>9.2f}{a:>8.2f}")
        if a > maxasym[node]:
            maxasym[node]=a; maxpair[node]=(x,y)
print()
for node in ("0","1"):
    lbl="DRAM" if node=="0" else "CXL"
    print(f"{lbl}: max pairwise asym = {maxasym[node]:.2f} ({maxpair[node]})")
print(f"\nAny CXL pair > 1.5x asymmetry? {'YES' if maxasym['1']>1.5 else 'NO'}")

# aggressor-type asymmetry: stream aggressor vs latency aggressor on same victim
print("\n-- aggressor-type effect on CXL (stream agg vs latency agg) --")
for v in modes:
    s_stream = sd("1", v, "stream-read")
    s_lat = sd("1", v, "latency")
    print(f"  victim={v:<12} stream-agg={s_stream:.2f}x  latency-agg={s_lat:.2f}x  ratio={s_stream/s_lat:.2f}x")
