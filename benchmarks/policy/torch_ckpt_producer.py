#!/usr/bin/env python3
"""The real-library producer: a PyTorch process checkpoints a CPU-resident state dict with
torch.distributed.checkpoint.async_save every <period> s, beside a co-located victim.
  dcp-dram     stock DCP: FileSystemWriter + BlockingAsyncStager (torch.distributed.checkpoint.staging):
               stage() copies the state into a cached CPU state dict in DRAM (torch copy_, i.e. plain
               stores, on torch's thread pool) on the calling thread, then a background thread serialises
               it to .distcp files on NVMe                      -> today's practice
               (async_save's default fallback, _offload_state_dict_to_cpu, does NOT copy a CPU-resident
               state dict at all: it hands the live tensors to the background thread, so a checkpoint of
               a CPU-offloaded optimizer would be torn; the documented way to snapshot is the stager)
  dcp-cxlpath  CxlpathWriter: stage() copies into a CXL buffer set (NT stores, pinned copy threads),
               write_data() moves nothing, the daemon drains the set to NVMe without touching DRAM
Prints, per checkpoint: COPY <i> START <ns> END <ns> bytes=<n> GiBs=<x> dram_share=<1|0>  (the STAGE window,
during which the training thread of this process is blocked) and PERSIST <i> START <ns> END <ns> (until the
data is durable: the DCP future for dcp-dram, the buffer-set drain flag for dcp-cxlpath).
usage: torch_ckpt_producer.py <dcp-dram|dcp-cxlpath> <state_GiB> <period_s> <periods> <root_dir> [store]"""
import os, shutil, sys, time
import torch, torch.distributed.checkpoint as dcp
from torch.distributed.checkpoint import FileSystemWriter
from torch.distributed.checkpoint.staging import BlockingAsyncStager
class StockStagingWriter(FileSystemWriter, BlockingAsyncStager):
    """the two stock components combined: DRAM staging copy + file serialisation"""
    def __init__(self, path):
        FileSystemWriter.__init__(self, path); BlockingAsyncStager.__init__(self, cache_staged_state_dict=True)
sys.path.insert(0, os.path.expanduser("~/CXL/system/cxlpath/clients/pytorch"))
mode, gib, period, periods, root = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
store = sys.argv[6] if len(sys.argv) > 6 else "policy"
torch.set_num_threads(8)                                     # the copy threads of the stock path; ours are pinned by CXLPATH_COPY_CPUS
g = torch.Generator().manual_seed(1)                          # 1 GiB tensors of random data: every cache line non-zero (see 2026-09-22-zero-line-writes.md;
sd = {f"layer{i}": torch.rand((1 << 28,), dtype=torch.float32, generator=g) for i in range(gib)}   # the runs of 2026-09-22 used torch.full(i): layer0 all zero, the rest non-zero)
nbytes = sum(t.numel() * 4 for t in sd.values())
if mode == "dcp-cxlpath":
    from cxlpath_dcp import CxlpathWriter
    W = CxlpathWriter(store=store, capacity_bytes=nbytes + (64 << 20), client="hl")
else: W = StockStagingWriter(f"{root}/v0")                  # async_save resets the path per checkpoint_id
shutil.rmtree(root, ignore_errors=True); os.makedirs(root)
print(f"READY {time.monotonic_ns()} mode={mode} state_GiB={gib}", flush=True)
next_t = time.monotonic()
for i in range(periods):
    while time.monotonic() < next_t: time.sleep(0.001)
    cid = f"{root}/v{i}"
    t0 = time.monotonic_ns()
    fut = dcp.async_save(sd, storage_writer=W, checkpoint_id=cid)
    t1 = time.monotonic_ns()                                  # stage() has returned: the training thread is free again
    print(f"COPY {i} START {t0} END {t1} bytes={nbytes} GiBs={nbytes / ((t1 - t0) / 1e9) / 2**30:.2f} dram_share={1.0 if mode == 'dcp-dram' else 0.0}", flush=True)
    if mode == "dcp-dram": fut.result(); t2 = time.monotonic_ns()
    else:
        fut.result(); which = W.which
        while not W.drained(which): time.sleep(0.05)
        t2 = time.monotonic_ns()
    print(f"PERSIST {i} START {t1} END {t2} durable_s={(t2 - t1) / 1e9:.2f}", flush=True)
    if i >= 1: shutil.rmtree(f"{root}/v{i-1}", ignore_errors=True)
    next_t += period
print(f"DONE {time.monotonic_ns()}", flush=True)
