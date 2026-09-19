#!/usr/bin/env python3
"""Live gates of Component B on the real machine (dax0.0 + dax1.0 + a DRAM pool):
  B2  probe: overhead <= 2% of one core while active; idle value and saturated value as in check V5
  B3  "CXL write direction full": not with 1 writer, yes with 4
  B4  controller: spill rises only when CXL is full and DRAM calm; halves after an injected DRAM
      aggressor; rises again after it leaves
CPU placement: probe cpu 16 (CCD1), cxlpath writers cpus 112.. (CCD7), aggressor cpus 32.. (CCD2-5).
usage: b_live.py <outdir> [b2] [b3] [b4]"""
import os, subprocess, sys, time, signal
B = "build/"; out = sys.argv[1]; which = [a for a in sys.argv[2:]] or ["b2", "b3", "b4"]
os.makedirs(out, exist_ok=True); STORE = "live"; fails = []

def sh(*a, **k): return subprocess.run(a, capture_output=True, text=True, **k)
def check(ok, msg): print(("  ok   " if ok else "  FAIL ") + msg); (None if ok else fails.append(msg))
def start_daemon(log, *extra):
    p = subprocess.Popen([B + "cxlpathd", STORE, "--cpu", "16", "--log", log, *extra])
    for _ in range(200):
        time.sleep(0.05)
        if "alive=1" in sh(B + "cxlp_admin", STORE, "view").stdout: return p
    raise SystemExit("daemon did not come up")
def stop(p): p.send_signal(signal.SIGTERM); p.wait()
def cpu_ticks(pid): f = open(f"/proc/{pid}/stat").read().split(); return int(f[13]) + int(f[14])
def rows(log):
    hdr, r, ev = {}, [], []
    for line in open(log):
        if line.startswith("# cxlpathd"): hdr = dict(kv.split("=") for kv in line[2:].split()[1:])
        elif line.startswith("#HALVE"): ev.append([float(x) for x in line.strip().split(",")[1:]])
        elif line[0].isdigit():
            v = line.strip().split(","); r.append(dict(t=float(v[0]), probe=float(v[1]), mean=float(v[2]), base=float(v[3]), ref_idle=float(v[14]), ref_act=float(v[15]), spill=int(v[4]), staged=int(v[5]), full=int(v[6]), active=int(v[8]), cxl=float(v[9]), dram=float(v[10]), pw=float(v[11]), conc=float(v[12]), halved=int(v[13])))
    return hdr, r, ev
def start_line(txt): return int([l for l in txt.splitlines() if l.startswith("START")][0].split()[1])

print(sh(B + "cxlp_mkstore", STORE, "16384", "16384", "/dev/dax0.0", "/dev/dax1.0").stdout.strip())

