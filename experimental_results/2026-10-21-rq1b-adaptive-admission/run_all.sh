#!/bin/bash
# RQ1-B practical and adaptive admission study (2026-10-21): exact commands. Run from the repo root on c28.
# Groups: val (semantic validation against the 2026-10-20 replay), g (main grid, all policies, 5 capacities, 3 traces),
# gh (bounded ghost history), ab (adaptive ablations), tune (parameter selection on the FIRST half only), m (constructed
# mixed traces), a (real agent traces), gpu (GPU front cache sensitivity), sh (shadow tables, selection-bias check).
set -u
PY=python3; O=experimental_results/2026-10-21-rq1b-adaptive-admission; P=experimental_results/2026-10-20-rq1b-admission-study
MC="--mooncake"; ALL=lru,slru,2q,arc,tinylfu,wtinylfu,2nd,2nd_int,adapt2,adaptive,lhd,oracle
mkdir -p $O/dump
# ---- val: lru / slru / 2nd / lhd / oracle must reproduce the 2026-10-20 numbers exactly ----
$PY scripts/kv_admission_sim.py workloads/mooncake_conversation_trace.jsonl $O val-conversation-c3200 $MC --caps 3200 --policies lru,slru,2nd,lhd,oracle > $O/val-conversation-c3200.log 2>&1
# ---- g: main grid ----
for tr in conversation toolagent synthetic; do for cap in 800 1600 3200 6400 12800; do
  $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O g-$tr-c$cap $MC --caps $cap --policies $ALL --dump-hits $O/dump/g-$tr --dump-admit $O/dump/g-$tr --dump-tables $O/dump/g-$tr --plan-log $O/dump/g-$tr > $O/g-$tr-c$cap.log 2>&1 &
