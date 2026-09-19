#!/usr/bin/env python3
"""E2 gate: a model on the GPU is checkpointed with dcp.async_save through cxlpath; training mutates
the model right after; reloading gives the checkpoint-time tensors exactly — from CXL, from NVMe for
a version whose buffer set was overwritten, and from NVMe after the store is gone (reboot).
usage: test_dcp_cxlpath.py <outdir>   (needs cxlp_mkstore / cxlpathd in ../../build)"""
import os, shutil, signal, subprocess, sys, time
import torch, torch.distributed.checkpoint as dcp
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cxlpath_dcp import CxlpathWriter, CxlpathReader
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "build"); out = sys.argv[1]; os.makedirs(out, exist_ok=True)
ROOT = "/mnt/local/ghu4/cxlpath_test/dcp"; shutil.rmtree(ROOT, ignore_errors=True); os.makedirs(ROOT); fails = []
def check(ok, msg): print(("  ok   " if ok else "  FAIL ") + msg, flush=True); (None if ok else fails.append(msg))
def sh(*a): return subprocess.run(a, capture_output=True, text=True)
sh(f"{B}/cxlp_mkstore", "torch", "8192", "2048", "/dev/dax0.0", "/dev/dax1.0")
import atexit
d = subprocess.Popen([f"{B}/cxlpathd", "torch", "--cpu", "16", "--log", f"{out}/E2-daemon.csv"])
atexit.register(lambda: (d.poll() is None) and d.send_signal(signal.SIGTERM))
for _ in range(200):
    time.sleep(0.05)
    if "alive=1" in sh(f"{B}/cxlp_admin", "torch", "view").stdout: break

torch.manual_seed(0)
model = torch.nn.Sequential(*[torch.nn.Linear(4096, 4096) for _ in range(24)]).cuda()          # 24 x 64 MiB = 1.5 GiB of fp32
opt_like = {"step": 7, "lr": 3e-4, "betas": (0.9, 0.95)}
def state(): return {"model": model.state_dict(), "extra": {"meta": opt_like, "rng": torch.arange(10, dtype=torch.int64)}}
nbytes = sum(p.numel() * p.element_size() for p in model.parameters())
W = CxlpathWriter(store="torch", capacity_bytes=2 << 30)
refs = {}
def flat(sd): return {k: v.detach().cpu().clone() for k, v in sd["model"].items()}
def load_and_compare(v, reader):
    fresh = {"model": {k: torch.zeros_like(t) for k, t in refs[v].items()}, "extra": {"meta": {"step": 0, "lr": 0.0, "betas": (0.0, 0.0)}, "rng": torch.zeros(10, dtype=torch.int64)}}
    t0 = time.time(); dcp.load(fresh, storage_reader=reader, checkpoint_id=f"{ROOT}/v{v}"); dt = time.time() - t0
    same = all(torch.equal(fresh["model"][k], refs[v][k]) for k in refs[v]) and fresh["extra"]["meta"] == opt_like and torch.equal(fresh["extra"]["rng"], torch.arange(10))
    return same, reader.source, dt

print(f"model state: {nbytes/2**20:.0f} MiB on {torch.cuda.get_device_name(0)}")
for v in (1, 2, 3):
    refs[v] = flat(state()); t0 = time.time()
    fut = dcp.async_save(state(), storage_writer=W, checkpoint_id=f"{ROOT}/v{v}"); t_block = time.time() - t0
    with torch.no_grad():
        for p in model.parameters(): p.add_(1.0)                      # training goes on and changes every weight
    fut.result()
    print(f"    v{v}: training blocked {t_block:.2f} s (waited {W.stats['wait_s']:.2f} s for a free buffer set, copied {W.stats['bytes']/2**20:.0f} MiB GPU->CXL in {W.stats['stage_s']:.2f} s = {W.stats['bytes']/2**30/max(W.stats['stage_s'],1e-9):.2f} GiB/s)", flush=True)
    if v == 1:
        same, src, dt = load_and_compare(1, CxlpathReader(store="torch")); check(same and src == "cxl", f"v1 reloaded from {src.upper()} in {dt:.2f} s: checkpoint-time values, not the mutated model")
check(W.stats["wait_s"] > 0.2, "v3 had to wait until v1 was on NVMe before it could overwrite v1's buffer set (back-pressure)")
t0 = time.time()
while not (W.drained(0) and W.drained(1)) and time.time() - t0 < 120: time.sleep(0.1)
for v in (1, 2, 3): print(f"    v{v} on NVMe: {os.path.getsize(f'{ROOT}/v{v}/cxlpath_data_rank0.bin')/2**20:.0f} MiB")
same, src, dt = load_and_compare(3, CxlpathReader(store="torch")); check(same and src == "cxl", f"v3 (newest, still in its buffer set) reloaded from {src.upper()} in {dt:.2f} s")
same, src, dt = load_and_compare(1, CxlpathReader(store="torch")); check(same and src == "nvme", f"v1 (its buffer set now holds v3) reloaded from {src.upper()} in {dt:.2f} s, byte-exact")
same, src, dt = load_and_compare(2, CxlpathReader(store="torch")); check(same, f"v2 reloaded from {src.upper()} in {dt:.2f} s")
d.send_signal(signal.SIGTERM); d.wait(); sh(f"{B}/cxlp_admin", "torch", "destroy")
same, src, dt = load_and_compare(3, CxlpathReader(store=None)); check(same and src == "nvme", f"after the store is gone (reboot): v3 reloaded from {src.upper()} in {dt:.2f} s, byte-exact")
shutil.rmtree(ROOT, ignore_errors=True)
print("PASS" if not fails else "FAIL: " + "; ".join(fails)); sys.exit(1 if fails else 0)
