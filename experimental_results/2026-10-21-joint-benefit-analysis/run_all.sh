#!/bin/bash
# Joint benefit analysis (Phase 3, 2026-10-21): exact commands. Run from the repo root on c28.
# Groups: val (single-tier reproduction of the RQ1 numbers), sel (budget B in {0.25 … 32} GB/s x depth {1, 4} on the FIRST half for the
# budget policies, one rule for all), test (every policy at the selected budget on the test half; 6 model×speed × 2 traces ×
# 3 neighbours), reg (regime studies: capacity pressure, checkpoint co-writers, neighbour phases, phase-change trace),
# abl (decomposition at the configurations where joint differs from indep), sens (q / v thresholds).
set -u
PY=python3; O=experimental_results/2026-10-21-joint-benefit-analysis; P=experimental_results/2026-10-20-rq1b-admission-study
MC="--mooncake"; ALL=split_lru,split_slru,value_split,cost_budget,indep,joint,joint_hash,joint_2nd,joint_nodrop,indep_nodrop,oracle_cost,oracle_joint,oracle_free
mkdir -p $O/series
# ---- val ----
$PY scripts/kv_joint_sim.py workloads/mooncake_conversation_trace.jsonl $O val-single-tier $MC --dram-gib 0 --cxl-gib 200 --cxl-gbps 1000000 --neighbour none --policies split_lru,value_split,oracle_free > $O/val-single-tier.log 2>&1
# ---- sel: budget B x depth d for the critical baseline `indep` (and cost_budget / joint use the same chosen pair), first half, p99 <= 6% margin ----
for tr in conversation toolagent; do for cfg in "8b 1 67.1" "8b 4 67.1" "8b 8 67.1" "70b 1 167.8" "70b 4 167.8" "70b 8 167.8"; do set -- $cfg; m=$1; sp=$2; bm=$3
  for nb in adam reader; do
    ( for B in 0.25 0.5 1 2 4 8 12 16 24 32; do for d in 1 4; do $PY scripts/kv_joint_sim.py workloads/mooncake_${tr}_trace.jsonl $O sel-$tr-$m-${sp}x-$nb-B$B-d$d $MC --speed $sp --block-mb $bm --neighbour $nb --budget $B --depth $d --score-range 0.25,0.5 --policies indep,cost_budget,joint; done; done ) > $O/sel-$tr-$m-${sp}x-$nb.log 2>&1 &
  done
done; done
wait
$PY scripts/kv_joint_tables.py $O select > $O/selection.md
# ---- test: every policy on the test half at the selected (B, d) per trace x config x neighbour (read from selection.md's chosen.json) ----
$PY - <<'PYEOF'
import json, subprocess, os
O = "experimental_results/2026-10-21-joint-benefit-analysis"; ch = json.load(open(f"{O}/chosen.json"))
procs = []
for key, (B, d) in ch.items():
    tr, m, sp, nb = key.split("|"); bm = "67.1" if m == "8b" else "167.8"
    for nb2 in ([nb] if nb != "adam" else [nb, "none"]):
        tag = f"test-{tr}-{m}-{sp}x-{nb2}"
        cmd = f"python3 scripts/kv_joint_sim.py workloads/mooncake_{tr}_trace.jsonl {O} {tag} --mooncake --speed {sp} --block-mb {bm} --neighbour {nb2} --budget {B} --depth {d} --policies split_lru,split_slru,value_split,cost_budget,indep,joint,joint_hash,joint_2nd,joint_nodrop,indep_nodrop,oracle_cost,oracle_joint,oracle_free --series {O}/series/{tag} --dump-hits {O}/series/{tag}"
        procs.append(subprocess.Popen(cmd, shell=True, stdout=open(f"{O}/{tag}.log", "w"), stderr=subprocess.STDOUT))
