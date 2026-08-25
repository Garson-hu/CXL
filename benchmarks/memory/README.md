# membench — DRAM vs CXL memory benchmark

Minimal C benchmark for c28. No MLC required.

## Build

```
make
```

Requires libnuma headers (`numa.h`). On c28, libnuma is already installed.

## Modes

| Mode | What it measures |
|---|---|
| `latency` | pointer-chase idle latency (ns/access) |
| `stream-read` | sequential read bandwidth (GiB/s) |
| `stream-write` | sequential write bandwidth (GiB/s) |
| `random-read` | random 64-byte gather bandwidth (GiB/s) |
| `mixed` | configurable read/write ratio bandwidth |
| `loaded-latency` | thread 0 measures pointer-chase latency while N−1 threads stream-read (saturate node) |

## Usage

```
./membench --node=N --mode=MODE [--size=BYTES] [--threads=T] [--rw=PCT_READ]
           [--duration=SEC] [--tag=NAME] [--csv]
```

Examples:

```
# DRAM idle latency
./membench --node=0 --mode=latency --size=$((1<<30)) --duration=5

# CXL idle latency (only works once node 1 is online)
./membench --node=1 --mode=latency --size=$((1<<30)) --duration=5

# DRAM stream read with 32 threads
./membench --node=0 --mode=stream-read --threads=32 --size=$((512<<20))

# Loaded latency on DRAM
./membench --node=0 --mode=loaded-latency --threads=16 --size=$((256<<20))

# CSV mode (one row per run, header on first call with --tag=header:...)
./membench --node=0 --mode=latency --csv --tag=header:hdr
./membench --node=0 --mode=stream-read --threads=8 --csv --tag=dram-r8
```

## Error behavior

- If `--node=N` is out of range → exit 3.
- If the chosen node has 0 MB online memory → exit 4 with the exact c28 unblock command:
  ```
  sudo daxctl online-memory dax2.0
  ```
  No fake numbers ever printed for unavailable nodes.

## Notes

- Threads are pinned to CPUs on node 0 (the CPU-bearing node on c28). Memory is
  bound to `--node`. This mirrors how real workloads use CXL: CPUs on the local
  socket, memory partly on remote CXL.
- Pointer-chase buffer is shuffled with a Fisher-Yates pass; access pattern is
  truly random within the buffer, so latency is not hidden by stride prefetchers.
- Buffers are pre-touched (`memset 0`) before timing so page faults are excluded.
