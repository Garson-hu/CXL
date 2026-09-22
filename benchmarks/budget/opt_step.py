#!/usr/bin/env python3
"""CPU optimizer step as a victim: fused Adam over <params_millions> fp32 parameters held in DRAM
(params + grads + two Adam states = 16 bytes per parameter), the CPU half of ZeRO-Offload-style training.
Every step reads and rewrites the whole state: a read-modify-write stream that is memory-bandwidth-bound.
usage: opt_step.py <threads> <params_millions> <steps>      prints "[STEP] i seconds" and START/END mono ns"""
import sys, time, torch
threads, pm, steps = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
torch.set_num_threads(threads)
n = pm * 1_000_000 // 8
params = [torch.zeros(n, requires_grad=True) for _ in range(8)]
for p in params: p.grad = torch.full_like(p, 1e-3)
opt = torch.optim.Adam(params, lr=1e-4, fused=True)
for _ in range(3): opt.step()                                   # allocate the states, warm up
print(f"START {time.monotonic_ns()}", flush=True)
for i in range(steps):
    t0 = time.perf_counter(); opt.step(); print(f"[STEP] {i} {time.perf_counter() - t0:.4f} {time.monotonic_ns()}", flush=True)   # step time and its end, monotonic ns
print(f"END {time.monotonic_ns()}", flush=True)
