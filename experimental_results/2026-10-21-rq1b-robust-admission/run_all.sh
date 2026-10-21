#!/bin/bash
# RQ1-B robust online reuse information and adaptive admission (2026-10-21, second round of the day): exact commands.
# Run from the repo root on c28. Groups: val (semantic validation + audit), g (focused baseline grid), reg (regime-rule
# variants: selection on the FIRST half, then test), est (residence estimators: accuracy, and which estimator drives the
# gap rule), dyn (CONSTRUCTED dynamic load: step up / step down / burst / thinning, plus the mixes), meta (bounded ghost
# under high unique-prefix arrival), dump (per-access bitmaps for the mechanism analysis), a (real agent traces).
set -u
PY=python3; O=experimental_results/2026-10-21-rq1b-robust-admission; P=experimental_results/2026-10-20-rq1b-admission-study
MC="--mooncake"; BASE=lru,slru,2nd,2nd_int,2nd_int_auto,tinylfu,oracle
mkdir -p $O/dump
# ---- val ----
$PY scripts/kv_admission_sim.py workloads/mooncake_conversation_trace.jsonl $O val-conversation-c3200 $MC --caps 3200 --policies lru,slru,2nd,2nd_int,lhd,oracle --audit > $O/val-conversation-c3200.log 2>&1
# ---- g: focused baseline grid (default regime rule: res, q 0.5, hold 30 s, normal = LRU); bounded second touch with a 64k ghost in a separate run ----
for tr in conversation toolagent synthetic; do for cap in 800 1600 3200 6400 12800; do
  ( $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O g-$tr-c$cap $MC --caps $cap --policies $BASE --audit --dump-hits $O/dump/g-$tr --plan-log $O/dump/g-$tr --res-log $O/dump/g-$tr
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O g-$tr-c$cap-g64k $MC --caps $cap --policies 2nd,2nd_int,2nd_int_auto --ghost 64000 --dump-hits $O/dump/g64k-$tr ) > $O/g-$tr-c$cap.log 2>&1 &
done; done
# ---- reg: regime-rule variants on the FIRST half (selection) and on the test half ----
for tr in conversation toolagent; do for cap in 800 3200 6400 12800; do
  ( for sr in 0.25,0.5 0.5,1.0; do tag=$( [ "$sr" = "0.25,0.5" ] && echo sel || echo test )
      for q in 0.5 0.75 0.9; do for hold in 0 30 120; do $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O reg-$tr-c$cap-$tag-res-q$q-h$hold $MC --caps $cap --policies 2nd_int_auto --regime res --regime-q $q --regime-hold $hold --score-range $sr --plan-log $O/dump/reg-$tr-$tag-q$q-h$hold; done; done
      for m in 0 0.1 0.3; do $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O reg-$tr-c$cap-$tag-model-m$m $MC --caps $cap --policies 2nd_int_auto --regime model --regime-margin $m --score-range $sr --plan-log $O/dump/reg-$tr-$tag-model-m$m; done
      $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O reg-$tr-c$cap-$tag-slru $MC --caps $cap --policies 2nd_int_auto --regime res --normal-mode slru --score-range $sr
      $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O reg-$tr-c$cap-$tag-ref $MC --caps $cap --policies lru,slru,2nd_int,oracle --score-range $sr
    done ) > $O/reg-$tr-c$cap.log 2>&1 &
done; done
# ---- est: which residence estimator drives the gap rule (test half), and estimator accuracy logs ----
for tr in conversation toolagent; do for cap in 800 3200 6400; do
  ( for rm in evict evict50 evict1000 dead rate tail median; do $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O est-$tr-c$cap-$rm $MC --caps $cap --policies 2nd_int,2nd_int_auto --res-mode $rm --res-log $O/dump/est-$tr-$rm --dec-log $O/dump/est-$tr-$rm; done ) > $O/est-$tr-c$cap.log 2>&1 &
