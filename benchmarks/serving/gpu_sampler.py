#!/usr/bin/env python3
"""GPU-side sampler for the 2026-11-04 serving study, until SIGTERM / SIGINT. Two kinds of lines on stdout:
  "C <mono_ns at the end of the bin> <tx_bytes> <rx_bytes>"   NVML's cumulative PCIe byte counters (32-bit, wrapping),
        polled ~1 ms apart and summed into 5 ms bins (the method of benchmarks/lmcache/pcie_sampler.py v2, 2026-10-10):
        exact totals, bursts resolved to ~5 ms. TX = GPU -> host (KV stores), RX = host -> GPU (KV loads). Link bytes
        include protocol overhead: ~1.12x (D2H) / ~1.09x (H2D) the payload (calibration of 2026-10-10).
  "U <mono_ns> <util_gpu %> <util_mem %> <mem_used_MiB>"      nvmlDeviceGetUtilizationRates every `util_ms` ms: the share
        of NVML's own sample period (1/6 s .. 1 s on this product class) in which a kernel was running - a coarse view;
        the engine-step log of vllmevt is the fine-grained one.
usage: gpu_sampler.py [gpu_index=0] [util_ms=50]"""
import signal, sys, threading, time
import pynvml as N

N.nvmlInit(); h = N.nvmlDeviceGetHandleByIndex(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
UTIL_MS = int(sys.argv[2]) if len(sys.argv) > 2 else 50
stop = threading.Event(); lock = threading.Lock()
signal.signal(signal.SIGTERM, lambda s, f: stop.set()); signal.signal(signal.SIGINT, lambda s, f: stop.set())
F = [N.NVML_FI_DEV_PCIE_COUNT_TX_BYTES, N.NVML_FI_DEV_PCIE_COUNT_RX_BYTES]
BIN = 5_000_000

def emit(s):
    with lock: print(s, flush=False)

def util():
    while not stop.is_set():
        try:
            u = N.nvmlDeviceGetUtilizationRates(h); m = N.nvmlDeviceGetMemoryInfo(h); t = time.monotonic_ns()
            emit(f"U {t} {u.gpu} {u.memory} {m.used >> 20}")
        except Exception as e:
            emit(f"# util error {e!r}")
        stop.wait(UTIL_MS / 1000)

def cumulative():
    prev = [x.value.uiVal for x in N.nvmlDeviceGetFieldValues(h, F)]
    bin_end = (time.monotonic_ns() // BIN + 1) * BIN; acc = [0, 0]
    while not stop.is_set():
        v = [x.value.uiVal for x in N.nvmlDeviceGetFieldValues(h, F)]; t = time.monotonic_ns()
        d = [(v[i] - prev[i]) % (1 << 32) for i in (0, 1)]; prev = v
        while t >= bin_end:                       # the delta belongs to the bin in which it was read
            emit(f"C {bin_end} {acc[0]} {acc[1]}"); acc = [0, 0]; bin_end += BIN
        acc[0] += d[0]; acc[1] += d[1]
        time.sleep(0.0005)

print(f"# gpu_sampler start {time.monotonic_ns()} wall {time.time():.6f} gpu {N.nvmlDeviceGetName(h)} util_ms {UTIL_MS}", flush=True)
ths = [threading.Thread(target=cumulative, daemon=True), threading.Thread(target=util, daemon=True)]
for t in ths: t.start()
while not stop.is_set():
    stop.wait(1.0); sys.stdout.flush()
print(f"# gpu_sampler end {time.monotonic_ns()}", flush=True)
