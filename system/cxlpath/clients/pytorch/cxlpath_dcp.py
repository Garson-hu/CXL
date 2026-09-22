"""cxlpath storage plugin for PyTorch Distributed Checkpoint (torch >= 2.5, dcp.async_save).

    writer = CxlpathWriter(store="torch", capacity_bytes=2 << 30)
    fut = dcp.async_save(state_dict, storage_writer=writer, checkpoint_id="/mnt/local/.../step_100")
    ...
    dcp.load(state_dict, storage_reader=CxlpathReader(store="torch"), checkpoint_id="/mnt/local/.../step_100")

What happens (DESIGN 10.2/10.3/10.6):
  stage()      the AsyncStager hook, on the training thread: every tensor is copied GPU -> a CXL
               BUFFER SET (long-lived, CUDA-registered once, two sets alternate). Per 32 MiB chunk
               the runtime picks the direct path (GPU writes CXL, no DRAM traffic) or the staged path
               (GPU -> small pinned DRAM buffer -> runtime copy thread -> CXL), following the ratio
               cxlpathd publishes. If neither set may be overwritten yet, stage() waits: back-pressure.
  write_data() moves no data: tensors already live in the buffer set; it records (offset, nbytes).
  finish()     writes the small metadata files and arms the drain; cxlpathd copies the raw buffer
               set to <checkpoint_id>/cxlpath_data_rank<r>.bin with O_DIRECT straight from CXL.
  reader       restores from the buffer set on CXL if that version is still there, else from NVMe.
Plain tensors and picklable objects only (no DTensor / ShardedTensor yet)."""
import copy, ctypes, io, os, pickle, time
import torch
from torch.distributed.checkpoint.metadata import Metadata, StorageMeta
from torch.distributed.checkpoint.planner import LoadItemType, WriteItemType
from torch.distributed.checkpoint.staging import AsyncStager
from torch.distributed.checkpoint.storage import StorageReader, StorageWriter, WriteResult
from torch.futures import Future
from torch.utils._pytree import tree_map

_LIB = None
def _lib():
    global _LIB
    if _LIB is None:
        here = os.path.dirname(os.path.abspath(__file__))
        L = ctypes.CDLL(os.environ.get("CXLPATH_LIB", os.path.join(here, "..", "..", "build", "libcxlpath.so")))
        u64, vp, ci, sz = ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int, ctypes.c_size_t
        L.cxlp_attach.argtypes = [ctypes.c_char_p]; L.cxlp_key_of.argtypes = [ctypes.c_char_p]; L.cxlp_key_of.restype = u64
        L.cxlp_bufset_create.argtypes = [u64, ci, ci, sz]; L.cxlp_bufset_map.argtypes = [u64, ci, ctypes.POINTER(sz)]; L.cxlp_bufset_map.restype = vp
        L.cxlp_bufset_begin.argtypes = [u64, u64]; L.cxlp_bufset_commit_drain.argtypes = [u64, ci, ctypes.c_char_p]
        L.cxlp_bufset_drained.argtypes = [u64, ci]; L.cxlp_bufset_newest.argtypes = [u64, ctypes.POINTER(u64)]
        L.cxlp_gpu_init.argtypes = [ci, ci]; L.cxlp_gpu_register.argtypes = [vp, sz]
        L.cxlp_gpu_copy_in.argtypes = [vp, vp, sz, ctypes.c_uint32, vp]; L.cxlp_copy_in.argtypes = [vp, vp, sz]
        L.cxlp_copy_in_par.argtypes = [vp, vp, sz, ci, ctypes.POINTER(ci)]
        L.cxlp_bufset_set_used.argtypes = [u64, ci, u64]
        L.cxlp_bufset_version.argtypes = [u64, ci]; L.cxlp_bufset_version.restype = ctypes.c_int64
        L.cxlp_dev_kind.argtypes = [ci]; L.cxlp_dev_free.argtypes = [ci]; L.cxlp_dev_free.restype = ctypes.c_uint32
        _LIB = L
    return _LIB

_ATTACHED = {}
def _attach(store):
    if store not in _ATTACHED:
        if _lib().cxlp_attach(store.encode()) != 0: raise RuntimeError(f"cxlpath store '{store}' not found")
        _ATTACHED[store] = True

def _arena(ptr, nbytes): return torch.frombuffer((ctypes.c_ubyte * nbytes).from_address(ptr), dtype=torch.uint8)

