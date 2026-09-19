#!/usr/bin/env python3
"""D2 live gate: (a) writers are not slowed by a pending drain (the drain yields), and the backlog
drains once they stop; (b) a 10-version checkpoint loop on a store that holds only ~4 versions
completes through back-pressure, every file byte-identical.
usage: d_live.py <outdir>"""
import os, subprocess, sys, time, signal, re
B = "build/"; out = sys.argv[1]; os.makedirs(out, exist_ok=True); fails = []; DIR = "/mnt/local/ghu4/cxlpath_test"; os.makedirs(DIR, exist_ok=True)
def sh(*a): return subprocess.run(a, capture_output=True, text=True)
def check(ok, msg): print(("  ok   " if ok else "  FAIL ") + msg, flush=True); (None if ok else fails.append(msg))
def daemon(store, log):
    d = subprocess.Popen([B + "cxlpathd", store, "--cpu", "16", "--log", log])
    for _ in range(200):
        time.sleep(0.05)
        if "alive=1" in sh(B + "cxlp_admin", store, "view").stdout: return d
    raise SystemExit("daemon did not come up")
def total(txt): return float(re.search(r"total_GiBs=([\d.]+)", txt).group(1))

print("D2.a pacing: 4 unlimited writers with and without a 6 GiB drain backlog")
sh(B + "cxlp_mkstore", "dl", "16384", "0", "/dev/dax0.0", "/dev/dax1.0"); d = daemon("dl", f"{out}/D2a-daemon.csv")
w0 = sh(B + "cxlp_writers", "dl", "4", "112", "5"); t0 = total(w0.stdout); time.sleep(1)
bl = subprocess.Popen([B + "cxlp_ckpt_loop", "dl", "1", "6144", DIR, "backlog"], stdout=subprocess.PIPE, text=True)
while True:
    line = bl.stdout.readline()
    if "BACKLOG-READY" in line or not line: break
tb = time.time(); w1 = sh(B + "cxlp_writers", "dl", "4", "112", "5"); t1 = total(w1.stdout); tw = time.time() - tb
rest = bl.communicate()[0]; tdrain = time.time() - tb
print(f"    writers alone: {t0:.2f} GiB/s; with a 6 GiB backlog pending: {t1:.2f} GiB/s ({100*t1/t0:.1f}%)")
print(f"    the backlog finished {tdrain:.1f} s after the writers started ({tw:.1f} s of writers + drain at NVMe speed)")
check(t1 >= 0.9 * t0, "writer speed with a pending drain within 10% of no drain"); check("PASS" in rest, "backlog drained afterwards, file byte-identical")
d.send_signal(signal.SIGTERM); d.wait(); sh(B + "cxlp_admin", "dl", "destroy")

print("D2.b 10 versions of 2 GiB on a store of 8 GiB (4 versions fit), producer >> NVMe")
sh(B + "cxlp_mkstore", "dl", "4096", "0", "/dev/dax0.0", "/dev/dax1.0"); d = daemon("dl", f"{out}/D2b-daemon.csv"); tb = time.time()
lp = sh(B + "cxlp_ckpt_loop", "dl", "10", "2048", DIR); el = time.time() - tb
open(f"{out}/D2b-loop.txt", "w").write(lp.stdout); print("    " + "\n    ".join(lp.stdout.strip().splitlines()))
print(f"    whole loop incl. final drain and verification: {el:.0f} s for 20 GiB (NVMe sustains ~0.9 GiB/s)")
check("PASS" in lp.stdout and "files_ok=1" in lp.stdout, "all 10 versions written through back-pressure, every file byte-identical")
m = re.search(r"final_free=(\d+)/(\d+)", lp.stdout); check(bool(m) and m.group(1) == m.group(2), "all segments free at the end")
d.send_signal(signal.SIGTERM); d.wait(); sh(B + "cxlp_admin", "dl", "destroy")
print("PASS" if not fails else "FAIL: " + "; ".join(fails)); sys.exit(1 if fails else 0)