if "b2" in which:
    print("B2 probe"); log = f"{out}/B2-daemon.csv"; d = start_daemon(log); time.sleep(3)
    hz = os.sysconf("SC_CLK_TCK"); c0 = cpu_ticks(d.pid); t0 = time.time()
    w = sh(B + "cxlp_writers", STORE, "1", "112", "6"); c1 = cpu_ticks(d.pid); dt = time.time() - t0
    pct = 100.0 * (c1 - c0) / hz / dt
    print("   ", w.stdout.strip().splitlines()[-1]); print(f"    daemon CPU while writers are active (10 ms probes, 50 ms epochs): {pct:.2f}% of one core")
    check(pct <= 2.0, "probe + policy overhead <= 2% of one core")
    time.sleep(1); a = sh(B + "dram_aggressor", "80", "32", "6"); time.sleep(1); stop(d)
    hdr, r, ev = rows(log); t0m = int(hdr["t0_mono_ns"]); a0 = (start_line(a.stdout) - t0m) / 1e6
    idle = sorted(x["mean"] for x in r if x["t"] < 2500); sat = sorted(x["mean"] for x in r if a0 + 1500 < x["t"] < a0 + 5500)
    pi, ps = idle[len(idle) // 2], sat[len(sat) // 2]
    print(f"    idle {pi:.1f} ns per load; under 80 NT writers ({a.stdout.strip().splitlines()[-1]}) {ps:.1f} ns = {ps/pi:.1f}x")
    check(90 <= pi <= 150, "idle value in the range seen in V5 (100-140 ns)"); check(ps / pi >= 4.0, "saturated DRAM reads >= 4x idle (V5: 6.5x)")

if "b3" in which:
    print("B3 CXL-full signal (spill forced to 0 so CXL stays the only target)"); log = f"{out}/B3-daemon.csv"; d = start_daemon(log); sh(B + "cxlp_admin", STORE, "force", "0")
    time.sleep(1); w1 = sh(B + "cxlp_writers", STORE, "1", "112", "5", "20480"); time.sleep(1.5); wu = sh(B + "cxlp_writers", STORE, "1", "112", "5"); time.sleep(1.5)
    w4 = sh(B + "cxlp_writers", STORE, "4", "112", "5"); time.sleep(0.5); sh(B + "cxlp_admin", STORE, "force", "-1"); stop(d)
    hdr, r, ev = rows(log); t0m = int(hdr["t0_mono_ns"]); s1 = (start_line(w1.stdout) - t0m) / 1e6; s4 = (start_line(w4.stdout) - t0m) / 1e6
    su = (start_line(wu.stdout) - t0m) / 1e6; ru = [x for x in r if su + 500 < x["t"] < su + 4500 and x["active"]]; fu = sum(x["full"] == 1 for x in ru) / max(1, len(ru))
    r1 = [x for x in r if s1 + 500 < x["t"] < s1 + 4500 and x["active"]]; r4 = [x for x in r if s4 + 500 < x["t"] < s4 + 4500 and x["active"]]
    f1 = sum(x["full"] == 1 for x in r1) / max(1, len(r1)); f4 = sum(x["full"] == 1 for x in r4) / max(1, len(r4))
    print(f"    calibrated: solo {hdr['solo_GiBs']} GiB/s, capacity {hdr['cap_GiBs']} GiB/s")
    print(f"    1 writer limited to 20 GiB/s: {w1.stdout.strip().splitlines()[-1]}\n               epochs flagged full: {100*f1:.0f}% of {len(r1)}")
    print(f"    1 writer, unlimited (info): {wu.stdout.strip().splitlines()[-1]}\n               epochs flagged full: {100*fu:.0f}% of {len(ru)}  <- one core already pushes ~94% of the pair's write capacity")
    print(f"    4 writers: {w4.stdout.strip().splitlines()[-1]}\n               epochs flagged full: {100*f4:.0f}% of {len(r4)}")
    check(f4 >= 0.9, "4 writers: CXL write direction reported full")
    check(f1 <= 0.1, "1 writer at 20 GiB/s (half the capacity): not reported full")

if "b4" in which:
    print("B4 controller, live"); log = f"{out}/B4-daemon.csv"; sh(B + "cxlp_admin", STORE, "force", "-1"); d = start_daemon(log)
    w = subprocess.Popen([B + "cxlp_writers", STORE, "4", "112", "16", "15360"], stdout=subprocess.PIPE, text=True)   # 4 x 15 GiB/s demand
    time.sleep(7.5); a = sh(B + "dram_aggressor", "64", "32", "4"); wout = w.communicate()[0]; time.sleep(0.5); stop(d)
    hdr, r, ev = rows(log); t0m = int(hdr["t0_mono_ns"]); a0 = (start_line(a.stdout) - t0m) / 1e6
    a1 = (int([l for l in a.stdout.splitlines() if l.startswith("END")][0].split()[1]) - t0m) / 1e6
    print("   ", wout.strip().splitlines()[-1]); print("   ", a.stdout.strip().splitlines()[-1], f"(from {a0:.0f} ms to {a1:.0f} ms of the daemon log)")
    ups = [(p, q) for p, q in zip(r, r[1:]) if q["spill"] > p["spill"]]
    bad = [q for p, q in ups if not (q["full"] == 1 and q["mean"] <= 1.05 * q["base"] + 0.06)]
    before = [x for x in r if x["t"] < a0]; peak = max(x["spill"] for x in before); at = [x for x in before if x["t"] > a0 - 1000]
    print(f"    before the aggressor: {len([1 for p, q in ups if q['t'] < a0])} increases, peak spill {peak}/16, last second: spill {at[-1]['spill']}/16, CXL {at[-1]['cxl']:.1f} + DRAM {at[-1]['dram']:.1f} GiB/s, probe {at[-1]['mean']:.1f} vs reference {at[-1]['base']:.1f}")
    check(peak > 0, "spill rose while CXL was full and DRAM calm"); check(not bad, f"every increase happened in an epoch with CXL full and probe <= 1.05 x reference ({len(ups)} increases checked)")
    hv = [e for e in ev if e[0] >= a0]; 
    if hv:
        print(f"    aggressor starts at {a0:.0f} ms; first halving at {hv[0][0]:.0f} ms = {hv[0][0]-a0:.0f} ms later (probe {hv[0][1]:.0f} ns)")
        z = [x for x in r if x["t"] >= a0 and x["spill"] == 0]
        if z: print(f"    spill reaches 0 at {z[0]['t']:.0f} ms = {z[0]['t']-a0:.0f} ms after the aggressor started")
    check(bool(hv) and hv[0][0] - a0 <= 50, "first halving within 50 ms of the injected DRAM aggressor")
    during = [x for x in r if a0 + 500 < x["t"] < a1 - 100]; check(max(x["spill"] for x in during) == 0, "no spill while the aggressor runs")
    after = [x for x in r if x["t"] > a1 + 1000]; check(bool(after) and max(x["spill"] for x in after) > 0, "spill rises again after the aggressor leaves")

sh(B + "cxlp_admin", STORE, "destroy")
print("PASS" if not fails else "FAIL: " + "; ".join(fails)); sys.exit(1 if fails else 0)
