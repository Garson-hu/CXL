#!/usr/bin/env python3
"""GPU <-> host PCIe traffic as the GPU itself counts it (NVML), until SIGTERM. (2026-10-10; v2 14:50)
Two sources:
  "C <mono ns at the end of the bin> <tx_bytes> <rx_bytes>": NVML's cumulative PCIe byte counters
     (NVML_FI_DEV_PCIE_COUNT_TX/RX_BYTES, 32-bit, wrapping) polled ~1 ms apart (a read takes 0.2-0.3 ms) and summed
     into 5 ms bins: exact totals and bursts resolved to ~5 ms. TX = GPU -> host (KV stores), RX = host -> GPU (loads).
  "P <TX|RX> <mono ns at the end of the window> <MB/s>": nvmlDeviceGetPcieThroughput, one 20 ms window per call
     (kept for continuity with v1; v1 runs lost windows when the sampler shared cores with the server).
Both count bytes on the link including protocol overhead (calibration: ~1.12x / ~1.09x the payload for D2H / H2D).
usage: pcie_sampler.py [gpu_index=0]"""
import signal, sys, threading, time
import pynvml as N

N.nvmlInit(); h = N.nvmlDeviceGetHandleByIndex(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
stop = threading.Event(); lock = threading.Lock()
signal.signal(signal.SIGTERM, lambda s, f: stop.set()); signal.signal(signal.SIGINT, lambda s, f: stop.set())
F = [N.NVML_FI_DEV_PCIE_COUNT_TX_BYTES, N.NVML_FI_DEV_PCIE_COUNT_RX_BYTES]
BIN = 5_000_000

def emit(s):
    with lock: print(s, flush=False)

def loop(name, counter):
    while not stop.is_set():
        kbs = N.nvmlDeviceGetPcieThroughput(h, counter); t = time.monotonic_ns()
        emit(f"P {name} {t} {kbs / 1000:.1f}")

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

print(f"# pcie_sampler v2 start {time.monotonic_ns()} gpu {N.nvmlDeviceGetName(h)}", flush=True)
ths = [threading.Thread(target=loop, args=a, daemon=True) for a in (("TX", N.NVML_PCIE_UTIL_TX_BYTES), ("RX", N.NVML_PCIE_UTIL_RX_BYTES))]
ths.append(threading.Thread(target=cumulative, daemon=True))
for t in ths: t.start()
while not stop.is_set():
    stop.wait(1.0); sys.stdout.flush()
print(f"# pcie_sampler end {time.monotonic_ns()}", flush=True)
