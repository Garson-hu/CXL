#!/usr/bin/env bash
# Phase 2 campaign: 2 victims x 7 policy settings x 3 repetitions, repetitions interleaved.
OUT=$1; mkdir -p $OUT; cd "$(dirname "$0")"
{ date; uptime; grep MemFree /proc/meminfo; } > $OUT/machine-state.txt
for rep in 1 2 3; do
  for victim in opt reader; do
    if [ $victim = opt ]; then R1=10; R2=20; BT=1.05; MT=1.02; BL=1.10; ML=1.05; else R1=20; R2=30; BT=1.09; MT=1.05; BL=1.15; ML=1.08; fi
    python3 run_policy.py $OUT $victim dram $rep --period 25
    python3 run_policy.py $OUT $victim dram-plain $rep --period 25
    python3 run_policy.py $OUT $victim cxl $rep --period 25
    python3 run_policy.py $OUT $victim dram-limited $rep --rate $R1 --period 25
    python3 run_policy.py $OUT $victim dram-limited $rep --rate $R2 --period 25
    python3 run_policy.py $OUT $victim cxlpath $rep --bound $BT --margin $MT --period 25
    python3 run_policy.py $OUT $victim cxlpath $rep --bound $BL --margin $ML --period 25
  done
done
echo ALL-DONE
