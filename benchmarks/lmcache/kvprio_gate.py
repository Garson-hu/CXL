#!/usr/bin/env python3
"""KV-priority gate for ckpt_cxl (2026-10-12): reads the GPU's cumulative host->GPU PCIe byte counter about every
0.5 ms and sets the byte /dev/shm/kvprio_flag to 1 while the host->GPU rate is above <threshold_GBps> (KV blocks being
loaded), and back to 0 after <hold_ms> below it. Logs "G <mono_ns> <0|1>" on every change. Runs until SIGTERM.
usage: kvprio_gate.py [threshold_GBps=1.0] [hold_ms=5]"""
import mmap, os, signal, sys, time
import pynvml as N
thr = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0; hold = (float(sys.argv[2]) if len(sys.argv) > 2 else 5.0) / 1000
N.nvmlInit(); h = N.nvmlDeviceGetHandleByIndex(0); F = [N.NVML_FI_DEV_PCIE_COUNT_RX_BYTES]
fd = os.open("/dev/shm/kvprio_flag", os.O_RDWR | os.O_CREAT, 0o644); os.ftruncate(fd, 4096); m = mmap.mmap(fd, 4096); m[0] = 0
stop = False
def on_term(s, f):
    global stop; stop = True
signal.signal(signal.SIGTERM, on_term); signal.signal(signal.SIGINT, on_term)
prev = N.nvmlDeviceGetFieldValues(h, F)[0].value.uiVal; tp = time.monotonic(); last_high = 0.0; state = 0
print(f"# kvprio_gate threshold {thr} GB/s hold {hold * 1000:.0f} ms start {time.monotonic_ns()}", flush=True)
while not stop:
    time.sleep(0.0005)
    v = N.nvmlDeviceGetFieldValues(h, F)[0].value.uiVal; t = time.monotonic()
    rate = ((v - prev) % (1 << 32)) / (t - tp) / 1e9 if t > tp else 0; prev, tp = v, t
    if rate > thr: last_high = t
    want = 1 if t - last_high < hold else 0
    if want != state: state = want; m[0] = want; print(f"G {time.monotonic_ns()} {want}", flush=True)
m[0] = 0
