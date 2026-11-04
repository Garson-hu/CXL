#!/bin/bash
# Night queue, part 2 (2026-11-04 18:35): B chain (fixed sequences) -> E chain -> replay chain D -> replay chain B -> "all done" (queue_f.sh then runs F).
set -u
R=/home/ghu4/CXL/experimental_results/2026-11-04-cxl-serving-scheduling-gap; S=/home/ghu4/CXL/benchmarks/serving
log() { echo "[$(date -Is)] $*" >> $R/queue.txt; }
log "B chain (restart with fixed sequences)"; bash $S/run_b_chain.sh $R/B 5; log "B chain done"
log "E chain"; bash $S/run_e_chain.sh $R/E 4; log "E chain done"
log "replay chain D"; bash $S/run_replay_chain.sh $R/replay D 100 0.08; log "replay chain B"; bash $S/run_replay_chain.sh $R/replay B 100 0.08; log "all done"