class CxlpathWriter(StorageWriter, AsyncStager):
    _synchronize_after_execute = False            # stage() returns only when the copy is complete
    _gpu_ready = False

    def __init__(self, store, capacity_bytes, client="dcp", rank=0, stream=2, copy_cpu=100, copy_cpus=None):
        L = _lib(); _attach(store)
        # CPU tensors are copied with NT stores by several pinned threads (one core cannot fill CXL);
        # CXLPATH_COPY_CPUS="96,97,98,99,112,113,114,115" or the copy_cpus argument
        cl = copy_cpus or [int(x) for x in os.environ.get("CXLPATH_COPY_CPUS", "").split(",") if x.strip()]
        self._cpus = (ctypes.c_int * len(cl))(*cl) if cl else None; self._ncopy = len(cl) if cl else 1
        self.store, self.rank, self.stream, self.cap = store, rank, stream, int(capacity_bytes)
        self.client = L.cxlp_key_of(f"{client}:{rank}".encode()); self.version = 0; self.path = None; self.which = -1
        cxl = [d for d in range(L.cxlp_ndev()) if L.cxlp_dev_kind(d) == 0]; dev = max(cxl, key=lambda d: L.cxlp_dev_free(d))
        self.ptr, self.arena = [None, None], [None, None]
        if not CxlpathWriter._gpu_ready and torch.cuda.is_available():
            torch.cuda.init(); L.cxlp_gpu_init(1, copy_cpu); CxlpathWriter._gpu_ready = True
        for w in (0, 1):
            if L.cxlp_bufset_create(self.client, w, dev, self.cap) != 0: raise RuntimeError("cannot create the buffer set (not enough free CXL segments?)")
            n = ctypes.c_size_t(); self.ptr[w] = L.cxlp_bufset_map(self.client, w, ctypes.byref(n)); self.arena[w] = _arena(self.ptr[w], self.cap)
            if CxlpathWriter._gpu_ready: L.cxlp_gpu_register(self.ptr[w], self.cap)      # once per set: ~20 ms per GiB
        self.stats = dict(wait_s=0.0, stage_s=0.0, bytes=0); self._staged = {}

    # ---- AsyncStager ----
    def stage(self, state_dict):
        L = _lib(); t0 = time.time(); self.version += 1
        while True:                                   # back-pressure: the set we would overwrite is not on NVMe yet
            w = L.cxlp_bufset_begin(self.client, self.version)
            if w >= 0: break
            time.sleep(0.01)
        t1 = time.time(); self.which = w; off = [0]; base = self.ptr[w]; arena = self.arena[w]
        def put(x):
            if not torch.is_tensor(x): return copy.deepcopy(x)
            src = x.detach().contiguous(); n = src.numel() * src.element_size(); o = (off[0] + 63) & ~63
            if o + n > self.cap: raise RuntimeError("state_dict larger than the buffer set capacity")
            if n:
                if src.is_cuda: torch.cuda.current_stream().synchronize(); rc = L.cxlp_gpu_copy_in(base + o, src.data_ptr(), n, self.stream, None)
                else: rc = 0; L.cxlp_copy_in_par(base + o, src.data_ptr(), n, self._ncopy, self._cpus)
                if rc != 0: raise RuntimeError("cxlpath GPU copy failed")
            off[0] = o + n
            return arena[o:o + n].view(src.dtype).view(src.shape)
        staged = tree_map(put, state_dict)
        self.stats = dict(wait_s=t1 - t0, stage_s=time.time() - t1, bytes=off[0]); self.used = off[0]
        # async_save calls reset(checkpoint_id) before stage(): remember what belongs to THIS checkpoint, so a
        # later stage() cannot disturb the background save of an earlier one
        self._staged[self.path] = (self.which, self.version, self.used)
        return staged

    def synchronize_staging(self): pass

    # ---- StorageWriter ----
    def reset(self, checkpoint_id=None):
        if checkpoint_id is not None: self.path = str(checkpoint_id)
        self.blobs = {}
    def _mine(self): return self._staged.get(self.path, (self.which, self.version, self.used))
    def set_up_storage_writer(self, is_coordinator): os.makedirs(self.path, exist_ok=True)
    def prepare_local_plan(self, plan): return plan
    def prepare_global_plan(self, plans): return plans
    def storage_meta(self): return StorageMeta(checkpoint_id=self.path)
    @classmethod
    def validate_checkpoint_id(cls, checkpoint_id): return True

    def write_data(self, plan, planner):
        which, _, _ = self._mine(); res = []; base = self.ptr[which]
        for item in plan.items:
            data = planner.resolve_data(item)
            if item.type == WriteItemType.BYTE_IO:
                b = data.getvalue(); self.blobs[item.index.fqn] = b
                res.append(WriteResult(index=item.index, size_in_bytes=len(b), storage_data=dict(kind="blob", fqn=item.index.fqn)))
            else:
                t = data.detach(); o = t.data_ptr() - base; n = t.numel() * t.element_size()
                if not (0 <= o and o + n <= self.cap): raise RuntimeError(f"{item.index.fqn}: tensor is not inside the cxlpath buffer set")
                res.append(WriteResult(index=item.index, size_in_bytes=n, storage_data=dict(kind="tensor", offset=o, nbytes=n, rank=self.rank)))
        f = Future(); f.set_result(res); return f

    def finish(self, metadata, results):
        metadata.storage_data = {r.index: r.storage_data for rs in results for r in rs}
        metadata.storage_meta = self.storage_meta()
        data_file = os.path.join(self.path, f"cxlpath_data_rank{self.rank}.bin")
        which, version, used = self._mine()
        info = dict(store=self.store, client=self.client, version=version, which=which, nbytes=self.cap, used=used, data_file=data_file, blobs=self.blobs)
        for name, obj in ((".metadata", metadata), (f".cxlpath_rank{self.rank}", info)):
            tmp = os.path.join(self.path, name + ".tmp")
            with open(tmp, "wb") as fh: pickle.dump(obj, fh); fh.flush(); os.fsync(fh.fileno())
            os.replace(tmp, os.path.join(self.path, name))
        _lib().cxlp_bufset_set_used(self.client, which, used)                     # drain the used prefix, not the whole set
        if _lib().cxlp_bufset_commit_drain(self.client, which, data_file.encode()) != 0: raise RuntimeError("cxlpath: commit failed")
        self._staged.pop(self.path, None)

    def drained(self, which=None): return _lib().cxlp_bufset_drained(self.client, self.which if which is None else which) == 1


