#!/usr/bin/env bash
# P0 smoke runs (2026-11-12): one short single-request run per tier on the real devices, with the residency hashes on.
cd /home/ghu4/CXL/benchmarks/serving; OUT=/mnt/local/ghu4/results/2026-11-12-cxl-vs-nvme-serving/P0; PY=/mnt/local/ghu4/envs/lmcache/bin/python
COMMON="Ls=2048,8192 reps=2 adm=true adm_env=KVADM_POLICY=storefix lm_hook=kvtier lm_env=KVTIER_VERIFY=1"
run() { tag=$1; shift; echo "[$(date +%T)] $tag"; taskset -c 80-87 $PY run_a.py $OUT $tag "$@" $COMMON > $OUT/$tag-driver.txt 2>&1; echo "[$(date +%T)] $tag rc=$?"; }
run p0-daxl2-s tier=daxl2 l1_gb=8 dax_devs=/dev/dax1.0:8,/dev/dax0.0:8 l2_policy=skip_l1
run p0-ssd-s   tier=ssd   l1_gb=8 keep_ssd=true
run p0-ssdn-s  tier=ssdn  l1_gb=8 l2_gb=16 l2_policy=skip_l1 keep_ssd=true
run p0-dax-s   tier=dax   l1_gb=8 dax_path=/dev/dax1.0
run p0-dram-s  tier=dram  l1_gb=8
run p0-hyb2-s  tier=hyb   l1_gb=2 dax_devs=/dev/dax1.0:4,/dev/dax0.0:4 n_fill=12
run p0-daxl2wt-s tier=daxl2 l1_gb=8 dax_devs=/dev/dax1.0:8,/dev/dax0.0:8 l2_policy=default l2_prefetch=retain
echo "[$(date +%T)] smoke1 done"
