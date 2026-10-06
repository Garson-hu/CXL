#!/usr/bin/env python3
"""E2b gate (2026-10-06): a CPU-resident state dict (the CPU-offloaded optimizer case) checkpointed with dcp.async_save
through cxlpath goes through OBJECTS (segment-sized chunks placed one by one, so the DRAM loan applies), drains into one
file per checkpoint, and reloads byte-exactly: from CXL (or the DRAM copies) while the version lives, from the file after
the store is gone. usage: test_dcp_cpu_objects.py <outdir>"""
import os, shutil, signal, subprocess, sys, time
import torch, torch.distributed.checkpoint as dcp
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cxlpath_dcp import CxlpathWriter, CxlpathReader
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "build"); out = sys.argv[1]; os.makedirs(out, exist_ok=True)
ROOT = "/mnt/local/ghu4/cxlpath_test/dcp_cpu"; shutil.rmtree(ROOT, ignore_errors=True); os.makedirs(ROOT); fails = []
def check(ok, msg): print(("  ok   " if ok else "  FAIL ") + msg, flush=True); (None if ok else fails.append(msg))
def sh(*a): return subprocess.run(a, capture_output=True, text=True)
sh(f"{B}/cxlp_mkstore", "torch", "8192", "4096", "/dev/dax0.0", "/dev/dax1.0")
import atexit
d = subprocess.Popen([f"{B}/cxlpathd", "torch", "--cpu", "16", "--log", f"{out}/E2b-daemon.csv"])
atexit.register(lambda: (d.poll() is None) and d.send_signal(signal.SIGTERM))
for _ in range(200):
    time.sleep(0.05)
    if "alive=1" in sh(f"{B}/cxlp_admin", "torch", "view").stdout: break
os.environ.setdefault("CXLPATH_COPY_CPUS", "96,97,98,99,112,113,114,115")
torch.manual_seed(0)
sd = {f"layer{i}": torch.rand((1 << 26,), dtype=torch.float32) for i in range(6)}            # 6 x 256 MiB = 1.5 GiB on the CPU
extra = {"meta": {"step": 7, "lr": 3e-4}, "rng": torch.arange(10, dtype=torch.int64)}
def state(): return {"model": sd, "extra": extra}
W = CxlpathWriter(store="torch", capacity_bytes=64 << 20, client="hl")                         # a small buffer set: CPU tensors do not use it
refs = {}
def load_and_compare(v, reader):
    fresh = {"model": {k: torch.zeros_like(t) for k, t in refs[v].items()}, "extra": {"meta": {"step": 0, "lr": 0.0}, "rng": torch.zeros(10, dtype=torch.int64)}}
    t0 = time.time(); dcp.load(fresh, storage_reader=reader, checkpoint_id=f"{ROOT}/v{v}"); dt = time.time() - t0
    same = all(torch.equal(fresh["model"][k], refs[v][k]) for k in refs[v]) and fresh["extra"]["meta"] == extra["meta"] and torch.equal(fresh["extra"]["rng"], torch.arange(10))
    return same, reader.source, dt
for v in (1, 2, 3):
    refs[v] = {k: t.clone() for k, t in sd.items()}; t0 = time.time()
    fut = dcp.async_save(state(), storage_writer=W, checkpoint_id=f"{ROOT}/v{v}"); t_block = time.time() - t0
    for t in sd.values(): t.add_(1.0)                                                            # training mutates every weight right after
    fut.result()
    print(f"    v{v}: training blocked {t_block:.2f} s; staged {W.stats['bytes']/2**20:.0f} MiB in {W.stats['stage_s']:.2f} s = {W.stats['bytes']/2**30/max(W.stats['stage_s'],1e-9):.2f} GiB/s; objects {len(W._objs)}", flush=True)
    if v == 1:
        same, src, dt = load_and_compare(1, CxlpathReader(store="torch")); check(same and src == "cxl", f"v1 reloaded from {src.upper()} in {dt:.2f} s: checkpoint-time values, not the mutated tensors")
t0 = time.time()
while not W.drained() and time.time() - t0 < 180: time.sleep(0.1)
check(W.drained(), f"v3 durable after {time.time() - t0:.1f} s of waiting")
for v in (1, 2, 3): print(f"    v{v} object file on NVMe: {os.path.getsize(f'{ROOT}/v{v}/cxlpath_obj_rank0.bin')/2**20:.0f} MiB")
same, src, dt = load_and_compare(3, CxlpathReader(store="torch")); check(same and src == "cxl", f"v3 (newest) reloaded from {src.upper()} in {dt:.2f} s")
same, src, dt = load_and_compare(1, CxlpathReader(store="torch")); check(same, f"v1 reloaded from {src.upper()} in {dt:.2f} s, byte-exact (its objects may have been reclaimed: then from the file)")
v = sh(f"{B}/cxlp_admin", "torch", "view").stdout; print("    " + v.strip().replace("\n", "\n    "))
d.send_signal(signal.SIGTERM); d.wait(); sh(f"{B}/cxlp_admin", "torch", "destroy")
same, src, dt = load_and_compare(3, CxlpathReader(store=None)); check(same and src == "nvme", f"after the store is gone (reboot): v3 reloaded from {src.upper()} in {dt:.2f} s, byte-exact")
shutil.rmtree(ROOT, ignore_errors=True)
print("PASS" if not fails else "FAIL: " + "; ".join(fails)); sys.exit(1 if fails else 0)
