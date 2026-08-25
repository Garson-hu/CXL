# CLAUDE.md

Instructions to Claude for working in this repo.

## What this repo is
CXL + LLM systems research project. Target: top systems venue (OSDI, ASPLOS, SOSP, FAST). Currently in **Week 1** — hardware verification on c28, no system code yet. Primary inspiration: Memstrata (OSDI'24).

## Layout
- `hardware/scripts/` — measurement scripts for c28 (bash). Run as `./script.sh` on the node after `salloc`.
- `hardware/results/` — raw measurement output, **append-only**, dated filenames (`YYYY-MM-DD-<what>.log`). Never edit past results.
- `experiments/baselines/` — KV-cache placement comparisons (DRAM / CXL-pinned / interleaved).
- `experiments/system/` — experiment harnesses for the built system (empty until direction is locked).
- `system/` — the built system source (empty until direction is locked).
- `workloads/` — trace configs (LMSys-Chat-1M, ShareGPT, BurstGPT, Azure LLM Inference Traces).
- `scripts/` — generic utility scripts.

Do not recreate `notes/`, `papers/`, or `writing/` — the user deleted these deliberately. Planning and design context live in conversation + memory, not in the repo.

## Accessing hardware
The dev environment **is already on c28** — `hostname` returns `c28`, no `ssh`/`salloc` needed from here. If working from a separate login: `ssh arc.csc.ncsu.edu` then `salloc -p turin128 -w c28 -t 04:00:00`.

Backup GPU nodes (no CXL): c29 (`-p h100`, H100 NVL 94 GB), c33 (`-p a100`, A100 80 GB), c30–31 (`-p a6000`, 4× A6000 48 GB), `-p rtx4060ti16g` pool. c28's local GPU is only **1× RTX 4060 Ti 8 GB** — small VRAM, use backup nodes for anything > 7B.

## CXL is not online by default
Kernel boots with `memhp_default_state=offline`. The 4× CZ120 are exposed as **devdax** only (`dax0.0`/`dax1.0`/`dax2.0`, ~1.06 TiB total, `target_node 1`) — not as a NUMA node. Before `numactl --membind` / MLC / Memstrata-style tiering works, bring CXL online as system-ram (needs root):
```
sudo daxctl reconfigure-device --mode=system-ram --no-online dax0.0 dax1.0 dax2.0
sudo daxctl online-memory dax0.0 dax1.0 dax2.0
numactl --hardware   # should now show a new node for CXL
```
User `ghu4` has no passwordless sudo as of 2026-04-18; admin help required.

## MLC is not installed
Intel MLC must be fetched manually (EULA-gated): https://www.intel.com/content/www/us/en/download/736633/intel-memory-latency-checker-intel-mlc.html → `tar xf` to `~/mlc/Linux` → add to PATH. `hardware/scripts/setup-mlc.sh` checks for it.

## Running the Week 1 measurements
On c28, in order:
1. `hardware/scripts/inspect-system.sh > hardware/results/$(date +%F)-inspect.log`
2. Read inspect output for CXL NUMA node IDs, then:
   `hardware/scripts/mlc-sweep.sh <DRAM_NODE> <CXL_NODE_1> [CXL_NODE_2 ...] > hardware/results/$(date +%F)-mlc.log`
3. Edit `CXL_NODES`, `DRAM_NODE`, `MODEL` at the top of `hardware/scripts/llm-baselines.sh`, then run it. Add a benchmark client for TTFT/TBT/throughput — the script currently has TODO markers.

## Conventions
- **Raw data is sacred.** `hardware/results/*.log` files are never edited; append new dated files.
- **Absolute dates only** in any written artifact (WORKLOG, memory). "2026-04-18", not "today" / "last week".
- **Lean repo.** If it's planning or decision context, it goes in memory or WORKLOG, not as a new markdown file in the repo.

## Docs / memory management

Three layers:

1. **Per-project memory** at `~/.claude/projects/-home-ghu4-CXL/memory/` — `MEMORY.md` index + `<type>_<topic>.md` files (types: `user`, `feedback`, `project`, `reference`). Each file has YAML frontmatter with `name` / `description` / `type`. Project and feedback memories include `**Why:**` and `**How to apply:**` lines.
2. **WORKLOG.md** at repo root — append-only session history. "Current Status" at top; reverse-chronological session entries below.
3. **CLAUDE.md** (this file) — codebase rules. Update only when layout / build / run / access changes.

End-of-session ritual: run `/update-mem` to refresh memory and WORKLOG. Skill definition at `.claude/skills/update-mem/SKILL.md`.

**Docs policy (reorganized 2026-08-25 — full rules in `docs/README.md`).** WORKLOG.md is the primary progress tracker; every meaningful update goes there. `docs/` structure:
- **Living docs** (only two): `PAPER.md` (thesis + claims + positioning) and `DESIGN.md` (current system design + API). Both END with an append-only `## Change history` section — edit the body to reflect the present, append one dated line per change, NEVER rewrite/delete history entries.
- **`experiments/`**: one file per experiment named `YYYY-MM-DD-<content>.md` (question, setup, commands, numbers, verdict). ONE active file at a time; when its verdict lands in `experiments/INDEX.md` the file is FROZEN (corrections = new dated file). Shared invariants: `experiments/METHODOLOGY.md` (append-only).
- **`guides/`** (onboarding walkthroughs), **`slides/`** (dated decks, never edit past ones), **`archive/`** (superseded docs, verbatim, never edited).
- Precision rule: every number carries units/threads/node/date and links its raw log. Do NOT create new top-level docs; new material is an experiment file, a Change-history-tracked edit, or WORKLOG. Literature: `Related.md` (repo root).
**Process rule (2026-08-25):** for any multi-step action (reorganizations, doc rewrites, code changes, experiment campaigns), present the plan and get the user's explicit agreement BEFORE executing.

## Venue candidates
OSDI'27 (~Dec 2026), ASPLOS'27 summer (~Dec 2026), SOSP'27 (~Apr 2027), FAST'28 (~Sep 2026). Already passed: OSDI'26, ASPLOS'26 spring/summer, SOSP'26.
