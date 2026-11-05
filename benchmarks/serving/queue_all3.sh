#!/bin/bash
# Night queue, part 3 (2026-11-04 21:00, after the home-directory quota stopped part 2): b-noasync rerun -> E chain -> replay D -> replay B -> F -> G (clean SSD rerun) -> H (hits-first + chunk 512).
set -u
R=/home/ghu4/CXL/experimental_results/2026-11-04-cxl-serving-scheduling-gap; S=/home/ghu4/CXL/benchmarks/serving; PY=/mnt/local/ghu4/envs/lmcache/bin/python
log() { echo "[$(date -Is)] $*" >> $R/queue.txt; }
log "part 3 start (results now on /mnt/local, symlinked)"
cd $R/B && log "b-noasync rerun"; timeout 5400 taskset -c 80-87 $PY $S/run_b.py . b-noasync reps=5 tier=dram async_sched=off > b-noasync-driver.txt 2>&1; echo "[$(date -Is)] end b-noasync rc=$?" >> chain.txt
log "E chain"; bash $S/run_e_chain.sh $R/E 4; log "E chain done"
log "replay chain D"; bash $S/run_replay_chain.sh $R/replay D 100 0.08; log "replay chain B"; bash $S/run_replay_chain.sh $R/replay B 100 0.08
mkdir -p $R/F && cd $R/F
log "F: s4 default"; timeout 5400 taskset -c 80-87 $PY $S/run_b.py . f-default tier=dram scenarios=s4 > f-default-driver.txt 2>&1; log "f-default rc=$?"
log "F: s4 none"; timeout 5400 taskset -c 80-87 $PY $S/run_b.py . f-none tier=none scenarios=s4 > f-none-driver.txt 2>&1; log "f-none rc=$?"
cd $R/A && log "G: clean ssd odirect rerun"; timeout 3600 taskset -c 80-87 $PY $S/run_a.py . a-3b-ssd-odirect2 tier=ssd l1_gb=10 ssd_odirect=true enforce_eager=false Ls=256,512,1024,2048,4096,8192,16384 reps=8 > a-3b-ssd-odirect2-driver.txt 2>&1; log "a-3b-ssd-odirect2 rc=$?"
cd $R/B && log "H: b-prio-hits-chunk512"; timeout 5400 taskset -c 80-87 $PY $S/run_b.py . b-prio-hits-chunk512 reps=5 tier=dram prio=hits_first max_batched=512 > b-prio-hits-chunk512-driver.txt 2>&1; log "b-prio-hits-chunk512 rc=$?"
log "all done 3"
