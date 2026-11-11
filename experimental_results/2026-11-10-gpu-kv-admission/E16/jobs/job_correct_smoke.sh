#!/bin/bash
# smoke test of run_correct.py (8 prompts), node c66, stock
R=/mnt/beegfs/ghu4/kvadm/results/correct; S=/home/ghu4/CXL/benchmarks/serving
$S/remote16.sh $R run_correct.py correct-smoke n=8 gpu_blocks=7456 l1_gb=40; echo "[$(date -Is)] correct-smoke done on $(hostname)" >> $R/chain.txt