done; done
# ---- dyn: CONSTRUCTED dynamic load at 210 GiB and 839 GiB (regime switching), both real traces; churn = 8-block never-reused requests (changed from single blocks on 2026-10-21 11:00: a single-block request is a root and the gap rules always admit a request first block, which made single-block churn pure pollution) ----
for tr in conversation toolagent; do for cap in 3200 12800; do
  ( $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O dyn-$tr-c$cap-stepup $MC --caps $cap --policies $BASE --churn 50,0.6,1.0 --res-log $O/dump/dyn-$tr-stepup --plan-log $O/dump/dyn-$tr-stepup
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O dyn-$tr-c$cap-stepdown $MC --caps $cap --policies $BASE --churn 50,0.25,0.6 --res-log $O/dump/dyn-$tr-stepdown --plan-log $O/dump/dyn-$tr-stepdown
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O dyn-$tr-c$cap-burst $MC --caps $cap --policies $BASE --churn 150,0.62,0.66 --res-log $O/dump/dyn-$tr-burst --plan-log $O/dump/dyn-$tr-burst
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O dyn-$tr-c$cap-thin $MC --caps $cap --policies $BASE --thin 0.5,0.6,1.0 --res-log $O/dump/dyn-$tr-thin --plan-log $O/dump/dyn-$tr-thin ) > $O/dyn-$tr-c$cap.log 2>&1 &
done; done
for mx in mix-interleave mix-phase; do
  $PY scripts/kv_admission_sim.py $P/$mx.jsonl $O dyn-m-$mx --caps 3200 --policies $BASE --res-log $O/dump/dyn-m-$mx --plan-log $O/dump/dyn-m-$mx --dump-hits $O/dump/dyn-m-$mx > $O/dyn-m-$mx.log 2>&1 &
done
# ---- meta: bounded ghost / Bloom under a high unique-prefix arrival rate (churn), 210 GiB ----
for tr in conversation toolagent; do
  ( for g in 16000 64000; do $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O meta-$tr-c3200-g$g-churn $MC --caps 3200 --policies 2nd,2nd_int,2nd_int_auto --ghost $g --churn 50,0.5,1.0; done
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O meta-$tr-c3200-ginf-churn $MC --caps 3200 --policies 2nd,2nd_int,2nd_int_auto --churn 50,0.5,1.0
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O meta-$tr-c3200-bloom-churn $MC --caps 3200 --policies 2nd --ghost-bloom 65536,4,8000 --churn 50,0.5,1.0
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O meta-$tr-c3200-bloom $MC --caps 3200 --policies 2nd --ghost-bloom 65536,4,8000 ) > $O/meta-$tr.log 2>&1 &
done
# ---- a: real agent traces (horizons of seconds; tau / windows scaled by hand, not selected) ----
AG="--tok 256 --chunk-mb 9.44 --tau 30 --replan 2 --regime-hold 4 --wgrid 2,4,8,15,30,60,120"
$PY scripts/kv_admission_sim.py experimental_results/2026-10-17-rq1b-agent-runtime-validation/k16-l1g-trace.jsonl $O a-short-k16 $AG --caps 24,32,48 --policies $BASE > $O/a-short-k16.log 2>&1 &
$PY scripts/kv_admission_sim.py experimental_results/2026-10-17-rq1b-reuse-horizon/lt-k16-l1g-bg2-trace.jsonl $O a-lt-k16-bg2 $AG --caps 24,32,48 --policies $BASE > $O/a-lt-k16-bg2.log 2>&1 &
wait; echo "campaign done"
# ---- reg2 (added 2026-10-21 11:05 after the first regime results): res_ft rule = admit-all residence vs the gap quantile of FIRST-touch re-lookups (the re-seen gap median is dominated by immediate re-touches on the tool-agent trace) ----
for tr in conversation toolagent; do
  ( for cap in 800 3200 6400 12800; do for sr in 0.25,0.5 0.5,1.0; do tag=$( [ "$sr" = "0.25,0.5" ] && echo sel || echo test )
      for q in 0.5 0.75 0.9; do $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O reg-$tr-c$cap-$tag-resft-q$q-h30 $MC --caps $cap --policies 2nd_int_auto --regime res_ft --regime-q $q --regime-hold 30 --score-range $sr --plan-log $O/dump/reg-$tr-$tag-resft-q$q; done
    done; done ) > $O/reg2-$tr.log 2>&1 &
