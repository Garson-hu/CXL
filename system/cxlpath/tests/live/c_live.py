#!/usr/bin/env python3
"""C1 live gate on c28: the daemon calibrates the read path and publishes k for a CPU consumer;
with the GPU module's constants the GPU consumer comes out as 'never'. Then a promotion under a
real daemon: an object read k times moves to the DRAM pool, byte-exact.
usage: c_live.py <outdir>"""
import os, subprocess, sys, time, signal, re
B = "build/"; out = sys.argv[1]; os.makedirs(out, exist_ok=True); fails = []
def sh(*a): return subprocess.run(a, capture_output=True, text=True)
def check(ok, msg): print(("  ok   " if ok else "  FAIL ") + msg); (None if ok else fails.append(msg))
sh(B + "cxlp_mkstore", "rd", "8192", "4096", "/dev/dax0.0", "/dev/dax1.0")
d = subprocess.Popen([B + "cxlpathd", "rd", "--cpu", "16", "--log", f"{out}/C-daemon.csv"])
for _ in range(200):
    time.sleep(0.05)
    if "alive=1" in sh(B + "cxlp_admin", "rd", "view").stdout: break
g = sh(B + "cxlp_gpu_test", "rd", "live", "2"); time.sleep(0.5)
r = sh(B + "cxlp_readers", "rd"); print(r.stdout.strip()); time.sleep(0.3)
d.send_signal(signal.SIGTERM); d.wait()
hdr = [l for l in open(f"{out}/C-daemon.csv") if l.startswith("# read path")]
print("   ", hdr[0].strip()[2:] if hdr else "no read-path calibration line")
m = re.search(r"k = (\d+)", hdr[0]) if hdr else None
check(bool(m) and int(m.group(1)) >= 1, "CPU consumer: a finite k from the calibrated constants")
check("k_gpu=0" in r.stdout, "GPU consumer on c28: never (reads CXL at link speed)")
check("PASS" in r.stdout, "object promoted after k reads under a real daemon, byte-exact, CXL copy released")
sh(B + "cxlp_admin", "rd", "destroy"); print("PASS" if not fails else "FAIL: " + "; ".join(fails)); sys.exit(1 if fails else 0)