class CxlpathReader(StorageReader):
    def __init__(self, store=None, rank=0): self.store, self.rank, self.path, self.source = store, rank, None, None
    def reset(self, checkpoint_id=None):
        if checkpoint_id is not None: self.path = str(checkpoint_id)
    def read_metadata(self):
        with open(os.path.join(self.path, ".metadata"), "rb") as fh: return pickle.load(fh)
    def set_up_storage_reader(self, metadata, is_coordinator): self.meta = metadata
    def prepare_local_plan(self, plan): return plan
    def prepare_global_plan(self, plans): return plans
    @classmethod
    def validate_checkpoint_id(cls, checkpoint_id): return True

    def _open(self, info):
        """The version still sits in its buffer set on CXL -> read in place; else the NVMe file.
        (Meant for restart: nothing protects a reader from a writer that starts overwriting the set.)"""
        if self.store is not None:
            try:
                L = _lib(); _attach(self.store)
                if L.cxlp_bufset_version(info["client"], info["which"]) == info["version"]:
                    n = ctypes.c_size_t(); p = L.cxlp_bufset_map(info["client"], info["which"], ctypes.byref(n))
                    if p: self.source = "cxl"; return _arena(p, info["nbytes"])
            except (RuntimeError, OSError): pass
        self.source = "nvme"
        return torch.from_file(info["data_file"], shared=False, size=os.path.getsize(info["data_file"]), dtype=torch.uint8)

    def read_data(self, plan, planner):
        with open(os.path.join(self.path, f".cxlpath_rank{self.rank}"), "rb") as fh: info = pickle.load(fh)
        arena = self._open(info)
        for item in plan.items:
            sd = self.meta.storage_data[item.storage_index]
            if item.type == LoadItemType.BYTE_IO:
                planner.load_bytes(item, io.BytesIO(info["blobs"][sd["fqn"]])); continue
            md = self.meta.state_dict_metadata[item.storage_index.fqn]
            t = arena[sd["offset"]:sd["offset"] + sd["nbytes"]].view(md.properties.dtype).view(md.size)
            for dim, (o, n) in enumerate(zip(item.storage_offsets, item.lengths)): t = torch.narrow(t, dim, o, n)
            target = planner.resolve_tensor(item).detach(); target.copy_(t); planner.commit_tensor(item, target)
        f = Future(); f.set_result(None); return f
