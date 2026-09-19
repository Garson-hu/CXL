#!/usr/bin/env python3
"""F1 helper: checkpoint a GPU model through cxlpath in a loop for <seconds>; every reload is compared
with the checkpoint-time values. usage: loop_dcp.py <store> <seconds> <root_dir>"""
import os, shutil, sys, time
import torch, torch.distributed.checkpoint as dcp
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cxlpath_dcp import CxlpathWriter, CxlpathReader
store, secs, root = sys.argv[1], float(sys.argv[2]), sys.argv[3]; shutil.rmtree(root, ignore_errors=True); os.makedirs(root)
torch.manual_seed(1); model = torch.nn.Sequential(*[torch.nn.Linear(4096, 4096) for _ in range(16)]).cuda()      # 1 GiB
W = CxlpathWriter(store=store, capacity_bytes=(1 << 30) + (64 << 20), client="f1dcp")
refs, errors, v, t_end, blocked, waited = {}, 0, 0, time.time() + secs, 0.0, 0.0
def verify(ver, expect_src=None):
    global errors
    fresh = {"model": {k: torch.zeros_like(t) for k, t in refs[ver].items()}}; r = CxlpathReader(store=store)
    dcp.load(fresh, storage_reader=r, checkpoint_id=f"{root}/v{ver}")
    if not all(torch.equal(fresh["model"][k], refs[ver][k]) for k in refs[ver]): errors += 1; print(f"DCP MISMATCH v{ver} from {r.source}", flush=True)
    return r.source
src_count = {"cxl": 0, "nvme": 0}
while time.time() < t_end:
    v += 1; refs[v] = {k: t.detach().cpu().clone() for k, t in model.state_dict().items()}; t0 = time.time()
    fut = dcp.async_save({"model": model.state_dict()}, storage_writer=W, checkpoint_id=f"{root}/v{v}"); blocked += time.time() - t0; waited += W.stats["wait_s"]
    with torch.no_grad():
        for p in model.parameters(): p.mul_(1.0001).add_(0.01)
    fut.result(); src_count[verify(v)] += 1                       # newest version: still on CXL
    if v >= 3:
        old = v - 2; t1 = time.time()
        while not os.path.exists(f"{root}/v{old}/cxlpath_data_rank0.bin") and time.time() - t1 < 60: time.sleep(0.05)
        src_count[verify(old)] += 1; refs.pop(old); shutil.rmtree(f"{root}/v{old}", ignore_errors=True)       # an overwritten version: from NVMe
    time.sleep(1.0)
print(f"DCP versions={v} reloads_from_cxl={src_count['cxl']} reloads_from_nvme={src_count['nvme']} mean_blocked_s={blocked/max(v,1):.2f} total_wait_for_set_s={waited:.1f} ERRORS={errors}", flush=True)
shutil.rmtree(root, ignore_errors=True); sys.exit(1 if errors else 0)
