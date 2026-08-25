#!/usr/bin/env python3
"""
embbench — embedding / feature-store row-gather benchmark.

Models the access pattern of:
  * recommender embedding lookup (DLRM-style sparse lookups)
  * GNN feature gather (per-neighbor row fetch)
  * RAG vector retrieval (top-k gather)

Allocates a single large [num_rows, row_dim] table and repeatedly gathers a
batch of random rows. Access distribution is either uniform or Zipfian.

Placement modes:
    --place=dram         table on NUMA node 0
    --place=cxl          table on NUMA node 1
    --place=interleave   table striped across nodes 0 and 1
    --place=skew         hot rows on DRAM, cold rows on CXL (Zipfian only)

Output is CSV to stdout.
"""
import argparse
import ctypes
import ctypes.util
import os
import sys
import time

import numpy as np


def get_libnuma():
    name = ctypes.util.find_library("numa")
    if not name:
        return None
    lib = ctypes.CDLL(name, use_errno=True)
    lib.numa_available.restype = ctypes.c_int
    lib.numa_node_size64.restype = ctypes.c_longlong
    lib.numa_node_size64.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_longlong)]
    lib.numa_alloc_onnode.restype = ctypes.c_void_p
    lib.numa_alloc_onnode.argtypes = [ctypes.c_size_t, ctypes.c_int]
    lib.numa_alloc_interleaved.restype = ctypes.c_void_p
    lib.numa_alloc_interleaved.argtypes = [ctypes.c_size_t]
    lib.numa_free.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    return lib


_libnuma = get_libnuma()
_NUMA_KEEPALIVE = []


class ObjAttr(ctypes.Structure):
    # Must match obj_attr_t in objplace.h.
    _fields_ = [
        ("type", ctypes.c_int),
        ("size", ctypes.c_size_t),
        ("access", ctypes.c_int),
        ("sensitivity", ctypes.c_int),
        ("hot_fraction", ctypes.c_double),
        ("skew_alpha", ctypes.c_double),
        ("phase", ctypes.c_int),
    ]


def get_objplace():
    """Load the ObjPlace runtime shared lib (system/placement/libobjplace.so)."""
    here = os.path.dirname(os.path.abspath(__file__))
    so = os.path.normpath(os.path.join(here, "..", "..", "system", "placement",
                                       "libobjplace.so"))
    if not os.path.exists(so):
        return None
    lib = ctypes.CDLL(so, use_errno=True)
    lib.obj_alloc_hint.restype = ctypes.c_void_p
    lib.obj_alloc_hint.argtypes = [ctypes.c_size_t, ctypes.c_int]
    lib.objplace_set_dram_budget.argtypes = [ctypes.c_size_t]
    lib.objplace_set_pressure.argtypes = [ctypes.c_double]
    lib.obj_create.restype = ctypes.c_void_p
    lib.obj_create.argtypes = [ctypes.POINTER(ObjAttr)]
    lib.obj_rebalance.argtypes = []
    lib.obj_placement.restype = ctypes.c_int
    lib.obj_placement.argtypes = [ctypes.c_void_p]
    lib.obj_hot_ptr.restype = ctypes.c_void_p
    lib.obj_hot_ptr.argtypes = [ctypes.c_void_p]
    lib.obj_cold_ptr.restype = ctypes.c_void_p
    lib.obj_cold_ptr.argtypes = [ctypes.c_void_p]
    lib.obj_hot_bytes.restype = ctypes.c_size_t
    lib.obj_hot_bytes.argtypes = [ctypes.c_void_p]
    lib.obj_cold_bytes.restype = ctypes.c_size_t
    lib.obj_cold_bytes.argtypes = [ctypes.c_void_p]
    return lib


_libobj = get_objplace()
# Hint enum values must match objplace.h.
HINT_BW_SENSITIVE, HINT_COLD_CAPACITY, HINT_SKEW_HOT, HINT_SKEW_COLD = 0, 1, 2, 3
# obj_attr_t enums.
OBJ_EMBEDDING, ACC_RANDOM, SENS_BANDWIDTH, PHASE_GATHER = 1, 1, 0, 4
PLACE_DRAM, PLACE_CXL, PLACE_SPLIT, PLACE_INTERLEAVE = 0, 1, 2, 3


def buf_from_ptr(ptr, size_bytes):
    buf = (ctypes.c_uint8 * size_bytes).from_address(ptr)
    arr = np.frombuffer(buf, dtype=np.uint8)
    _NUMA_KEEPALIVE.append((ptr, size_bytes, buf))
    return arr


def obj_alloc(size_bytes, hint):
    """Allocate via the placement prototype's obj_alloc_hint, return numpy view."""
    if _libobj is None:
        print("embbench: libobj_placement.so not found; build system/placement",
              file=sys.stderr)
        sys.exit(6)
    ptr = _libobj.obj_alloc_hint(size_bytes, hint)
    if not ptr:
        print(f"embbench: obj_alloc_hint(hint={hint}) failed", file=sys.stderr)
        sys.exit(5)
    buf = (ctypes.c_uint8 * size_bytes).from_address(ptr)
    arr = np.frombuffer(buf, dtype=np.uint8)
    _NUMA_KEEPALIVE.append((ptr, size_bytes, buf))
    return arr


