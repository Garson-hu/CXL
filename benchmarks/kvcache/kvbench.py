#!/usr/bin/env python3
"""
kvbench — KV-cache-shape memory benchmark.

Models the *memory access pattern* of LLM decode-time KV access without
running a real LLM. Useful when GPU VRAM is small (1x 4060 Ti 8 GB on c28)
but we still want to study how CXL placement affects KV traffic.

Layout per request:
    KV cache shape = [n_layers, 2, n_heads, seq_len, head_dim] of dtype
    The benchmark allocates this for each concurrent request.

Decode access pattern:
    For each generated token:
      for each layer:
        for each request in the active batch:
          read K[layer, head, 0..seq_len, head_dim]   # attention dot-product
          read V[layer, head, 0..seq_len, head_dim]
          write K[layer, head, seq_len, head_dim]     # append new token
          write V[layer, head, seq_len, head_dim]

Placement modes:
    --place=dram         all KV on NUMA node 0
    --place=cxl          all KV on NUMA node 1
    --place=interleave   striped across nodes 0 and 1
    --place=split        per-layer split: layers [0..K) on DRAM, [K..L) on CXL

Output is CSV to stdout.

Requirements: numpy, optionally numactl on the command line for binding.

Note: this benchmark uses numpy + posix shm-style buffers. NUMA binding is
provided by running the script under `numactl --membind=...` OR by passing
--place which uses libnuma via ctypes when available. We prefer the external
numactl approach for reproducibility.
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
# Keep numa-allocated regions alive for the life of the process.
_NUMA_KEEPALIVE = []


def numa_alloc(size_bytes, node):
    """Allocate a numpy buffer backed by a NUMA-pinned region."""
    if _libnuma is None or _libnuma.numa_available() < 0:
        # Fall back to plain numpy allocation; honors numactl from caller.
        return np.zeros(size_bytes, dtype=np.uint8)
    if node == "interleave":
        ptr = _libnuma.numa_alloc_interleaved(size_bytes)
    else:
        node_int = int(node)
        sz = _libnuma.numa_node_size64(node_int, None)
        if sz <= 0:
            print(f"kvbench: NUMA node {node_int} has 0 MB online memory.",
                  file=sys.stderr)
            print("  If this is the CXL node on c28 (likely node 1), an admin",
                  file=sys.stderr)
            print("  still needs to run: sudo daxctl online-memory dax2.0",
                  file=sys.stderr)
            sys.exit(4)
        ptr = _libnuma.numa_alloc_onnode(size_bytes, node_int)
    if not ptr:
        print(f"kvbench: numa_alloc failed for node={node}", file=sys.stderr)
        sys.exit(5)
    # Keep the raw pointer alive; wrap as a numpy uint8 view.
    buf = (ctypes.c_uint8 * size_bytes).from_address(ptr)
    arr = np.frombuffer(buf, dtype=np.uint8)
    _NUMA_KEEPALIVE.append((ptr, size_bytes, buf))
    return arr


def build_layer_buffers(args, dtype):
    """
    Build [n_layers] of K and V buffers shaped [n_heads, seq_len, head_dim],
    placed according to args.place.
    """
    layer_bytes = (
        2 * args.heads * args.seq_len * args.head_dim * np.dtype(dtype).itemsize
    )
    layers = []
    for li in range(args.layers):
        if args.place == "dram":
            node = 0
        elif args.place == "cxl":
            node = 1
        elif args.place == "interleave":
            node = "interleave"
        elif args.place == "split":
            node = 0 if li < args.split_at else 1
        else:
            print(f"kvbench: unknown place '{args.place}'", file=sys.stderr)
            sys.exit(2)
        raw = numa_alloc(layer_bytes, node)
        # Reshape to [K|V, heads, seq_len, head_dim]
        view = np.frombuffer(raw, dtype=dtype).reshape(
            2, args.heads, args.seq_len, args.head_dim
        )
        layers.append(view)
    return layers


def decode_step(layers, args, tok_idx, batch_size, dst_buf):
    """
    One decode step: for each layer, do dot-product-style reads across the
    full prefix and append a new token. We only model traffic, not math.
    """
    bytes_touched = 0
    for layer in layers:
        K = layer[0]  # [heads, seq, dim]
        V = layer[1]
        # Read full prefix across heads. We use np.sum to force memory traffic.
        for b in range(batch_size):
            # Simulate that each request touches its own slice;
            # in this synthetic benchmark all requests share the same buffer.
            # Accumulate in float64 to force a full read without fp16 overflow.
            s = (K[:, : tok_idx + 1, :].sum(dtype=np.float64)
                 + V[:, : tok_idx + 1, :].sum(dtype=np.float64))
            dst_buf[0] = int(s) & 0xFF
            bytes_touched += 2 * K[:, : tok_idx + 1, :].nbytes
        # Append new token (write).
        if tok_idx + 1 < args.seq_len:
            K[:, tok_idx + 1, :] = tok_idx
            V[:, tok_idx + 1, :] = tok_idx
            bytes_touched += 2 * K[:, tok_idx + 1, :].nbytes
    return bytes_touched


def main():
    p = argparse.ArgumentParser(description="KV-cache-shape benchmark")
    p.add_argument("--layers", type=int, default=32)
    p.add_argument("--heads", type=int, default=32)
    p.add_argument("--head-dim", type=int, default=128)
    p.add_argument("--seq-len", type=int, default=2048)
    p.add_argument("--batch", type=int, default=1)
    p.add_argument("--tokens", type=int, default=64,
                   help="number of decode steps to simulate")
    p.add_argument("--dtype", default="float16",
                   choices=["float16", "bfloat16", "float32"])
    p.add_argument("--place", default="dram",
                   choices=["dram", "cxl", "interleave", "split"])
    p.add_argument("--split-at", type=int, default=16,
                   help="when --place=split, layers <split-at are on DRAM, rest on CXL")
    p.add_argument("--tag", default="run")
    p.add_argument("--csv", action="store_true")
    p.add_argument("--warmup", type=int, default=4)
    args = p.parse_args()

    if args.dtype == "bfloat16":
        # numpy lacks native bf16 in some versions; emulate with float16.
        dtype = np.float16
    else:
        dtype = np.dtype(args.dtype)

    layer_bytes = 2 * args.heads * args.seq_len * args.head_dim * dtype.itemsize
    total_bytes = layer_bytes * args.layers
    print(f"kvbench: layers={args.layers} heads={args.heads} "
          f"head_dim={args.head_dim} seq={args.seq_len} batch={args.batch} "
          f"dtype={args.dtype} place={args.place} "
          f"per_layer={layer_bytes/2**20:.1f} MiB "
          f"total={total_bytes/2**30:.2f} GiB",
          file=sys.stderr)

    layers = build_layer_buffers(args, dtype)
    # Pre-touch all buffers so paging is out of the timing.
    for li in layers:
        li[...] = 0
    dst = np.zeros(1, dtype=np.uint64)

    # Warmup
    for t in range(args.warmup):
        decode_step(layers, args, t, args.batch, dst)

    t0 = time.perf_counter()
    bytes_total = 0
    for t in range(args.warmup, args.warmup + args.tokens):
        bytes_total += decode_step(layers, args, t, args.batch, dst)
    t1 = time.perf_counter()

    elapsed = t1 - t0
    per_token_ms = (elapsed / args.tokens) * 1000.0
    bw_gibs = (bytes_total / elapsed) / (1 << 30)

    if args.csv:
        if args.tag.startswith("header:"):
            print("tag,place,layers,heads,head_dim,seq_len,batch,tokens,dtype,"
                  "elapsed_sec,per_token_ms,bandwidth_gib_s")
        print(f"{args.tag},{args.place},{args.layers},{args.heads},"
              f"{args.head_dim},{args.seq_len},{args.batch},{args.tokens},"
              f"{args.dtype},{elapsed:.4f},{per_token_ms:.3f},{bw_gibs:.3f}")
    else:
        print(f"  tokens         = {args.tokens}")
        print(f"  elapsed        = {elapsed:.3f} s")
        print(f"  per_token      = {per_token_ms:.2f} ms")
        print(f"  bytes_touched  = {bytes_total:.3e}")
        print(f"  bandwidth      = {bw_gibs:.3f} GiB/s")


if __name__ == "__main__":
    main()
