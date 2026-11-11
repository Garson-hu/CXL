#!/bin/bash
# Regenerates the per-family tables of the 2026-11-10 admission study's trace replays (Experiment D / E): for every family (one replay, one node,
# its own stock run first) tables-primary-<name>.md (table_adm_primary.py), tables-tails-<name>.md (table_adm_tails.py) and tables-d-<name>.md
# (table_adm_d.py) in the family's results directory. Runs that do not exist (yet) are left out of a family; a family without its stock run is
# skipped. usage: tables_adm_all.sh [<c28 replay dir> [<16 GB results root>]]
S=$(dirname "$(readlink -f "$0")"); PY=${PY:-/mnt/local/ghu4/envs/agent/bin/python}
R=${1:-/mnt/local/ghu4/results/2026-11-10-gpu-kv-admission/replay}; B=${2:-/mnt/beegfs/ghu4/kvadm/results}
fam() {   # fam <dir> <name> <tag>=<label> [<tag>=<label> ...]   (labels must not contain '|' or ',')
  local d=$1 name=$2; shift 2; local tags=() labs=()
  for kv in "$@"; do local t=${kv%%=*} l=${kv#*=}; [ -e "$d/$t-adm-requests.csv" ] && { tags+=("$t"); labs+=("$l"); }; done
  [ ${#tags[@]} -ge 1 ] && [ "${tags[0]}" = "${1%%=*}" ] || { echo "skip $name (no stock run)"; return; }
  local lp; lp=$(IFS='|'; echo "${labs[*]}"); local lc; lc=$(IFS=','; echo "${labs[*]}")
  $PY $S/table_adm_primary.py "$d" "${tags[@]}" "labels=$lp" > "$d/tables-primary-$name.md"
  $PY $S/table_adm_tails.py "$d" "${tags[@]}" "labels=$lp" > "$d/tables-tails-$name.md"
  $PY $S/table_adm_d.py "$d" "${tags[@]}" "name=$name" "labels=$lc" > /dev/null
  echo "$name: ${#tags[@]} runs"
}
# --- c28, 320 GB host tier, pool 7,456 blocks
fam $R tool04-320 tool04-320-base=stock tool04-320-priohits="oracle hits-first priority" tool04-320-priolen="shortest-prompt-first priority" tool04-320-tokfast11="prototype v1.1" \
    tool04-320-p2=P2 tool04-320-p4=P4 tool04-320-skip30="bypass alone; 30 s"
fam $R tool08-320 tool08-320-base=stock tool08-320-base2="stock; second run" tool08-320-sync="synchronous scheduling" tool08-320-lpt1024="prefill cap 1024" \
    tool08-320-priohits="oracle hits-first priority" tool08-320-priolen="shortest-prompt-first priority" tool08-320-storefix="store fix alone" tool08-320-skip30="bypass alone; 30 s" \
    tool08-320-tokfast="prototype v1" tool08-320-tokfast11="prototype v1.1" tool08-320-p1=P1 tool08-320-p2=P2 tool08-320-p2-r2="P2; second run" tool08-320-p3=P3 \
    tool08-320-p4=P4 tool08-320-priohits-p1="oracle priority + P1"
fam $R conv04-320 conv04-320-base=stock conv04-320-priolen="shortest-prompt-first priority" conv04-320-skip30="bypass alone; 30 s" conv04-320-p2=P2 conv04-320-p4=P4
fam $R conv08-320 conv08-320-base=stock conv08-320-p2=P2
# --- 16 GB nodes, overloaded replays with the pool pinned to 7,456 blocks and a 150 GB host tier (own stock run per node)
fam $B/X08 x08-c60 x08-base="stock (c60)" x08-priolenage3="shortest-prompt-first with aging; 3 ms per token" x08-skip3="bypass alone; 3 s" x08-skip10="bypass alone; 10 s" x08-skip30="bypass alone; 30 s" x08-skip100="bypass alone; 100 s" \
    x08-skip30-nores="bypass alone; 30 s; no block reservation" x08-p2="P2 (token rules + bypass; 3 s)" x08-p2-skip10="token rules + bypass; 10 s" \
    x08-p2-skip30="P4 (token rules + bypass; 30 s)" x08-p2-skip30-r2="P4; second run" x08-p2-skip100="token rules + bypass; 100 s"
fam $B/X08 x08-c61 x08b-base="stock (c61)" x08b-priolen="shortest-prompt-first priority" x08b-priouncached="oracle shortest-compute-first priority" x08b-priolenage1="shortest-prompt-first with aging; 1 ms per token" x08b-skip="bypass alone; 3 s" x08b-tokfast12="v1.2 (P1 without blkfirst)" \
    x08b-p1-a20="P1 + starvation bound 20 s" x08b-p2-sync="P2 + synchronous scheduling"
fam $B/X08 x08c-conv x08c-conv-base="stock (c60)" x08c-conv-priolen="shortest-prompt-first priority" x08c-conv-skip30="bypass alone; 30 s" x08c-conv-p2=P2 x08c-conv-p2-skip30=P4
# --- 16 GB nodes, Experiment E, the 80 GB capacity point and the intermediate load
fam $B/E e-tool04-80-p7456 e-tool04-80-p7456-base="stock (c61)" e-tool04-80-p7456-priohits="oracle hits-first priority" e-tool04-80-p7456-priolen="shortest-prompt-first priority" e-tool04-80-p7456-priolen-p1="shortest-prompt-first + P1" e-tool04-80-p7456-p1=P1 e-tool04-80-p7456-p4=P4
fam $B/E e66-tool04-80-p7456 e66-tool04-80-p7456-base="stock (c66)" e66-tool04-80-p7456-priolen="shortest-prompt-first priority" e66-tool04-80-p7456-priolen-p1="shortest-prompt-first + P1" e66-tool04-80-p7456-skip30="bypass alone; 30 s" e66-tool04-80-p7456-p4=P4
fam $B/T06 t06 t06-base="stock (c73)" t06-priohits="oracle hits-first priority" t06-priolen="shortest-prompt-first priority" t06-skip30="bypass alone; 30 s" t06-p2=P2 t06-p4=P4
fam $B/E e-tool04-80-big e-tool04-80-big-base=stock e-tool04-80-big-p1=P1 e-tool04-80-big-p1-sync="P1 + synchronous scheduling"
fam $B/E e7-tool02-80 e7-tool02-80-base=stock e7-tool02-80-p1=P1
fam $B/E e-tool08-120-big e-tool08-120-big-base=stock e-tool08-120-big-priolen="shortest-prompt-first priority" e-tool08-120-big-p1=P1
# --- the cross-load matrix of report section C2.6 (configurations against load regimes; every column is a family with its own stock run)
$PY $S/table_adm_cross.py "sustainable, 320 GB (c28)=$R:tool04-320-base" "sustainable, 80 GB (c61)=$B/E:e-tool04-80-p7456-base" "sustainable, 80 GB (c66)=$B/E:e66-tool04-80-p7456-base" \
  "intermediate, 80 GB (c73)=$B/T06:t06-base" "overload, 320 GB (c28)=$R:tool08-320-base" "overload, 150 GB (c60)=$B/X08:x08-base" "overload, 150 GB (c61)=$B/X08:x08b-base" \
  "overload, large pool (c66)=$B/E:e-tool08-120-big-base" -- \
  "oracle hits-first priority=1:tool04-320-priohits,2:e-tool04-80-p7456-priohits,4:t06-priohits,5:tool08-320-priohits" \
  "shortest-prompt-first priority=1:tool04-320-priolen,2:e-tool04-80-p7456-priolen,3:e66-tool04-80-p7456-priolen,4:t06-priolen,5:tool08-320-priolen,7:x08b-priolen,8:e-tool08-120-big-priolen" \
  "oracle shortest-compute-first priority=7:x08b-priouncached" \
  "shortest-prompt-first with aging (1 ms per token on c61; 3 ms on c60)=6:x08-priolenage3,7:x08b-priolenage1" \
  "shortest-prompt-first + token mechanisms (P1)=2:e-tool04-80-p7456-priolen-p1,3:e66-tool04-80-p7456-priolen-p1" \
  "token mechanisms (P1; with the 3 s bypass, P2, on c28 at the sustainable load and on c73)=1:tool04-320-p2,2:e-tool04-80-p7456-p1,4:t06-p2,5:tool08-320-p1,8:e-tool08-120-big-p1" \
  "token mechanisms + bypass, 3 s (P2)=5:tool08-320-p2,6:x08-p2" \
  "bypass alone, 3 s=6:x08-skip3,7:x08b-skip" \
  "bypass alone, 10 s=6:x08-skip10" \
  "bypass alone, 30 s=1:tool04-320-skip30,3:e66-tool04-80-p7456-skip30,4:t06-skip30,5:tool08-320-skip30,6:x08-skip30" \
  "bypass alone, 100 s=6:x08-skip100" \
  "token mechanisms + bypass, 30 s (P4)=1:tool04-320-p4,2:e-tool04-80-p7456-p4,4:t06-p4,6:x08-p2-skip30" \
  "token mechanisms + bypass, 100 s=6:x08-p2-skip100" > "$R/tables-cross-load.md"
$PY $S/table_adm_cross.py "conversation, sustainable, 320 GB (c28)=$R:conv04-320-base" "conversation, overload, 320 GB (c28)=$R:conv08-320-base" "conversation, overload, 150 GB (c60)=$B/X08:x08c-conv-base" -- \
  "shortest-prompt-first priority=1:conv04-320-priolen,3:x08c-conv-priolen" "bypass alone, 30 s=1:conv04-320-skip30,3:x08c-conv-skip30" \
  "token mechanisms + bypass, 3 s (P2)=1:conv04-320-p2,2:conv08-320-p2,3:x08c-conv-p2" "token mechanisms + bypass, 30 s (P4)=1:conv04-320-p4,3:x08c-conv-p2-skip30" > "$R/tables-cross-load-conv.md"
echo "cross-load matrices written"