done; done
# ---- gh: bounded ghost history (exact LRU entries, TTL, double-buffered Bloom) ----
for tr in conversation toolagent; do for cap in 800 3200 6400; do
  ( for g in 1000 4000 16000 64000 0.5c 1c; do $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O gh-$tr-c$cap-g$g $MC --caps $cap --policies 2nd,2nd_int,adaptive --ghost $g; done ) > $O/gh-$tr-c$cap-entries.log 2>&1 &
  ( for ttl in 60 300 1200; do $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O gh-$tr-c$cap-ttl$ttl $MC --caps $cap --policies 2nd,2nd_int,adaptive --ghost-ttl $ttl; done ) > $O/gh-$tr-c$cap-ttl.log 2>&1 &
  ( for b in 32768,4,8000 65536,4,8000 262144,4,32000 1048576,4,128000; do $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O gh-$tr-c$cap-bloom${b//,/_} $MC --caps $cap --policies 2nd --ghost-bloom $b; done ) > $O/gh-$tr-c$cap-bloom.log 2>&1 &
done; done
# ---- ab: adaptive ablations (test half) ----
for tr in conversation toolagent; do for cap in 800 3200 6400; do
  ( $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O ab-$tr-c$cap-feat-c $MC --caps $cap --policies adaptive --feat c
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O ab-$tr-c$cap-feat-cint $MC --caps $cap --policies adaptive --feat c,int
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O ab-$tr-c$cap-feat-cintpos $MC --caps $cap --policies adaptive --feat c,int,pos
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O ab-$tr-c$cap-feat-cintpreroot $MC --caps $cap --policies adaptive --feat c,int,pre,root
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O ab-$tr-c$cap-nochain $MC --caps $cap --policies adaptive --no-chain
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O ab-$tr-c$cap-hitbe $MC --caps $cap --policies adaptive --label hitbe
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O ab-$tr-c$cap-th0.5 $MC --caps $cap --policies adaptive --fixed-th 0.5
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O ab-$tr-c$cap-th0.3 $MC --caps $cap --policies adaptive --fixed-th 0.3 ) > $O/ab-$tr-c$cap-1.log 2>&1 &
  ( $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O ab-$tr-c$cap-w300 $MC --caps $cap --policies adaptive --fixed-w 300
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O ab-$tr-c$cap-w120 $MC --caps $cap --policies adaptive --fixed-w 120
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O ab-$tr-c$cap-resrate $MC --caps $cap --policies adaptive,2nd_int --res-mode rate
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O ab-$tr-c$cap-frozen $MC --caps $cap --policies adaptive,adapt2 --freeze-at 0.2
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O ab-$tr-c$cap-cold $MC --caps $cap --policies adaptive,adapt2,2nd --cold-start --plan-log $O/dump/ab-$tr-cold
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O ab-$tr-c$cap-replan60 $MC --caps $cap --policies adaptive --replan 60 ) > $O/ab-$tr-c$cap-2.log 2>&1 &
done; done
# ---- tune: parameter selection for adaptive on the FIRST half only (scored 0.25-0.5; the cache warms on 0-0.25) ----
for tr in conversation toolagent; do for cap in 800 3200 6400; do
  ( for tau in 150 300 600; do for pr in 2 10 50; do $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O tune-$tr-c$cap-tau$tau-pr$pr $MC --caps $cap --policies adaptive,lru,oracle --tau $tau --prior $pr --score-range 0.25,0.5; done; done ) > $O/tune-$tr-c$cap.log 2>&1 &
done; done
# ---- m: constructed mixed traces (interleaved / phase change), 3200 blocks; agent-format jsonl (no --mooncake) ----
for mx in mix-interleave mix-phase; do
  $PY scripts/kv_admission_sim.py $P/$mx.jsonl $O m-$mx --caps 3200 --policies $ALL --dump-hits $O/dump/m-$mx --plan-log $O/dump/m-$mx --dump-tables $O/dump/m-$mx > $O/m-$mx.log 2>&1 &
  ( $PY scripts/kv_admission_sim.py $P/$mx.jsonl $O m-$mx-cold --caps 3200 --policies adaptive,adapt2,2nd --cold-start --plan-log $O/dump/m-$mx-cold
    $PY scripts/kv_admission_sim.py $P/$mx.jsonl $O m-$mx-frozen --caps 3200 --policies adaptive,adapt2 --freeze-at 0.2
    $PY scripts/kv_admission_sim.py $P/$mx.jsonl $O m-$mx-g16k --caps 3200 --policies 2nd,2nd_int,adaptive --ghost 16000 ) > $O/m-$mx-var.log 2>&1 &
done
# ---- a: real agent traces (horizons of seconds: window grid and decay scaled) ----
AG="--tok 256 --chunk-mb 9.44 --tau 30 --replan 2 --wgrid 2,4,8,15,30,60,120"
$PY scripts/kv_admission_sim.py experimental_results/2026-10-17-rq1b-agent-runtime-validation/k16-l1g-trace.jsonl $O a-short-k16 $AG --caps 24,32,48 --policies $ALL > $O/a-short-k16.log 2>&1 &
$PY scripts/kv_admission_sim.py experimental_results/2026-10-17-rq1b-reuse-horizon/lt-k16-l1g-bg2-trace.jsonl $O a-lt-k16-bg2 $AG --caps 24,32,48 --policies $ALL > $O/a-lt-k16-bg2.log 2>&1 &
# ---- gpu: vLLM GPU prefix cache in front of the host cache; ghost fed from the store path (all) or from host lookups only ----
for tr in conversation toolagent; do for gb in 512 1024; do for src in all host; do
  $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O gpu-$tr-c3200-g$gb-$src $MC --caps 3200 --policies lru,2nd,2nd_int,adapt2,adaptive,oracle --gpu-blocks $gb --ghost-src $src > $O/gpu-$tr-c3200-g$gb-$src.log 2>&1 &
done; done; done
# ---- sh: the adaptive tables maintained under other policies (selection-bias check) ----
for tr in conversation toolagent; do
  $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O sh-$tr-c3200 $MC --caps 3200 --policies lru,2nd,oracle --shadow --dump-tables $O/dump/sh-$tr > $O/sh-$tr-c3200.log 2>&1 &
done
wait; echo "campaign done"
for tr in conversation toolagent; do $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O sh-$tr-c3200-hitbe $MC --caps 3200 --policies adaptive --label hitbe --dump-tables $O/dump/sh-$tr-hitbe > $O/sh-$tr-c3200-hitbe.log 2>&1 & done
NOTE: in the g-* and m-* runs --plan-log and --dump-tables shared a file name; the plan log won (tables of those runs lost); fixed by the -tables.json suffix on 2026-10-21 00:40
# ---- tune2: configuration selection on the FIRST half (scored 0.25-0.5) for the adaptive policies: decay tau x features x threshold; adapt2 tau; 2nd_int ghost size ----
for tr in conversation toolagent; do for cap in 800 3200 6400; do
  ( for tau in 40 75 150 300; do for feat in c c,int c,int,pos,pre; do for th in -1 0.3 0.5; do $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O tune2-$tr-c$cap-tau$tau-f${feat//,/}-th$th $MC --caps $cap --policies adaptive --tau $tau --feat $feat --fixed-th $th --score-range 0.25,0.5; done; done; done ) > $O/tune2-$tr-c$cap-adaptive.log 2>&1 &
  ( for tau in 40 75 150 300; do $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O tune2-$tr-c$cap-tau$tau-adapt2 $MC --caps $cap --policies adapt2,lru,oracle --tau $tau --score-range 0.25,0.5; done
    for g in 4000 16000 64000 inf; do $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O tune2-$tr-c$cap-g$g-2nd $MC --caps $cap --policies 2nd,2nd_int --ghost $g --score-range 0.25,0.5; done ) > $O/tune2-$tr-c$cap-simple.log 2>&1 &
done; done
# ---- sel: TEST-half runs of the configurations selected on the first half (tune2-selection.md): A = adaptive tau 300, classes = touch count only, fixed threshold 0.5 (best mean);
#      B = adaptive tau 150, classes = touch count x gap bucket, replanned threshold (runner-up); C = adapt2 tau 150; D = second-touch rules with a 64k-entry ghost (best mean among ghost sizes) ----
for tr in conversation toolagent synthetic; do for cap in 800 1600 3200 6400 12800; do
  ( $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O sel-$tr-c$cap-A $MC --caps $cap --policies adaptive --tau 300 --feat c --fixed-th 0.5 --plan-log $O/dump/sel-A-$tr
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O sel-$tr-c$cap-B $MC --caps $cap --policies adaptive --tau 150 --feat c,int --plan-log $O/dump/sel-B-$tr
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O sel-$tr-c$cap-C $MC --caps $cap --policies adapt2 --tau 150
    $PY scripts/kv_admission_sim.py workloads/mooncake_${tr}_trace.jsonl $O sel-$tr-c$cap-D $MC --caps $cap --policies 2nd_int,2nd --ghost 64000 ) > $O/sel-$tr-c$cap.log 2>&1 &
done; done
for mx in mix-interleave mix-phase; do
  ( $PY scripts/kv_admission_sim.py $P/$mx.jsonl $O sel-m-$mx-A --caps 3200 --policies adaptive --tau 300 --feat c --fixed-th 0.5
    $PY scripts/kv_admission_sim.py $P/$mx.jsonl $O sel-m-$mx-B --caps 3200 --policies adaptive --tau 150 --feat c,int
    $PY scripts/kv_admission_sim.py $P/$mx.jsonl $O sel-m-$mx-C --caps 3200 --policies adapt2 --tau 150
    $PY scripts/kv_admission_sim.py $P/$mx.jsonl $O sel-m-$mx-D --caps 3200 --policies 2nd_int,2nd --ghost 64000 ) > $O/sel-m-$mx.log 2>&1 &
done
