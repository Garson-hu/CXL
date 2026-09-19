#!/usr/bin/env bash
# E3 live gate: Mooncake traces replayed through the KV stand-in with a real cxlpathd (so the read
# path counts reads and promotes hot blocks while the trace runs). Every hit is verified word by word.
# usage: e3_kv.sh <outdir>
set -u; OUT=$1; mkdir -p "$OUT"; cd "$(dirname "$0")/../.."; B=$PWD/build; W=$PWD/../../workloads; FAILS=0
CXLP_OBJ_SLOTS=65536 $B/cxlp_mkstore kv 8192 2048 /dev/dax0.0 /dev/dax1.0 | sed 's/^/    /'
$B/cxlpathd kv --cpu 16 --log $OUT/E3-daemon.csv & DPID=$!; for i in $(seq 100); do sleep 0.05; $B/cxlp_admin kv view 2>/dev/null | grep -q alive=1 && break; done
for t in conversation toolagent synthetic; do
  echo "  trace $t (4 MiB per block, first 4000 requests, KV layer capacity 12 GiB of the 16 GiB CXL)"
  $B/cxlp_kv_replay kv $W/mooncake_${t}_trace.jsonl 4096 4000 12 > $OUT/E3-$t.txt; R=$?; sed 's/^/    /' $OUT/E3-$t.txt | head -3
  [ $R = 0 ] && echo "  ok   $t: every hit byte-exact, no failed store" || { echo "  FAIL $t"; FAILS=$((FAILS+1)); }
  sleep 1
done
$B/cxlp_admin kv view | sed 's/^/    /'
FREE=$($B/cxlp_admin kv view | awk '/^dev/{split($5,a,"/"); f+=a[1]; t+=a[2]} END{print f"/"t}')
[ "${FREE%/*}" = "${FREE#*/}" ] && echo "  ok   all segments free after the three replays ($FREE)" || { echo "  FAIL segments left: $FREE"; FAILS=$((FAILS+1)); }
kill -TERM $DPID; wait $DPID 2>/dev/null; $B/cxlp_admin kv destroy
[ $FAILS = 0 ] && echo PASS || echo "FAIL ($FAILS)"; exit $FAILS
