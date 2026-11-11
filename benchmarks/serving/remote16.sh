#!/bin/bash
# Run one serving driver on a 16 GB RTX 4060 Ti node of the rtx4060ti16g partition (2026-11-10, Experiment E).
# The node has 16 cores and 125 GiB of RAM. The environment and the model cache are copies on the shared scratch file
# system (rsync -a of c28's /mnt/local/ghu4/envs/lmcache and /mnt/local/ghu4/hf/hub, 2026-11-10). The environment must be
# visible under its c28 path, because flashinfer's JIT cache (~/.cache/flashinfer, built on c28) records that path and would
# otherwise rebuild its kernels (no compiler set up on these nodes): the only thing written to the node's /mnt/local is the
# directory /mnt/local/ghu4/envs with one symlink (the node's /mnt/local holds other data of the user; untouched).
# usage (inside an sbatch job): remote16.sh <out_dir> <driver.py> <tag> [driver args ...]
set -u
SCR=/mnt/beegfs/ghu4/kvadm
mkdir -p /mnt/local/ghu4/envs && [ -e /mnt/local/ghu4/envs/lmcache ] || ln -s $SCR/envs/lmcache /mnt/local/ghu4/envs/lmcache
export KVADM_SCRATCH=$SCR KVADM_TMP=/tmp/ghu4-kvadm PATH=/mnt/local/ghu4/envs/lmcache/bin:$PATH
mkdir -p "$KVADM_TMP" "$SCR/cache/vllm" "$1"; cd "$1" || exit 1
OUT=$1; DRV=$2; TAG=$3; shift 3
# wait until the previous run's server has given the GPU memory back (2026-11-10 21:06: a run that started 5 s after a 14,912-block
# server had stopped found 8.6 GiB still in use and vLLM refused to start); at most 3 minutes
for _i in $(seq 90); do
  _u=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1); [ "${_u:-0}" -lt 1000 ] && break; sleep 2
done
{ echo "# $(date -Is) $(hostname)"; nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader; lscpu | grep -E 'Model name'; free -g | sed -n 2p; ls -l /mnt/local/ghu4/envs/; } > "$TAG-node.txt" 2>&1
taskset -c 14-15 /mnt/local/ghu4/envs/lmcache/bin/python /home/ghu4/CXL/benchmarks/serving/$DRV . "$TAG" "$@" vllm_cpus=0-9 lm_cpus=10-13 gpu_sampler_cpu=14 cpu_sampler_cpu=15 > "$TAG-driver.txt" 2>&1
echo "rc=$?" >> "$TAG-driver.txt"