def numa_alloc(size_bytes, node):
    if _libnuma is None or _libnuma.numa_available() < 0:
        return np.zeros(size_bytes, dtype=np.uint8)
    if node == "interleave":
        ptr = _libnuma.numa_alloc_interleaved(size_bytes)
    else:
        n = int(node)
        sz = _libnuma.numa_node_size64(n, None)
        if sz <= 0:
            print(f"embbench: NUMA node {n} has 0 MB online memory.",
                  file=sys.stderr)
            print("  Need: sudo daxctl online-memory dax2.0", file=sys.stderr)
            sys.exit(4)
        ptr = _libnuma.numa_alloc_onnode(size_bytes, n)
    if not ptr:
        print(f"embbench: numa_alloc failed for node={node}", file=sys.stderr)
        sys.exit(5)
    buf = (ctypes.c_uint8 * size_bytes).from_address(ptr)
    arr = np.frombuffer(buf, dtype=np.uint8)
    _NUMA_KEEPALIVE.append((ptr, size_bytes, buf))
    return arr


def alloc_table_objplace(num_rows, row_dim, dtype, hot_frac, skew_alpha):
    """Let the ObjPlace runtime decide placement for the embedding table.

    Registers the table as one OBJ_EMBEDDING object with its skew metadata,
    sizes the DRAM fast-tier budget to the hot partition, and uses whatever the
    planner returns (typically SPLIT: hot rows on DRAM, cold tail on CXL)."""
    if _libobj is None:
        print("embbench: libobjplace.so not found; build system/placement",
              file=sys.stderr)
        sys.exit(6)
    row_bytes = row_dim * np.dtype(dtype).itemsize
    total_bytes = num_rows * row_bytes
    # Fast-tier budget sized to the hot partition (models DRAM scarcity).
    _libobj.objplace_set_dram_budget(int(total_bytes * hot_frac * 1.25))
    _libobj.objplace_set_pressure(ctypes.c_double(35.5))   # assume saturated CXL
    attr = ObjAttr(OBJ_EMBEDDING, total_bytes, ACC_RANDOM, SENS_BANDWIDTH,
                   hot_frac, skew_alpha, PHASE_GATHER)
    h = _libobj.obj_create(ctypes.byref(attr))
    _libobj.obj_rebalance()
    placement = _libobj.obj_placement(h)
    if placement == PLACE_SPLIT:
        hot_b = _libobj.obj_hot_bytes(h)
        cold_b = _libobj.obj_cold_bytes(h)
        hot_rows = hot_b // row_bytes
        hot = np.frombuffer(buf_from_ptr(_libobj.obj_hot_ptr(h), hot_b),
                            dtype=dtype).reshape(hot_rows, row_dim)
        cold = np.frombuffer(buf_from_ptr(_libobj.obj_cold_ptr(h), cold_b),
                             dtype=dtype).reshape(num_rows - hot_rows, row_dim)
        return None, hot, cold
    # whole-object placement (DRAM or CXL)
    raw = buf_from_ptr(_libobj.obj_hot_ptr(h), total_bytes)
    table = np.frombuffer(raw, dtype=dtype).reshape(num_rows, row_dim)
    return table, None, None


def alloc_table(num_rows, row_dim, dtype, place, hot_frac, skew_alpha=1.0):
    """Allocate the embedding table, splitting hot/cold if skew mode."""
    row_bytes = row_dim * np.dtype(dtype).itemsize
    total_bytes = num_rows * row_bytes
    if place == "objplace":
        return alloc_table_objplace(num_rows, row_dim, dtype, hot_frac, skew_alpha)
    if place not in ("skew", "skew-hint"):
        node = {"dram": 0, "cxl": 1, "interleave": "interleave"}[place]
        raw = numa_alloc(total_bytes, node)
        table = np.frombuffer(raw, dtype=dtype).reshape(num_rows, row_dim)
        return table, None, None
    # Skew: hot rows on DRAM, cold on CXL. Two separate buffers; the gather
    # routes low indices (the popular ones) to the hot buffer.
    #   skew       = manual placement via numa_alloc_onnode
    #   skew-hint  = same placement via the obj_alloc_hint prototype API
    hot_rows = max(1, int(num_rows * hot_frac))
    cold_rows = num_rows - hot_rows
    if place == "skew":
        raw_hot = numa_alloc(hot_rows * row_bytes, 0)
        raw_cold = numa_alloc(cold_rows * row_bytes, 1)
    else:  # skew-hint
        raw_hot = obj_alloc(hot_rows * row_bytes, HINT_SKEW_HOT)
        raw_cold = obj_alloc(cold_rows * row_bytes, HINT_SKEW_COLD)
    hot = np.frombuffer(raw_hot, dtype=dtype).reshape(hot_rows, row_dim)
    cold = np.frombuffer(raw_cold, dtype=dtype).reshape(cold_rows, row_dim)
    return None, hot, cold


