#!/bin/bash
# RQ1-B reuse-horizon validation (2026-10-17): process one finished long-tool run <tag> — join events, export the trace,
# replay it at churn 0 / 2 / 5 / 10 chunks/s (the churn is SYNTHETIC; churn 0 is the real trace alone).
# usage: process_lt.sh <tag> [churns=0,2,5,10]
cd /home/ghu4/CXL || exit 1
T=$1; CH=${2:-0,2,5,10}; O=experimental_results/2026-10-17-rq1b-reuse-horizon; D=$O/real
python3 scripts/kv_agent_events.py $D $T $O > $O/$T-events.log 2>&1 || { echo "events failed for $T"; exit 1; }
for c in ${CH//,/ }; do
  python3 scripts/kv_agent_replay.py $O/$T-trace.jsonl $O $T-churn$c --caps 24,32,48,64,96,128,192,256,384 --churn $c --no-fig > $O/$T-churn$c.log 2>&1 &
done
wait; echo "processed $T"
