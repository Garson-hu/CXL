# System Design (current)

*The one document that always describes the system as it exists now.
History: `## Change history` at the bottom (append-only). Predecessor file:
`archive/DESIGN_OBJPLACE.md` (2026-05-20 original, verbatim).*

**Status 2026-08-25:** ObjPlace v1 (below) is built and evaluated
(`experiments/2026-05-19-baseline-objplace.md`). The per-direction extension
(§7) is DESIGNED-ONLY, gated on the experiments in
`experiments/2026-08-25-direction-gates.md`.

## 1. What ObjPlace is
Object-level semantic placement, not a `numa_alloc_onnode` wrapper: the
application registers each memory object with its *type, access pattern,
sensitivity, hot fraction, skew, phase*; a benefit-guided planner decides
DRAM / CXL / SPLIT under a model of CXL bandwidth pressure. Rationale: the two
signals that decide CXL placement value — **bandwidth-sensitivity** and **access
skew** — are known to the application and invisible to page-grain hotness
tracking (a bandwidth-bound object loses 2.0–2.13× under a CXL co-tenant; a
latency-bound one ≤1.23×; same hotness, different placement value).

## 2. Object registry
Per-object metadata (in-process array, no kernel involvement):
`id` · `size` · `type` {generic, embedding, feature, kv, buffer} ·
`access` {streaming, random, mixed} · `sensitivity` {bandwidth, latency,
capacity} · `hot_fraction` 0..1 · `skew_alpha` ≥0 · `phase` {active, inactive,
prefill, decode, gather} · `placement` (planner output).

## 3. CXL pressure model (v1 — single ceiling)
```
CXL_BW_CEILING_GIB = 35.5          // measured pair ceiling, May 2026
pressure_factor    = clamp(cxl_load / ceiling, 0, 1.2)   // load supplied via
objplace_set_pressure(); default = saturated (conservative)
```
Known v1 limitation: ONE number models the tier; read and write traffic are not
distinguished. Replaced by §7 once gates pass.

## 4. Benefit-guided planner
Per candidate (whole object, or hot/cold partition of a skewed object):
```
cxl_penalty = 1 + base_penalty(access) * pressure_factor
              base: streaming 1.10, mixed 0.60, random 0.25
sens_mult   = bandwidth 1.0, latency 0.5, capacity 0.1
phase_mult  = active/prefill/decode/gather 1.0, inactive 0.1
density     = access_share / partition_fraction,
              access_share = hot_fraction ^ (1 / (1 + skew_alpha))
benefit_per_byte = sens_mult * phase_mult * (cxl_penalty - 1) * density
```
Greedy 0/1-knapsack: sort candidates by benefit-per-byte, fill the DRAM budget,
rest to CXL; partition decisions fold back to DRAM/CXL/SPLIT. This beats
hotness-only exactly where sensitivity separates equally-hot objects (+118%
measured).

## 5. Lifecycle (no migration)
`obj_create` registers + plans (no allocation) → `obj_rebalance()` global
re-plan of unmaterialized objects → `obj_ptr` / `obj_hot_ptr` / `obj_cold_ptr`
materialize on first call (one `numa_alloc_onnode` per partition), placement
then fixed. `obj_update_phase` / `obj_update_hotset` mutate metadata for the
next re-plan. Typical flow: create-all → rebalance → materialize → run.

## 6. Scope guard + known limitations (v1, from evaluation)
No automatic hot/cold detection; no page migration; no kernel module; no KV
claim; no multi-device policy. Planner has no INTERLEAVE candidate (uniform
bandwidth objects over budget go all-CXL: GNN-uniform −11.6%). Tight budgets
(0–1 objects fit) are degenerate. Pressure is supplied, not sensed.

