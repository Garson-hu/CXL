# Research progress deck 2026-10-13 — outline

Title: Interference-Aware Data Management with DRAM and CXL Memory — Research Progress and Experimental Findings

| # | slide | part | evidence | figure |
|---|---|---|---|---|
| 1 | Interference-Aware Data Management with DRAM and CXL Memory | — |  | — |
| 2 | Bulk writes into DRAM stall every DRAM reader; the same writes into CXL do not | Part I · Original research idea | Hardware measurement | f01_drain_cliff |
| 3 | Original design: write to CXL by default, borrow DRAM only with measured headroom | Part I · Original research idea | System built 2026-09-19 | f03_arch_original |
| 4 | First results: the loan works beside moderate victims; beside saturated ones the guard lends nothing | Part I · Original research idea | Real application | f02_original_core |
| 5 | The advisor's suggestion: manage DRAM and CXL as one pool with exclusive placement | Part II · Advisor's suggestion | Proposal (not implemented) | f04_unified_pool |
| 6 | Why unified management may matter: capacity and write bandwidth are two separate budgets | Part II · Advisor's suggestion | Analysis, Trace simulation | f21_two_resources |
| 7 | CXL writes spare a DRAM reader only from an unrelated core group | Part III · Hardware characterization | Hardware measurement | f05_topology |
| 8 | CXL readers lose 36–40% to CXL writes from anywhere; a dependent read takes 2.4× longer | Part III · Hardware characterization | Hardware measurement | f06_cxl_reader |
| 9 | Throttling DRAM does not protect neighbours, and persistent memory is not a substitute for CXL | Part III · Hardware characterization | Trace-driven emulation, Hardware measurement | f07_throttle_optane |
| 10 | Real KV serving on the RTX 4060 Ti writes ~0.1 GB/s in short bursts and disturbs nobody | Part IV · KV cache characterization | Real application | f08_real_kv |
| 11 | Host memory traffic emulation reproduces server-scale KV traffic from the traces | Part IV · KV cache characterization | Trace-driven emulation | f22_emulation_method |
| 12 | Server-scale KV writes into DRAM slow neighbours up to 63%; into CXL, at most 2% | Part IV · KV cache characterization | Trace-driven emulation | f10_emulation_neighbors |
| 13 | CXL protects readers but takes at most ~46 GB/s; heavier loads fall behind | Part IV · KV cache characterization | Trace-driven emulation | f09_emulation_rate |
| 14 | The host KV cache is capacity-bound; DRAM holding other blocks adds +3 to +15 points of hits | Part V · Capacity and memory management | Trace simulation, Estimate | f11_kv_capacity |
| 15 | Real LMCache: DRAM, DRAM-first hybrid and CXL-only L1 serve the same hits and TTFT on this GPU | Part V · Capacity and memory management | Real application | f12_real_lmcache |
| 16 | At equal capacity, static admission beats our migration policies; CXL-first alone idles a fifth of the hits | Part V · Capacity and memory management | Trace-driven emulation | f13_admission_migration |
| 17 | The current controller reads a DRAM-heavy neighbour as 'no headroom' and lends nothing | Part VI · Budget-gated admission | Trace-driven emulation | f14_controller_limit |
| 18 | Budget-gated admission: a token bucket decides, block by block, whether a new block may use DRAM | Part VI · Budget-gated admission | Emulated policy, Proposal (not implemented) | f15_budget_design |
| 19 | Calibration: smoother DRAM writes buy SLO room, but a one-block bucket caps DRAM's share at ~25% | Part VI · Budget-gated admission | Trace-driven emulation | f16_bga_calibration |
| 20 | Evaluation under the same 7% SLO: budget-gated admission ties the best safe split; both beat the controller | Part VI · Budget-gated admission | Trace-driven emulation | f17_bga_evaluation |
| 21 | A deeper bucket uses the budget fully, but on the evaluation segment it earns no extra hits | Part VI · Budget-gated admission | Trace-driven emulation | f18_bga_depth |
| 22 | Adapting the budget to the neighbour drains the backlog; 70B 4× next to Adam stays marginal | Part VI · Budget-gated admission | Trace-driven emulation | f19_bga_varying |
| 23 | Checkpoint writes and KV reads on the same CXL cards: KV priority protects loads, not the shared write pipe | Part VII · Mixed applications | Real application, Trace-driven emulation | f20_ckpt_kv |
| 24 | What we have learned | Part VIII · Current conclusions | Summary | — |
| 25 | Proposed direction: interference-aware capacity and bandwidth management for DRAM/CXL memory | Part VIII · Current conclusions | Proposal (not implemented) | f23_direction |
| 26 | Next steps and open questions | Part VIII · Current conclusions | Proposal (not implemented) | — |

Each content slide: one conclusion-style title, one figure, two to four short statements, one takeaway, the data source, speaker notes.
