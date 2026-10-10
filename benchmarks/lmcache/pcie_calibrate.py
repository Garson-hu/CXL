import time, torch, threading, pynvml as N
N.nvmlInit(); h = N.nvmlDeviceGetHandleByIndex(0)
peak = {"TX": 0, "RX": 0}; stop = False; gens = set()
def loop(name, c):
    while not stop:
        v = N.nvmlDeviceGetPcieThroughput(h, c) / 1000; peak[name] = max(peak[name], v)
        gens.add(N.nvmlDeviceGetCurrPcieLinkGeneration(h))
th = [threading.Thread(target=loop, args=a) for a in (("TX", N.NVML_PCIE_UTIL_TX_BYTES), ("RX", N.NVML_PCIE_UTIL_RX_BYTES))]
for t in th: t.start()
g = torch.empty(1 << 30, dtype=torch.uint8, device="cuda"); g.fill_(7)
for kind in ("pinned", "pageable"):
    host = torch.empty(1 << 30, dtype=torch.uint8, pin_memory=(kind == "pinned")); host.fill_(3)
    for d in ("D2H", "H2D"):
        peak.update(TX=0, RX=0); torch.cuda.synchronize(); t0 = time.time()
        for _ in range(8):
            (host.copy_(g) if d == "D2H" else g.copy_(host))
        torch.cuda.synchronize(); dt = time.time() - t0
        time.sleep(0.05)
        print(f"{kind:8s} {d}: {8/dt:.2f} GiB/s by wall clock; NVML peak TX {peak['TX']:.0f} MB/s RX {peak['RX']:.0f} MB/s")
stop = True; [t.join() for t in th]; print("link generations seen:", sorted(gens))
