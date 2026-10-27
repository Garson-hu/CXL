#!/bin/bash
#SBATCH -p a100
#SBATCH -w c33
#SBATCH -t 24:00:00
#SBATCH -c 16
#SBATCH -J cf-trace
#SBATCH -o /home/ghu4/CXL/experimental_results/2026-10-27-reuse-window-prefetch/train/main-%j.out
module load cuda 2>/dev/null
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}
PY=/home/ghu4/hvac/rlibrary/miniconda3/envs/hvac_tf/bin/python
O=/home/ghu4/CXL/experimental_results/2026-10-27-reuse-window-prefetch/train
hostname; nvidia-smi -L; free -g | head -2; date
cd $O && $PY train_trace.py /mnt/beegfs/ghu4/hvac/cosmoUniverse_2019_05_4parE_tf_v2_mini/train_61440 $O/run-61440 --epochs 3 --batch-size 4 --seed 0 --read-par 8 --parse-par 4 --prefetch 8 2>&1 | grep -v "^I0\|cpu_feature_guard\|oneDNN\|rebuild TensorFlow"
date; echo MAINDONE
