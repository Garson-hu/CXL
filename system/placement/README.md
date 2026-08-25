# obj_placement — minimal sensitivity-aware CXL placement prototype

Status: **minimal prototype** (locked direction 2026-05-20). Not a general
allocator — just the API surface + placement mapping motivated by measurement.

## API

```c
void *obj_alloc_hint(size_t size, obj_hint_t hint);
void  obj_free_hint(void *ptr, size_t size);
```

Hints → NUMA node mapping:

| hint | meaning | node |
|---|---|---|
| `HINT_BW_SENSITIVE` | bandwidth-bound / latency-sensitive | DRAM |
| `HINT_COLD_CAPACITY` | cold, capacity, latency-tolerant | CXL |
| `HINT_SKEW_HOT` | hot subset of a skewed structure | DRAM |
| `HINT_SKEW_COLD` | cold tail of a skewed structure | CXL |

Defaults DRAM=node 0, CXL=node 1 (c28). Override via `obj_placement_init()` or
env `OBJ_DRAM_NODE` / `OBJ_CXL_NODE`. If the CXL node has no online memory, CXL
hints fall back to DRAM with one warning.

## Why this mapping (measurement-grounded)

See `docs/DIRECTION_DECISION.md` (locked thesis) and the phase docs:
- Bandwidth-bound tenants on CXL suffer **>2×** interference from co-tenants
  (Phase 2.2 / confirm); DRAM does not → keep BW-sensitive objects on DRAM.
- Skew-aware split (hot→DRAM) beats interleave by **~15%** on embedding
  (confirm, median-of-5) → SKEW_HOT on DRAM, SKEW_COLD on CXL.

## Build / test

```
make          # builds test_placement
make test     # runs it; verifies each hint lands on the intended node via move_pages
```

## Explicitly out of scope (for now)

- No automatic hot/cold detection — the caller supplies the hint.
- No migration / promotion / demotion.
- No KV-cache integration — KV needs a request/recency-skew model first
  (Phase 3 showed split-by-layer ≈ interleave for KV).
- No multi-CXL-device awareness — single system-ram device measured so far.
