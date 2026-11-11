#!/bin/bash
# second round of controlled scenarios on c23 (pool pinned to 7,456 blocks): c1 with the reworked token reserve, c2 (reservation gate), c3 (head-of-line)
R=/mnt/beegfs/ghu4/kvadm/results/c2; S=/home/ghu4/CXL/benchmarks/serving
run() { tag=$1; plan=$2; shift 2; $S/remote16.sh $R run_adm.py $tag plan=$plan reps=3 gpu_blocks=7456 l1_gb=40 "$@"; echo "[$(date -Is)] $tag done" >> $R/chain.txt; sleep 5; }
run c1b-base c1 hbase=6000
run c1b-tok c1 hbase=6000 "adm_env=KVADM_POLICY=tokres=768"
run c1b-tokfast512 c1 hbase=6000 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512"
run c1b-tokfast256 c1 hbase=6000 "adm_env=KVADM_POLICY=tokres=768,fastchunk=256"
run c1b-tokfast512-sync c1 hbase=6000 async_sched=off "adm_env=KVADM_POLICY=tokres=768,fastchunk=512"
run c1b-lpt512 c1 hbase=6000 long_prefill_threshold=512
run c3-base c3
run c3-skip2 c3 "adm_env=KVADM_POLICY=skip=2"
run c3-skip2-hitres c3 "adm_env=KVADM_POLICY=skip=2,hitres=600"
run c3-tokfast-skip2 c3 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,skip=2,hitres=600"
run c2-base c2
run c2-tokfast c2 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512"
run c2-tokfast-a0 c2 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,alpha=0"
run c2-tokfast-a0-out512 c2 probe_out=512 tmax=60 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,alpha=0"
run c2-tokfast-out512 c2 probe_out=512 tmax=60 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512"
run c2-tokfast-fb c2 "adm_env=KVADM_POLICY=tokres=768,fastchunk=512,skip=1,fallback=1"
echo "[$(date -Is)] c2 round done" >> $R/chain.txt
