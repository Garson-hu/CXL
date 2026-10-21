#!/bin/bash
# RQ1-B admission study (2026-10-20): all replays of the round. Mooncake traces: 8B blocks (67.1 MB), tail order, prefix-aware, TTFT model from the miss-cost round.
cd /home/ghu4/CXL; O=experimental_results/2026-10-20-rq1b-admission-study; W=workloads; PY=python3; COMMON="--mooncake --tok 512 --chunk-mb 67.1 --order tail --tau 300 --r0 0.000134 --r1 9.4e-9 --l 0.000005 --no-fig"
MAIN="lru,slru,static_d8,static_p8,static_n8,static_dp8_8,lhd,cond,oracle"
for tr in conversation toolagent synthetic; do for cap in 800 1600 3200 6400 12800; do
  $PY scripts/kv_agent_replay.py $W/mooncake_${tr}_trace.jsonl $O g-$tr-c$cap $COMMON --caps $cap --policies $MAIN --admit-th 0.15 --dump-hits $O/dump/g-$tr --dump-admit $O/dump/g-$tr > $O/g-$tr-c$cap.log 2>&1 &
done; done
for tr in conversation toolagent; do
  $PY scripts/kv_agent_replay.py $W/mooncake_${tr}_trace.jsonl $O v-$tr-frozen $COMMON --caps 3200 --policies lhd,cond --admit-th 0.15 --freeze-at 0.2 > $O/v-$tr-frozen.log 2>&1 &
  $PY scripts/kv_agent_replay.py $W/mooncake_${tr}_trace.jsonl $O v-$tr-explore $COMMON --caps 3200 --policies lhd --admit-th 0.15 --explore 0.05 > $O/v-$tr-explore.log 2>&1 &
  $PY scripts/kv_agent_replay.py $W/mooncake_${tr}_trace.jsonl $O v-$tr-bypassfb $COMMON --caps 3200 --policies lhd --admit-th 0.15 --bypass-feedback > $O/v-$tr-bypassfb.log 2>&1 &
  $PY scripts/kv_agent_replay.py $W/mooncake_${tr}_trace.jsonl $O v-$tr-th0.1 $COMMON --caps 3200 --policies lhd,cond --admit-th 0.1 > $O/v-$tr-th0.1.log 2>&1 &
  $PY scripts/kv_agent_replay.py $W/mooncake_${tr}_trace.jsonl $O v-$tr-th0.25 $COMMON --caps 3200 --policies lhd,cond --admit-th 0.25 > $O/v-$tr-th0.25.log 2>&1 &
  $PY scripts/kv_agent_replay.py $W/mooncake_${tr}_trace.jsonl $O v-$tr-min200 $COMMON --caps 3200 --policies lhd --admit-th 0.15 --min-samples 200 > $O/v-$tr-min200.log 2>&1 &
  $PY scripts/kv_agent_replay.py $W/mooncake_${tr}_trace.jsonl $O v-$tr-static $COMMON --caps 3200 --policies static_d4,static_d16,static_n4,static_n16,static_p4,static_p16,static_dp8_4,static_dp4_8,static_dp16_8 --dump-hits $O/dump/v-$tr > $O/v-$tr-static.log 2>&1 &
done
MIXC="--order tail --tok 512 --chunk-mb 67.1 --tau 300 --r0 0.000134 --r1 9.4e-9 --l 0.000005 --no-fig"
for mx in mix-interleave mix-phase; do
  $PY scripts/kv_agent_replay.py $O/$mx.jsonl $O m-$mx $MIXC --caps 3200 --policies lru,slru,static_n8,static_dp8_8,lhd,cond,oracle --admit-th 0.15 --dump-hits $O/dump/m-$mx > $O/m-$mx.log 2>&1 &
  $PY scripts/kv_agent_replay.py $O/$mx.jsonl $O m-$mx-frozen $MIXC --caps 3200 --policies lhd,cond --admit-th 0.15 --freeze-at 0.2 > $O/m-$mx-frozen.log 2>&1 &
done
$PY scripts/kv_agent_replay.py experimental_results/2026-10-17-rq1b-agent-runtime-validation/k16-l1g-trace.jsonl $O a-short-k16 --order tail --tau 30 --r0 0.000134 --r1 9.4e-9 --l 0.000005 --no-fig --caps 24,32,48 --policies lru,slru,event_cont,static_n4,static_d6,lhd,cond,oracle --admit-th 0.15 > $O/a-short-k16.log 2>&1 &
$PY scripts/kv_agent_replay.py experimental_results/2026-10-17-rq1b-reuse-horizon/lt-k16-l1g-bg2-trace.jsonl $O a-lt-k16-bg2 --order tail --tau 30 --r0 0.000134 --r1 9.4e-9 --l 0.000005 --no-fig --caps 24,32,48 --policies lru,slru,event_cont,static_n4,static_d6,lhd,cond,oracle --admit-th 0.15 > $O/a-lt-k16-bg2.log 2>&1 &
wait; echo "all admission replays done"
# second-touch static rule (added 2026-10-20 23:10 after the main grid): Mooncake traces at every capacity, the constructed mixed traces and the real agent traces
for tr in conversation toolagent synthetic; do for cap in 800 1600 3200 6400 12800; do $PY scripts/kv_agent_replay.py workloads/mooncake_${tr}_trace.jsonl $O s2-$tr-c$cap --mooncake --tok 512 --chunk-mb 67.1 --order tail --tau 300 --r0 0.000134 --r1 9.4e-9 --l 0.000005 --no-fig --caps $cap --policies static_2nd1,static_2nd8,static_2nd32 --dump-hits $O/dump/g-$tr --dump-admit $O/dump/g-$tr > $O/s2-$tr-c$cap.log 2>&1 & done; done
for mx in mix-interleave mix-phase; do $PY scripts/kv_agent_replay.py $O/$mx.jsonl $O s2-m-$mx --order tail --tok 512 --chunk-mb 67.1 --tau 300 --r0 0.000134 --r1 9.4e-9 --l 0.000005 --no-fig --caps 3200 --policies static_2nd1,static_2nd8 --dump-hits $O/dump/m-$mx > $O/s2-m-$mx.log 2>&1 & done
$PY scripts/kv_agent_replay.py experimental_results/2026-10-17-rq1b-agent-runtime-validation/k16-l1g-trace.jsonl $O s2-a-short-k16 --order tail --tau 30 --r0 0.000134 --r1 9.4e-9 --l 0.000005 --no-fig --caps 24,32,48 --policies static_2nd1,static_2nd4 > $O/s2-a-short-k16.log 2>&1 &
$PY scripts/kv_agent_replay.py experimental_results/2026-10-17-rq1b-reuse-horizon/lt-k16-l1g-bg2-trace.jsonl $O s2-a-lt-k16-bg2 --order tail --tau 30 --r0 0.000134 --r1 9.4e-9 --l 0.000005 --no-fig --caps 24,32,48 --policies static_2nd1,static_2nd4 > $O/s2-a-lt-k16-bg2.log 2>&1 &