## 7. PLANNED extension — per-direction budgets (pending gates, 2026-08-25)
Motivation and evidence: `PAPER.md` Thesis v2. Design intent, to be finalized
after Gates 1–2:
- **Two budgets per tier** replace the single ceiling: `(read_bw, write_bw)`.
  DRAM charges an app-level write **2×** (RFO + writeback, measured exact);
  CXL charges it against the write budget only (duplex link).
- **`dir` attribute** on objects: `READ_STREAM / WRITE_STREAM / RMW` — the
  planner's benefit term keys on direction × per-tier direction cost.
- **Staging API:** `obj_stage_out(h)` / `obj_stage_in(h)` — NT-store bulk copy
  DRAM↔CXL off the critical path (checkpoint/eviction verb; NT stores skip RFO).
- **LLM extension points (interfaces only):** object-class presets
  `KV_EVICT`, `PREFIX_INSERT`, `OPT_STATE` over `dir`; promote-on-hit hook.
  Explicit non-goal now: active-decode KV on CXL (read-latency trap).

## 8. Positioning caveat (unchanged, binding)
"Object-level sensitivity-aware tiering" is NOT net-new (SoarAlto OSDI'25,
X-Mem, Colloid SOSP'24 own neighboring claims). Deltas we may claim: online
hint-driven placement + CXL bandwidth-pressure arbitration + real CZ120; after
the pivot, **traffic direction as the placement signal**. Never claim "first
object-level tiering" / "first hotness-insufficiency"; cite SoarAlto, Memstrata,
Colloid explicitly. Verify Clove + VLDB'25 before claiming the direction delta.

## 9. API reference (v1, header `system/placement/objplace.h`)
Enums: `obj_type_t` {GENERIC, EMBEDDING, FEATURE, KV, BUFFER}; `access_pattern_t`
{STREAMING, RANDOM, MIXED}; `sensitivity_t` {BANDWIDTH, LATENCY, CAPACITY};
`phase_t` {ACTIVE, INACTIVE, PREFILL, DECODE, GATHER}; `placement_t` {DRAM, CXL,
SPLIT, INTERLEAVE}.
Config: `objplace_init(dram_node, cxl_node)` (env `OBJ_DRAM_NODE`/`OBJ_CXL_NODE`)
· `objplace_set_dram_budget(bytes)` (default 2 GiB; env `OBJPLACE_DRAM_BUDGET`)
· `objplace_set_pressure(load_gib_s)`.
Lifecycle: `obj_create(attr)` · `obj_rebalance()` · `obj_update_phase` ·
`obj_update_hotset` · `obj_destroy`.
Access: `obj_ptr` (NULL if SPLIT) · `obj_hot_ptr`/`obj_cold_ptr` ·
`obj_hot_bytes`/`obj_cold_bytes`.
Introspection: `obj_placement` · `obj_benefit_per_byte` · `placement_name` ·
`objplace_record_bytes` · `objplace_live_count`.
Legacy wrapper: `obj_alloc_hint(size, hint)` {BW_SENSITIVE, COLD_CAPACITY,
SKEW_HOT, SKEW_COLD} (forces a tier, bypasses budget) · `obj_free_hint`.
Python: ctypes bridge, `ObjAttr` mirrors `obj_attr_t`
(`benchmarks/embbench.py:alloc_table_objplace`).

## Change history (append-only — never rewrite entries)
- **2026-05-20** — v1 designed and built: object registry, single-ceiling
  pressure model, benefit-per-byte greedy planner, lazy materialization, no
  migration. Evaluated same week (=manual ±1%, +14.3% vs interleave, +118% vs
  hotness-only, ~0.2% overhead). Original file: `archive/DESIGN_OBJPLACE.md`.
- **2026-08-25** — pivot to direction-aware placement (advisor-aligned): §7
  planned — per-direction budgets (DRAM write ×2, CXL duplex), `dir` attribute,
  NT staging API, LLM extension points as interfaces only. Build gated on
  `experiments/2026-08-25-direction-gates.md`. §3 marked v1-limited. Docs
  reorganized (this file created from `DESIGN_OBJPLACE.md`).