done
# ---- fin (added 2026-10-21 12:10 after the regime selection tables): the regime rule that the SELECTION half ranks first — res_ft, q 0.5, hold 30 s
#      (normal admission when the predicted admit-all residence >= the median re-lookup gap of FIRST-touch blocks) — with LRU or SLRU as the normal-regime structure,
#      on the full grid, the dynamic scenarios, the mixes and the agent traces; plus its SELECTION-half runs for the SLRU variant ----
FIN="--regime res_ft --regime-q 0.5 --regime-hold 30"
for tr in conversation toolagent synthetic; do for cap in 800 1600 3200 6400 12800; do
  ( $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O fin-$tr-c$cap $MC --caps $cap --policies 2nd_int_auto $FIN --plan-log $O/dump/fin-$tr --dump-hits $O/dump/fin-$tr --res-log $O/dump/fin-$tr
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O fin-$tr-c$cap-slru $MC --caps $cap --policies 2nd_int_auto $FIN --normal-mode slru --plan-log $O/dump/finslru-$tr --dump-hits $O/dump/finslru-$tr ) > $O/fin-$tr-c$cap.log 2>&1 &
done; done
for tr in conversation toolagent; do for cap in 800 3200 6400 12800; do
  $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O fin-$tr-c$cap-sel-slru $MC --caps $cap --policies 2nd_int_auto $FIN --normal-mode slru --score-range 0.25,0.5 > $O/fin-$tr-c$cap-sel.log 2>&1 &
done; done
for tr in conversation toolagent; do for cap in 3200 12800; do
  ( for nm in lru slru; do
      $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O findyn-$tr-c$cap-stepup-$nm $MC --caps $cap --policies 2nd_int_auto $FIN --normal-mode $nm --churn 50,0.6,1.0 --plan-log $O/dump/findyn-$tr-stepup-$nm
      $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O findyn-$tr-c$cap-stepdown-$nm $MC --caps $cap --policies 2nd_int_auto $FIN --normal-mode $nm --churn 50,0.25,0.6 --plan-log $O/dump/findyn-$tr-stepdown-$nm
      $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O findyn-$tr-c$cap-burst-$nm $MC --caps $cap --policies 2nd_int_auto $FIN --normal-mode $nm --churn 150,0.62,0.66 --plan-log $O/dump/findyn-$tr-burst-$nm
      $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O findyn-$tr-c$cap-thin-$nm $MC --caps $cap --policies 2nd_int_auto $FIN --normal-mode $nm --thin 0.5,0.6,1.0 --plan-log $O/dump/findyn-$tr-thin-$nm
    done ) > $O/findyn-$tr-c$cap.log 2>&1 &
done; done
for mx in mix-interleave mix-phase; do
  ( $PY scripts/kv_admission_sim.py $P/$mx.jsonl $O findyn-m-$mx --caps 3200 --policies 2nd_int_auto $FIN --plan-log $O/dump/findyn-m-$mx
    $PY scripts/kv_admission_sim.py $P/$mx.jsonl $O findyn-m-$mx-slru --caps 3200 --policies 2nd_int_auto $FIN --normal-mode slru ) > $O/findyn-m-$mx.log 2>&1 &
done
AG="--tok 256 --chunk-mb 9.44 --tau 30 --replan 2 --regime-hold 4 --wgrid 2,4,8,15,30,60,120"
( $PY scripts/kv_admission_sim.py experimental_results/2026-10-17-rq1b-agent-runtime-validation/k16-l1g-trace.jsonl $O fin-a-short-k16 $AG --caps 24,32,48 --policies 2nd_int_auto --regime res_ft --regime-q 0.5
  $PY scripts/kv_admission_sim.py experimental_results/2026-10-17-rq1b-agent-runtime-validation/k16-l1g-trace.jsonl $O fin-a-short-k16-slru $AG --caps 24,32,48 --policies 2nd_int_auto --regime res_ft --regime-q 0.5 --normal-mode slru
  $PY scripts/kv_admission_sim.py experimental_results/2026-10-17-rq1b-reuse-horizon/lt-k16-l1g-bg2-trace.jsonl $O fin-a-lt-k16-bg2 $AG --caps 24,32,48 --policies 2nd_int_auto --regime res_ft --regime-q 0.5
  $PY scripts/kv_admission_sim.py experimental_results/2026-10-17-rq1b-reuse-horizon/lt-k16-l1g-bg2-trace.jsonl $O fin-a-lt-k16-bg2-slru $AG --caps 24,32,48 --policies 2nd_int_auto --regime res_ft --regime-q 0.5 --normal-mode slru ) > $O/fin-agents.log 2>&1 &
