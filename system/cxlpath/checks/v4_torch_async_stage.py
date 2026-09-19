#!/usr/bin/env python3
"""V4: can PyTorch's built-in async checkpoint (dcp.async_save, torch 2.5.1) stage into OUR
buffers (a devdax CXL mapping registered with CUDA) and restore correctly?
Hook = the AsyncStager protocol on the storage writer: stage() returns CPU tensors whose
storage lives on devdax. The touched devdax range is saved and restored."""
import mmap, os, sys, tempfile, shutil, ctypes, time
import torch, torch.distributed as dist, torch.distributed.checkpoint as dcp
from torch.distributed.checkpoint.staging import AsyncStager
from torch.distributed.checkpoint import FileSystemWriter, FileSystemReader

DEV = sys.argv[1] if len(sys.argv) > 1 else "/dev/dax0.0"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/mnt/local/ghu4/v4_ckpt"
SIZE = 512 << 20

fd = os.open(DEV, os.O_RDWR)
mm = mmap.mmap(fd, SIZE, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)
saved = bytes(mm[:])                                   # restore at the end
addr = ctypes.addressof(ctypes.c_char.from_buffer(mm))
rc = torch.cuda.cudart().cudaHostRegister(addr, SIZE, 0)
print("cudaHostRegister on devdax from Python:", "OK" if int(rc) == 0 else rc)
arena = torch.frombuffer(mm, dtype=torch.uint8)        # whole mapping as one CPU tensor

class DevdaxStager(FileSystemWriter, AsyncStager):
    """Bump-allocates staging tensors inside the devdax arena."""
    _synchronize_after_execute = False
    def __init__(self, path):
        super().__init__(path); self.off = 0; self.staged_ptrs = []
    def _alloc(self, t):
        n = t.numel() * t.element_size()
        self.off = (self.off + 63) & ~63
        view = arena[self.off:self.off + n].view(t.dtype).view(t.shape)
        self.off += n
        return view
    def stage(self, state_dict):
        self.off = 0; out = {}
        for k, v in state_dict.items():
            if torch.is_tensor(v):
                dst = self._alloc(v); dst.copy_(v, non_blocking=True)
                self.staged_ptrs.append(dst.data_ptr()); out[k] = dst
            else:
                out[k] = v
        torch.cuda.synchronize()
        return out

os.environ.setdefault("MASTER_ADDR", "127.0.0.1"); os.environ.setdefault("MASTER_PORT", "29533")
dist.init_process_group("gloo", rank=0, world_size=1)
torch.manual_seed(0)
model = torch.nn.Sequential(torch.nn.Linear(4096, 4096), torch.nn.ReLU(), torch.nn.Linear(4096, 4096)).cuda()
sd = {k: v for k, v in model.state_dict().items()}
ref = {k: v.detach().cpu().clone() for k, v in sd.items()}

shutil.rmtree(OUT, ignore_errors=True)
writer = DevdaxStager(OUT)
t = time.time()
fut = dcp.async_save(sd, storage_writer=writer)
t_stage = time.time() - t
with torch.no_grad():                                   # training continues: mutate the model
    for p in model.parameters(): p.add_(1.0)
fut.result()
lo, hi = addr, addr + SIZE
print("staged tensors inside the devdax mapping:", all(lo <= p < hi for p in writer.staged_ptrs), f"({len(writer.staged_ptrs)} tensors, {writer.off>>20} MiB)")
print(f"async_save returned after {t_stage*1e3:.0f} ms (staging only); files:", sorted(os.listdir(OUT)))

fresh = {k: torch.zeros_like(v) for k, v in ref.items()}
dcp.load(fresh, storage_reader=FileSystemReader(OUT))
print("restored == values at checkpoint time (not the mutated model):", all(torch.equal(fresh[k], ref[k]) for k in ref))

del arena, writer, sd, fresh
torch.cuda.cudart().cudaHostUnregister(addr)
mm[:] = saved
shutil.rmtree(OUT, ignore_errors=True)
dist.destroy_process_group()
