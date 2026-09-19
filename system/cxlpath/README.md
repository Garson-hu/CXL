# cxlpath — write-path runtime for DRAM + CXL (+ NVMe)

Design, as-built notes and the list of design changes: `docs/DESIGN.md` §10.
Build record with every gate result: `docs/experiments/2026-09-08-write-tier-campaign.md`, "Phase 5 v2".
No root is needed anywhere.

## Build

    make            # libcxlpath.a, libcxlpath.so (bindings), cxlpathd, tests, tools; GPU parts if /usr/local/cuda exists
    make test       # unit tests on sparse files in /dev/shm + strace check of the data path
    make test-dax   # same tests on the first 8 GiB of /dev/dax0.0 and /dev/dax1.0 (the tests OWN that range)

## Quick start

    build/cxlp_mkstore demo 16384 4096 /dev/dax0.0 /dev/dax1.0   # 16 GiB of each dax device + a 4 GiB DRAM pool
    build/cxlpathd demo --cpu 16 --log /dev/shm/demo.csv &       # probe on cpu 16; everything else stays off that CCD
    build/cxlp_admin demo view                                   # published policy, free segments, bytes written
    build/cxlp_writers demo 4 112 5                              # 4 writer threads on cpus 112.., 5 s
    build/cxlp_admin demo destroy

A store is a name: metadata in `/dev/shm/cxlpath.<name>`, a range of each dax device that the store owns,
and a tmpfs file as DRAM pool. Small objects (KiB–few MiB) need a larger object table:
`CXLP_OBJ_SLOTS=65536 build/cxlp_mkstore ...`.

## Pieces

| path | what |
|---|---|
| `include/cxlpath.h` | client API: reservations, objects, read path, buffer sets, streams, drain targets |
| `src/store.c reserve.c object.c bufset.c` | Component A: segment store on raw devdax, shared index, crash cleanup |
| `src/policy.c probe.c controller.c`, `daemon/cxlpathd.c` | Component B: published spill ratio, DRAM latency probe, slow-increase / fast-decrease |
| `src/gpu/gpu.c`, `include/cxlpath_gpu.h` | GPU sources: direct vs staged path per 32 MiB chunk |
| `src/readpath.c` | Component C: pin/unpin, read counts, break-even promotion |
| `src/drain.c` | Component D: O_DIRECT drain straight from CXL, pacing, version chains |
| `src/stream.c` | file-style shim (packed 32 MiB extents) |
| `clients/veloc/` | VeloC client patch (`VELOC_CXLPATH_STORE=<store>`) + byte-exact round-trip helper |
| `clients/pytorch/cxlpath_dcp.py` | `CxlpathWriter` / `CxlpathReader` for `torch.distributed.checkpoint` (`async_save`) |
| `tests/live/` | gates that need the real machine, quiet: `b_live.py b5_live.py c_live.py d_live.py e1_veloc.sh e3_kv.sh f1_all.sh` |
| `checks/` | the feasibility checks V1–V6 that preceded the build |

## Conventions

- Only `/dev/dax0.0` and `/dev/dax1.0`. A program that writes to a dax device owns its range or restores it.
- CPU layout used by the live gates on c28: probe cpu 16 (CCD1), cxlpath writers cpus 112.. (CCD7),
  DRAM aggressor cpus 32.. (CCD2–5), GPU copy thread cpu 100.
- Stop a daemon with `kill -TERM <pid>`; do not `pkill -f` with a pattern that matches your own shell.
- Gate numbers decide pass/fail of a build step. They are not evaluation results.