def gen_indices(num_rows, batch, dist, zipf_s, rng):
    if dist == "uniform":
        return rng.integers(0, num_rows, size=batch, dtype=np.int64)
    if dist == "zipf":
        # Bounded Zipf over ranks 1..num_rows with P(k) ~ 1/k^alpha, sampled by
        # inverse-CDF. Supports any alpha > 0 (numpy's rng.zipf needs a>1, which
        # cannot express alpha<=1). Rank 0 = most popular = lowest index, so the
        # hot mass lands on low indices, which is where --place=skew puts DRAM rows.
        cdf = _zipf_cdf(num_rows, zipf_s)
        u = rng.random(batch)
        return np.searchsorted(cdf, u).astype(np.int64)
    raise SystemExit(f"unknown dist {dist}")


_ZIPF_CDF_CACHE = {}


def _zipf_cdf(num_rows, alpha):
    key = (num_rows, round(alpha, 4))
    cdf = _ZIPF_CDF_CACHE.get(key)
    if cdf is None:
        ranks = np.arange(1, num_rows + 1, dtype=np.float64)
        weights = 1.0 / np.power(ranks, alpha)
        cdf = np.cumsum(weights)
        cdf /= cdf[-1]
        _ZIPF_CDF_CACHE[key] = cdf
    return cdf


def main():
    p = argparse.ArgumentParser(description="Embedding / feature-store gather bench")
    p.add_argument("--rows", type=int, default=10_000_000,
                   help="number of embedding rows")
    p.add_argument("--row-dim", type=int, default=128)
    p.add_argument("--dtype", default="float16",
                   choices=["float16", "float32", "uint8"])
    p.add_argument("--batch", type=int, default=4096,
                   help="rows gathered per step")
    p.add_argument("--steps", type=int, default=200)
    p.add_argument("--dist", default="uniform", choices=["uniform", "zipf"])
    p.add_argument("--zipf-s", type=float, default=1.2)
    p.add_argument("--place", default="dram",
                   choices=["dram", "cxl", "interleave", "skew", "skew-hint",
                            "objplace"])
    p.add_argument("--hot-frac", type=float, default=0.1,
                   help="fraction of rows kept hot when --place=skew")
    p.add_argument("--tag", default="run")
    p.add_argument("--csv", action="store_true")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    dtype = np.dtype(args.dtype)
    row_bytes = args.row_dim * dtype.itemsize
    total_bytes = args.rows * row_bytes
    print(f"embbench: rows={args.rows} dim={args.row_dim} dtype={args.dtype} "
          f"batch={args.batch} dist={args.dist} place={args.place} "
          f"row_bytes={row_bytes} total={total_bytes/2**30:.2f} GiB",
          file=sys.stderr)

    table, hot, cold = alloc_table(args.rows, args.row_dim, dtype,
                                   args.place, args.hot_frac, args.zipf_s)
    # Pre-touch the WHOLE table so gathers hit warm pages, not page faults.
    if table is not None:
        table[...] = 0
    else:
        hot[...] = 0
        cold[...] = 0

    rng = np.random.default_rng(args.seed)
    # Warmup
    for _ in range(3):
        idx = gen_indices(args.rows, args.batch, args.dist, args.zipf_s, rng)
        if table is not None:
            _ = table[idx].sum()
        else:
            hot_rows = hot.shape[0]
            in_hot = idx < hot_rows
            _ = (hot[idx[in_hot]].sum()
                 + cold[idx[~in_hot] - hot_rows].sum())

    t0 = time.perf_counter()
    bytes_total = 0
    for s in range(args.steps):
        idx = gen_indices(args.rows, args.batch, args.dist, args.zipf_s, rng)
        if table is not None:
            out = table[idx]
            bytes_total += out.nbytes
            _ = out.sum()
        else:
            hot_rows = hot.shape[0]
            in_hot = idx < hot_rows
            h = hot[idx[in_hot]]
            c = cold[idx[~in_hot] - hot_rows]
            bytes_total += h.nbytes + c.nbytes
            _ = h.sum() + c.sum()
    t1 = time.perf_counter()

    elapsed = t1 - t0
    per_step_ms = (elapsed / args.steps) * 1000.0
    bw_gibs = (bytes_total / elapsed) / (1 << 30)
    rows_per_sec = (args.batch * args.steps) / elapsed

    if args.csv:
        if args.tag.startswith("header:"):
            print("tag,place,dist,rows,row_dim,batch,steps,dtype,"
                  "elapsed_sec,per_step_ms,bandwidth_gib_s,rows_per_sec")
        print(f"{args.tag},{args.place},{args.dist},{args.rows},{args.row_dim},"
              f"{args.batch},{args.steps},{args.dtype},"
              f"{elapsed:.4f},{per_step_ms:.3f},{bw_gibs:.3f},{rows_per_sec:.1f}")
    else:
        print(f"  steps          = {args.steps}")
        print(f"  elapsed        = {elapsed:.3f} s")
        print(f"  per_step       = {per_step_ms:.2f} ms")
        print(f"  bandwidth      = {bw_gibs:.3f} GiB/s")
        print(f"  rows/sec       = {rows_per_sec:.0f}")


if __name__ == "__main__":
    main()
