#!/bin/bash
# Regenerates every figure of the 2026-11-10 admission study's report into <results>/figs (the calls behind figures A1, A2 and 1-8).
# usage: figs_adm_all.sh [<c28 results dir> [<16 GB results root>]]
S=$(dirname "$(readlink -f "$0")"); PY=${PY:-/mnt/local/ghu4/envs/agent/bin/python}
F=${1:-/mnt/local/ghu4/results/2026-11-10-gpu-kv-admission}; B=${2:-/mnt/beegfs/ghu4/kvadm/results}; R=$F/replay; X=$B/X08
# figures A1, A2 (waiting time by reason, TTFT by engine state at arrival), 1 (occupancy against admission wait), 2 (prefix length)
$PY $S/figs_adm.py $F/figs replay=$R:tool04-320-base,tool08-320-base,conv04-320-base,conv08-320-base a3=$F/A3:a3
# figures 3, 3b (concurrency / arrival rate against TTFT) and 6 (throughput against measured pressure): mixed workloads, four pools
$PY $S/figs_adm2.py $F/figs cc=$B/cc:14912=cc-p14912-base,cc-p14912-p1,cc-p14912-p2+7456=cc-p7456-base,cc-p7456-p1,cc-p7456-p2+3728=cc-p3728-base,cc-p3728-p1,cc-p3728-p2+2560=cc-p2560-base,cc-p2560-p1,cc-p2560-p2 plab=P1 plab2=P2
# figure 4 (request timelines behind a 28k-token prefill)
$PY $S/figs_adm2.py $F/figs c1=$B/c1c:c1c-base,c1c-tokfast512-sync,28000 "plab=token reserve, 512-token steps, synchronous scheduling"
# figure 5 (hits against misses in the four primary replays; the conversation trace under overload is the c60 family)
# (labels must not contain commas: they separate the runs of a panel)
OP="oracle hits-first priority"; SP="shortest-prompt-first priority"; P2="token mechanisms + 3 s bypass (P2)"; P4="token mechanisms + 30 s bypass (P4)"; BA="bypass alone (30 s)"
$PY $S/figs_adm2.py $F/figs "d=tool-agent trace at 0.04× (sustainable load), c28=$R:tool04-320-base,tool04-320-priohits@$OP,tool04-320-priolen@$SP,tool04-320-p2@$P2,tool04-320-p4@$P4,tool04-320-skip30@$BA||tool-agent trace at 0.08× (overload), c28=$R:tool08-320-base,tool08-320-priohits@$OP,tool08-320-priolen@$SP,tool08-320-p2@$P2,tool08-320-p4@$P4,tool08-320-skip30@$BA||conversation trace at 0.04× (sustainable load), c28=$R:conv04-320-base,conv04-320-priolen@$SP,conv04-320-p2@$P2,conv04-320-p4@$P4,conv04-320-skip30@$BA||conversation trace at 0.08× (overload), node c60=$X:x08c-conv-base,x08c-conv-priolen@$SP,x08c-conv-p2@$P2,x08c-conv-p2-skip30@$P4,x08c-conv-skip30@$BA"
# figure 7 (every configuration of the overloaded replay on c28 as a point)
$PY $S/figs_adm2.py $F/figs "t=$R:tool08-320-base,tool08-320-sync,tool08-320-lpt1024,tool08-320-priohits,tool08-320-priolen,tool08-320-storefix,tool08-320-tokfast11,tool08-320-p1,tool08-320-p2,tool08-320-p3,tool08-320-skip30,tool08-320-priohits-p1" \
  "tlab=stock|synchronous scheduling|prefill cap 1,024|oracle hits-first priority|shortest-prompt-first priority|store fix alone|prototype v1.1|P1 (token mechanisms)|P2 (P1 + bypass, 3 s)|P3 (P2 + starvation bound)|bypass alone, 30 s|oracle priority + P1" \
  "ttitle=Overloaded tool-agent replay (0.08×), c28, GPU KV pool 7,456 blocks, 320 GB host tier"
# figure 8 (the bound of the bypass, node c60)
$PY $S/fig_bypass_bound.py $F/figs $X x08-base x08-p2=3 x08-p2-skip10=10 x08-p2-skip30=30 x08-p2-skip100=100 alone:x08-skip3=3 alone:x08-skip10=10 alone:x08-skip30=30 alone:x08-skip100=100 \
  "title=Overloaded tool-agent replay (0.08×), GPU KV pool 7,456 blocks, node c60"
