# 2026-09-22 — Phase 2 re-run with a data-carrying snapshot: three simple policies vs cxlpath beside seven victims

**STATUS: ACTIVE (campaign launched 2026-09-22 20:05 EDT, ~8 h; repetitions interleaved).** Replaces the numbers of
[2026-09-22-three-policies.md](2026-09-22-three-policies.md) and of items 1–2 of
[2026-09-22-moderate-pacing-dcp.md](2026-09-22-moderate-pacing-dcp.md), whose C producer copied a 98%-zero
snapshot ([2026-09-22-zero-line-writes.md](2026-09-22-zero-line-writes.md)). Raw:
`experimental_results/2026-09-22-three-policies-realdata/`. Tools: `benchmarks/policy/` (`ckpt_producer.c` now
fills its snapshot with xorshift pseudo-random data on the producer's 8 cpus; driver `run_policy.py`; the
daemon's default guard is 1.3 since this campaign, so tags carry no `-g`).

## Question
Same as the superseded file: a periodic checkpoint copy (64 GiB every 25 s; PageRank: 192 GiB every 30 s)
beside a DRAM-bound victim — where do all-DRAM (NT / plain), all-CXL, a throttled DRAM writer and cxlpath land
on the two axes (victim slowdown during the copy; completion time) — now with a snapshot whose every cache
line carries data. Victims: the synthetic reader (8 threads), CPU Adam / llama.cpp / PageRank on 80 threads
(saturated), and the same three on 32 threads (moderate). cxlpath bounds as before (reader 1.09 / 1.15; Adam
1.04 / 1.10; llama.cpp 1.06 / 1.10; PageRank 1.055 / 1.10; 32-thread victims 1.09 / 1.05), pacing on.

## Results
(to be filled as repetitions complete; per-run lines in `summary.csv`)

## Verdict
(pending)
