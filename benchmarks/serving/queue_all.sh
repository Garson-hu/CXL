#!/bin/bash
# Night queue (2026-11-04): after the A chain -> SSD O_DIRECT rerun of A -> smoke tests of B and E -> B chain -> E chain -> replay chain (D, then B-real).
set -u
R=/home/ghu4/CXL/experimental_results/2026-11-04-cxl-serving-scheduling-gap; S=/home/ghu4/CXL/benchmarks/serving; PY=/mnt/local/ghu4/envs/lmcache/bin/python
log() { echo "[$(date -Is)] $*" >> $R/queue.txt; }
until grep -q "chain done" $R/A/chain.txt 2>/dev/null; do sleep 20; done
log "A chain done; ssd odirect rerun"
cd $R/A && timeout 3600 taskset -c 80-87 $PY $S/run_a.py . a-3b-ssd-odirect tier=ssd l1_gb=10 ssd_odirect=true enforce_eager=false Ls=256,512,1024,2048,4096,8192,16384 reps=8 > a-3b-ssd-odirect-driver.txt 2>&1; log "a-3b-ssd-odirect rc=$?"
# PCIe link power management: the hook-less / sampler-less control showed +30 ms on host hits (link at Gen 1 when idle); separate the two
timeout 3600 taskset -c 80-87 $PY $S/run_a.py . a-3b-dram-hooksonly tier=dram hooks=true samplers=false enforce_eager=false Ls=256,512,1024,2048,4096,8192,16384 reps=4 > a-3b-dram-hooksonly-driver.txt 2>&1; log "a-3b-dram-hooksonly rc=$?"
timeout 3600 taskset -c 80-87 $PY $S/run_a.py . a-3b-dram-samplersonly tier=dram hooks=false samplers=true enforce_eager=false Ls=256,512,1024,2048,4096,8192,16384 reps=4 > a-3b-dram-samplersonly-driver.txt 2>&1; log "a-3b-dram-samplersonly rc=$?"
mkdir -p $R/smoke && cd $R/smoke
timeout 1800 taskset -c 80-87 $PY $S/run_b.py . smokeb tier=dram scenarios=s0,s1,s2,s3 reps=1 conc=2 rates=2 bursts=4 > smokeb-driver.txt 2>&1; log "smokeb rc=$?"
timeout 1800 taskset -c 80-87 $PY $S/run_e.py . smokee tier=dram ks=1,4 Ls=4096 reps=1 > smokee-driver.txt 2>&1; log "smokee rc=$?"
log "B chain"; bash $S/run_b_chain.sh $R/B 5; log "B chain done"
log "E chain"; bash $S/run_e_chain.sh $R/E 4; log "E chain done"
log "replay chain D"; bash $S/run_replay_chain.sh $R/replay D 100 0.08; log "replay chain B"; bash $S/run_replay_chain.sh $R/replay B 100 0.08; log "all done"
