#!/usr/bin/env bash
# CXL-vs-NVMe study (2026-11-12), phases P0 (path validation) and A (single-request retrieval). One run at a time on c28's GPU.
#   P0: short runs with KVTIER_VERIFY=1; right after each run (before anything else writes to the devices) an independent process
#       maps the DAX devices read-only and compares SHA-1 hashes (verify_residency.py); the file tiers are checked for page-cache
#       residency and read back with O_DIRECT. p0-ssdn-buf is the CONTROL with buffered I/O (use_odirect=false): it shows what
#       page-cache contamination looks like in the same checks and is not a performance result.
#   p0full: the whole of /dev/dax1.0 + /dev/dax0.0 (512 GiB): hybrid L1 with a 4 GiB DRAM part (the measured prompts land on
#       Device-DAX) and with the 80 GiB DRAM part of the main runs, and the DAX L2 adapter. (The first attempt, 2026-11-12 15:28, with
#       7,456 GPU blocks failed: vLLM could not start beside the 1.3 GiB of GPU memory the registration takes; the nine A runs queued
#       behind it then ran against the left-over cache server and are void -- kept as *-void-* files.)
#   A:  run_a.py per tier, prefixes 512 ... 16K, 5 repetitions, the GPU KV pool of the study (6,400 blocks), flush = 8 x 16,320 tokens.
#       a-hyb-nopin: hybrid L1 whose Device-DAX arenas are NOT registered with CUDA (KVTIER_NO_PIN=1): the pageable-copy path.
# usage: queue_tier_p0a.sh [p0] [p0full] [a]
set -u
cd /home/ghu4/CXL/benchmarks/serving; R=/mnt/local/ghu4/results/2026-11-12-cxl-vs-nvme-serving; PY=/mnt/local/ghu4/envs/lmcache/bin/python
FIX="adm=true adm_env=KVADM_POLICY=storefix lm_hook=kvtier"
FULL="dax_devs=/dev/dax1.0:269.5,/dev/dax0.0:242.5"
run() { out=$1; tag=$2; shift 2; echo "[$(date '+%F %T')] $tag start"; taskset -c 80-87 $PY run_a.py $R/$out $tag "$@" $FIX > $R/$out/$tag-driver.txt 2>&1; rc=$?; echo "[$(date '+%F %T')] $tag rc=$rc"; }
vdax() { $PY verify_residency.py $R/P0/$1-kvevents.jsonl > $R/P0/$1-residency.txt 2>&1; tail -1 $R/P0/$1-residency.txt; }
vfs()  { $PY verify_residency.py --files /mnt/local/ghu4/kvl2/$1 > $R/P0/$1-residency.txt 2>&1; tail -2 $R/P0/$1-residency.txt; rm -rf /mnt/local/ghu4/kvl2/$1; }
# GPU KV pool of the study: 6,400 blocks in every configuration (see env/vram-registered.txt: registering 592 GiB of host memory with
# CUDA costs 1.2 GiB of the 8 GiB card, and 7,456 blocks no longer fit beside it); gpu_util only has to pass vLLM's start-up check.
GPU="gpu_blocks=6400 gpu_util=0.8"
if [[ " $* " == *" p0 "* ]]; then
  V="Ls=2048,8192 reps=2 lm_env=KVTIER_VERIFY=1"
  run P0 p0-dax-v     tier=dax   l1_gb=8 dax_path=/dev/dax1.0 $V;                                        vdax p0-dax-v
  run P0 p0-hyb2-v    tier=hyb   l1_gb=2 dax_devs=/dev/dax1.0:4,/dev/dax0.0:4 n_fill=12 $V;               vdax p0-hyb2-v
  run P0 p0-daxl2-v   tier=daxl2 l1_gb=8 dax_devs=/dev/dax1.0:8,/dev/dax0.0:8 l2_policy=skip_l1 $V;       vdax p0-daxl2-v
  run P0 p0-ssd-v     tier=ssd   l1_gb=8 keep_ssd=true $V;                                                vfs p0-ssd-v
  run P0 p0-ssdn-v    tier=ssdn  l1_gb=8 l2_gb=16 l2_policy=skip_l1 keep_ssd=true $V;                     vfs p0-ssdn-v
  run P0 p0-ssdn-buf  tier=ssdn  l1_gb=8 l2_gb=16 l2_policy=skip_l1 keep_ssd=true ssd_odirect=false $V;   vfs p0-ssdn-buf
fi
if [[ " $* " == *" p0full "* ]]; then      # the whole of /dev/dax1.0 + /dev/dax0.0 with the 80 GiB DRAM L1 of the main runs
  V="Ls=2048,8192 reps=2 lm_env=KVTIER_VERIFY=1 $GPU n_fill=8"
  run P0 p0-hyb-full2  tier=hyb   l1_gb=4  $FULL $V;                                                      vdax p0-hyb-full2
  run P0 p0-hyb-full80 tier=hyb   l1_gb=80 $FULL $V;                                                      vdax p0-hyb-full80
  run P0 p0-daxl2-full2 tier=daxl2 l1_gb=80 $FULL l2_policy=skip_l1 $V;                                   vdax p0-daxl2-full2
fi
if [[ " $* " == *" a "* ]]; then
  A="Ls=512,1024,2048,4096,8192,16384 reps=5 $GPU n_fill=8"
  run A a-dram    tier=dram  l1_gb=80 $A
  run A a-dax     tier=dax   l1_gb=80 dax_path=/dev/dax1.0 $A
  run A a-hyb     tier=hyb   l1_gb=4 $FULL $A
  run A a-hyb-nopin tier=hyb l1_gb=4 $FULL $A lm_env=KVTIER_NO_PIN=1
  run A a-daxl2   tier=daxl2 l1_gb=80 $FULL l2_policy=skip_l1 $A
  run A a-ssd     tier=ssd   l1_gb=80 $A
  run A a-ssdn    tier=ssdn  l1_gb=80 l2_gb=512 l2_policy=skip_l1 $A
  run A a-ssdn16  tier=ssdn  l1_gb=80 l2_gb=512 l2_policy=skip_l1 l2_workers=16 $A
  run A a-ssdn-buf tier=ssdn l1_gb=80 l2_gb=512 l2_policy=skip_l1 ssd_odirect=false $A
  run A a-none    tier=none  Ls=512,1024,2048,4096,8192,16384 reps=3 $GPU n_fill=8
fi
echo "[$(date '+%F %T')] queue done: $*"