for p in procs: p.wait()
PYEOF
# ---- reg: regimes beyond the grid (budgets from chosen.json are applied by the python driver below) ----
$PY - <<'PYEOF'
import json, subprocess
O = "experimental_results/2026-10-21-joint-benefit-analysis"; P = "experimental_results/2026-10-20-rq1b-admission-study"; ch = json.load(open(f"{O}/chosen.json"))
POL = "split_slru,value_split,cost_budget,indep,joint,joint_hash,oracle_cost,oracle_joint"; procs = []
def run(tag, extra, tr="conversation", m="8b", sp="8", nb="adam", trace=None):
    B, d = ch[f"{tr}|{m}|{sp}|{nb if nb != 'none' else 'adam'}"]; bm = "67.1" if m == "8b" else "167.8"; trace = trace or f"workloads/mooncake_{tr}_trace.jsonl"   # (fixed 2026-10-21: the no-neighbour runs use the Adam-selected budget)
    cmd = f"python3 scripts/kv_joint_sim.py {trace} {O} {tag} --mooncake --speed {sp} --block-mb {bm} --neighbour {nb} --budget {B} --depth {d} --policies {POL} --series {O}/series/{tag} {extra}"
    if trace.endswith("mix-phase.jsonl") or trace.endswith("mix-interleave.jsonl"): cmd = cmd.replace(" --mooncake", "")
    procs.append(subprocess.Popen(cmd, shell=True, stdout=open(f"{O}/{tag}.log", "w"), stderr=subprocess.STDOUT))
for tr in ("conversation", "toolagent"):
    # E4 capacity pressure: half the capacity (32 + 68 GiB) at 70B 4x and 8B 8x
    run(f"reg-{tr}-cap100-70b-4x-adam", "--dram-gib 32 --cxl-gib 68", tr, "70b", "4"); run(f"reg-{tr}-cap100-8b-8x-adam", "--dram-gib 32 --cxl-gib 68", tr, "8b", "8")
    # E5 checkpoint co-writer: 64 GiB every 60 s and every 15 s, fifo / kvprio / joint rule, at 70B 4x and 8B 8x beside Adam
    for m, sp in (("70b", "4"), ("8b", "8")):
        for per in ("60", "15"):
            for mode in ("fifo", "kvprio", "joint"): run(f"reg-{tr}-ckpt{per}-{mode}-{m}-{sp}x-adam", f"--ckpt 64,{per},{mode}", tr, m, sp)
    # E6 neighbour phases (Adam 30 s on / 30 s off; budget 32 while off) at 70B 4x and 8B 8x
    for m, sp in (("70b", "4"), ("8b", "8")): run(f"reg-{tr}-phases-{m}-{sp}x-adam", "--phases 30,30 --budget-off 32", tr, m, sp)
    # E3 CXL saturation without a neighbour: 70B 8x, none
    run(f"reg-{tr}-sat-70b-8x-none", "", tr, "70b", "8", "none")
# E6 phase-change and interleaved CONSTRUCTED traces at 70B 4x beside Adam (budget of the conversation config)
run("reg-mixphase-70b-4x-adam", "", "conversation", "70b", "4", "adam", f"{P}/mix-phase.jsonl"); run("reg-mixinter-70b-4x-adam", "", "conversation", "70b", "4", "adam", f"{P}/mix-interleave.jsonl")
for p in procs: p.wait()
PYEOF
# ---- sens: joint thresholds and the drop bound at 70B 8x / 8B 8x beside Adam (conversation) ----
$PY - <<'PYEOF'
import json, subprocess
O = "experimental_results/2026-10-21-joint-benefit-analysis"; ch = json.load(open(f"{O}/chosen.json")); procs = []
for m, sp in (("70b", "8"), ("8b", "8"), ("70b", "4")):
    B, d = ch[f"conversation|{m}|{sp}|adam"]; bm = "67.1" if m == "8b" else "167.8"
    for q in ("1", "2", "5"):
        for v in ("0.3", "0.5", "0.7"):
            tag = f"sens-{m}-{sp}x-q{q}-v{v}"; cmd = f"python3 scripts/kv_joint_sim.py workloads/mooncake_conversation_trace.jsonl {O} {tag} --mooncake --speed {sp} --block-mb {bm} --neighbour adam --budget {B} --depth {d} --qmax {q} --vth {v} --policies cost_budget,indep,joint"
            procs.append(subprocess.Popen(cmd, shell=True, stdout=open(f"{O}/{tag}.log", "w"), stderr=subprocess.STDOUT))
    tag = f"sens-{m}-{sp}x-migrate"; cmd = f"python3 scripts/kv_joint_sim.py workloads/mooncake_conversation_trace.jsonl {O} {tag} --mooncake --speed {sp} --block-mb {bm} --neighbour adam --budget {B} --depth {d} --migrate --policies indep,joint"
    procs.append(subprocess.Popen(cmd, shell=True, stdout=open(f"{O}/{tag}.log", "w"), stderr=subprocess.STDOUT))
