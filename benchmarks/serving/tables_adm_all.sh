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
fam $R tool04-320 tool04-320-base=stock tool04-320-priohits="oracle hits-first priority" tool04-320-tokfast11="prototype v1.1" tool04-320-p2=P2 tool04-320-p4=P4
fam $R tool08-320 tool08-320-base=stock tool08-320-base2="stock; second run" tool08-320-sync="synchronous scheduling" tool08-320-lpt1024="prefill cap 1024" \
    tool08-320-priohits="oracle hits-first priority" tool08-320-storefix="store fix alone" tool08-320-tokfast="prototype v1" tool08-320-tokfast11="prototype v1.1" \
    tool08-320-p1=P1 tool08-320-p2=P2 tool08-320-p2-r2="P2; second run" tool08-320-p3=P3 tool08-320-p4=P4 tool08-320-priohits-p1="oracle priority + P1"
fam $R conv04-320 conv04-320-base=stock conv04-320-p2=P2 conv04-320-p4=P4
fam $R conv08-320 conv08-320-base=stock conv08-320-p2=P2
# --- 16 GB nodes, overloaded replays with the pool pinned to 7,456 blocks and a 150 GB host tier (own stock run per node)
fam $B/X08 x08-c60 x08-base="stock (c60)" x08-skip30="bypass alone; 30 s" x08-p2="P2 (bypass bound 3 s)" x08-p2-skip10="P2 with a bound of 10 s" \
    x08-p2-skip30="P2 with a bound of 30 s (= P4)" x08-p2-skip30-r2="P4; second run" x08-p2-skip100="P2 with a bound of 100 s"
fam $B/X08 x08-c61 x08b-base="stock (c61)" x08b-skip="bypass alone; 3 s" x08b-tokfast12="v1.2 (P1 without blkfirst)" x08b-p1-a20="P1 + starvation bound 20 s" x08b-p2-sync="P2 + synchronous scheduling"
fam $B/X08 x08c-conv x08c-conv-base="stock (c60)" x08c-conv-p2=P2 x08c-conv-p2-skip30=P4
# --- 16 GB nodes, Experiment E and the 80 GB capacity point
fam $B/E e-tool04-80-p7456 e-tool04-80-p7456-base="stock (c61)" e-tool04-80-p7456-priohits="oracle hits-first priority" e-tool04-80-p7456-p1=P1 e-tool04-80-p7456-p4=P4
fam $B/E e66-tool04-80-p7456 e66-tool04-80-p7456-base="stock (c66)" e66-tool04-80-p7456-skip30="bypass alone; 30 s" e66-tool04-80-p7456-p4=P4
fam $B/E e-tool04-80-big e-tool04-80-big-base=stock e-tool04-80-big-p1=P1 e-tool04-80-big-p1-sync="P1 + synchronous scheduling"
fam $B/E e7-tool02-80 e7-tool02-80-base=stock e7-tool02-80-p1=P1
fam $B/E e-tool08-120-big e-tool08-120-big-base=stock e-tool08-120-big-p1=P1
