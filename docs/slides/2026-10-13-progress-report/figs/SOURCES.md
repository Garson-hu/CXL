# Figure → data sources (all under experimental_results/ unless a path is given)

| figure | source files |
|---|---|
| f01_drain_cliff | 2026-09-08-dram-write-drain/1b-matrix.csv; 2026-09-08-dram-write-drain/1b2-matrix.csv; 2026-09-08-dram-write-drain/1b-aggressor.csv; 2026-10-09-cxl-topology-interference/topo.txt |
| f02_original_core | 2026-09-22-three-policies-realdata/summary.csv |
| f03_arch_original | docs/DESIGN.md §10 (as built) |
| f04_unified_pool | WORKLOG.md session 29 (2026-10-09 discussion) |
| f15_budget_design | benchmarks/memory/kvemu2.c (policy budget) |
| f05_topology | 2026-10-09-cxl-topology-interference/topo.txt |
| f06_cxl_reader | 2026-10-09-cxl-topology-interference/topo.txt; 2026-10-07-read-cost/readcost.txt |
| f07_throttle_optane | 2026-10-10-lmcache-kv-traffic/layer2/summary.csv; 2026-10-11-throttled-dram-baseline/summary.csv; 2026-10-06-optane-control/matrix.csv; 2026-10-06-optane-control/aggressor.csv |
| f08_real_kv | 2026-10-10-lmcache-kv-traffic/layer1/summary.txt; 2026-10-10-lmcache-kv-traffic/layer1/sat-alone-pcie.txt.gz; 2026-10-10-lmcache-kv-traffic/layer1/sat-alone-meta.txt |
| f09_emulation_rate | 2026-10-10-lmcache-kv-traffic/layer2/summary.csv |
| f10_emulation_neighbors | 2026-10-10-lmcache-kv-traffic/layer2/summary.csv |
| f11_kv_capacity | 2026-10-09-kv-capacity-characterization/kv-capacity.csv |
| f12_real_lmcache | 2026-10-11-capacity-matched-kv/real/summary.txt |
| f13_admission_migration | 2026-10-11-capacity-matched-kv/emulation/summary.csv |
| f14_controller_limit | 2026-10-11-capacity-matched-kv/emulation/summary.csv (opt-70b-4x-*) |
| f16_bga_calibration | 2026-10-12-budget-gated-admission/calibration/summary.csv |
| f17_bga_evaluation | 2026-10-12-budget-gated-admission/evaluation/summary.csv |
| f18_bga_depth | 2026-10-12-budget-gated-admission/calibration/summary.csv; 2026-10-12-budget-gated-admission/depth/summary.csv |
| f19_bga_varying | 2026-10-12-budget-gated-admission/varying/summary.csv; 2026-10-12-budget-gated-admission/longrun/summary.csv |
| f20_ckpt_kv | 2026-10-12-checkpoint-kv-mixed/emulation/*.txt.gz (S3 lines); 2026-10-12-checkpoint-kv-mixed/real/summary.txt |
| f21_two_resources | memory: user decisions 2026-10-09 (Direction 2) |
| f22_emulation_method | benchmarks/memory/kvemu2.c; benchmarks/memory/run_exp2b.py |
| f23_direction | this deck (proposal) |