for p in procs: p.wait()
PYEOF
echo "campaign done"
# ---- stress (added 2026-10-21 after the grid showed no congestion): where would value x cost couple? CXL path reduced to one card (23 GB/s) and below, and a 64 GiB checkpoint every 5 s, at 70B 8x beside Adam (CONSTRUCTED stress, not a measured condition) ----
$PY - <<'PYEOF'
import json, subprocess
O = "experimental_results/2026-10-21-joint-benefit-analysis"; ch = json.load(open(f"{O}/chosen.json")); procs = []
POL = "split_slru,value_split,cost_budget,indep,indep_nodrop,joint,joint_hash,joint_nodrop,oracle_cost,oracle_joint"
for tr in ("conversation", "toolagent"):
    B, d = ch[f"{tr}|70b|8|adam"]
    for cg in ("23", "12", "6"):
        tag = f"stress-{tr}-70b-8x-cxl{cg}-adam"; cmd = f"python3 scripts/kv_joint_sim.py workloads/mooncake_{tr}_trace.jsonl {O} {tag} --mooncake --speed 8 --block-mb 167.8 --neighbour adam --budget {B} --depth {d} --cxl-gbps {cg} --policies {POL} --series {O}/series/{tag}"
        procs.append(subprocess.Popen(cmd, shell=True, stdout=open(f"{O}/{tag}.log", "w"), stderr=subprocess.STDOUT))
    for mode in ("fifo", "kvprio", "joint"):
        tag = f"stress-{tr}-70b-8x-ckpt5-{mode}-adam"; cmd = f"python3 scripts/kv_joint_sim.py workloads/mooncake_{tr}_trace.jsonl {O} {tag} --mooncake --speed 8 --block-mb 167.8 --neighbour adam --budget {B} --depth {d} --ckpt 64,5,{mode} --policies {POL}"
        procs.append(subprocess.Popen(cmd, shell=True, stdout=open(f"{O}/{tag}.log", "w"), stderr=subprocess.STDOUT))
    # budget starved: the safe DRAM budget set to 1 GB/s and the CXL path to one card, 70B 8x
    tag = f"stress-{tr}-70b-8x-cxl23-b1-adam"; cmd = f"python3 scripts/kv_joint_sim.py workloads/mooncake_{tr}_trace.jsonl {O} {tag} --mooncake --speed 8 --block-mb 167.8 --neighbour adam --budget 1 --depth 1 --cxl-gbps 23 --policies {POL}"
    procs.append(subprocess.Popen(cmd, shell=True, stdout=open(f"{O}/{tag}.log", "w"), stderr=subprocess.STDOUT))
for p in procs: p.wait()
PYEOF
# ---- 2026-10-21, after the campaign: the two mixed-trace regime runs (reg-mixphase / reg-mixinter) had crashed on the non-hex block ids
# of the constructed agent-format traces ('c0', 't0', ...) in the hash-share placement; kv_joint_sim.py now maps non-hex ids with crc32
# (hex Mooncake ids keep the old mapping, so no other run is affected). The two runs were repeated with the reg driver's exact arguments
# (budget 4 GB/s depth 1 = the conversation 70B 4x Adam selection):
#   python3 scripts/kv_joint_sim.py $P/mix-phase.jsonl      $O reg-mixphase-70b-4x-adam --speed 4 --block-mb 167.8 --neighbour adam --budget 4.0 --depth 1.0 --policies split_slru,value_split,cost_budget,indep,joint,joint_hash,oracle_cost,oracle_joint --series $O/series/reg-mixphase-70b-4x-adam
#   python3 scripts/kv_joint_sim.py $P/mix-interleave.jsonl $O reg-mixinter-70b-4x-adam --speed 4 --block-mb 167.8 --neighbour adam --budget 4.0 --depth 1.0 --policies split_slru,value_split,cost_budget,indep,joint,joint_hash,oracle_cost,oracle_joint --series $O/series/reg-mixinter-70b-4x-adam
# After the campaign the per-second series and hit bitmaps in series/ were gzip-compressed in place (lossless; kv_joint_pressure.py and
# kv_joint_figs.py read either form).
