#!/usr/bin/env bash
# Where does CXL interleaving still happen? Walks the decoder chain, resolves
# every target to a real PCI device, then proves the answer with a live
# bandwidth test on Pair B. Read-only; safe to run any time, by anyone.
cd "$(dirname "$0")/../.." 2>/dev/null
CXL=/sys/bus/cxl/devices
echo "=========================================================="
echo " CXL interleave status — $(hostname) — $(date '+%F %T')"
echo " booted: $(uptime -s)   (BIOS changes only take effect after a reboot)"
echo "=========================================================="

# resolve a decoder's target_list ids into PCI names, using its parent's dports
targets() {  # $1 = parent dir, $2 = comma list
  local out=""
  for id in ${2//,/ }; do
    local l="$1/dport$id"
    [ -e "$l" ] && out="$out $(basename $(readlink -f $l))" || out="$out dport$id"
  done
  echo "$out"
}

for lvl in 1 2 3; do
  case $lvl in
    1) echo; echo "LEVEL 1 — ROOT / CFMWS decoders: which HOST BRIDGE serves an address?";;
    2) echo; echo "LEVEL 2 — HOST-BRIDGE decoders: which ROOT PORT (= which CARD)?";;
    3) echo; echo "LEVEL 3 — ENDPOINT decoders: address translation inside a card";;
  esac
  for d in $CXL/decoder*; do
    p=$(dirname $(readlink -f $d)); pn=$(basename $p)
    case $pn in
      root0)      [ $lvl -eq 1 ] || continue;;
      port*)      [ $lvl -eq 2 ] || continue;;
      endpoint*)  [ $lvl -eq 3 ] || continue;;
      *) continue;;
    esac
    w=$(cat $d/interleave_ways 2>/dev/null); g=$(cat $d/interleave_granularity 2>/dev/null)
    sz=$(cat $d/size 2>/dev/null); tl=$(cat $d/target_list 2>/dev/null)
    lk=$(cat $d/locked 2>/dev/null)
    gib=$(( ${sz:-0} / 1073741824 ))
    [ "$gib" = "0" ] && continue
    printf "  %-11s %5d GiB  ways=%s gran=%s%s" "$(basename $d)" "$gib" "${w:-?}" "${g:-?}" "$([ "$lk" = "1" ] && echo ' locked')"
    [ -n "$tl" ] && printf "  ->%s" "$(targets $p "$tl")"
    if [ "${w:-1}" -gt 1 ] 2>/dev/null; then echo "   *** INTERLEAVED ***"; else echo "   (no interleave)"; fi
  done
done

echo; echo "FUNCTIONAL TEST (ground truth, ignores sysfs) — Pair B via /dev/dax2.0"
CP=benchmarks/memory/cxlprobe
if [ -r /dev/dax2.0 ] && [ -x "$CP" ] && [ "$(daxctl list -u 2>/dev/null | grep -A5 dax2.0 | grep -c devdax)" != "0" ]; then
  run() { $CP --mode=daxstride --dax=/dev/dax2.0 --dax-offset=$1 --size=4G --threads=8 \
          --secs=3 --stride=512 --chunk=256 --offset=$2 --cpu-offset=$3 --tag=$4 2>/dev/null \
          | grep -o 'bw=[0-9.]*' | cut -d= -f2; }
  run 64G 0 0 a > /tmp/.ck_a & run 200G 0 16 b > /tmp/.ck_b & wait
  A=$(cat /tmp/.ck_a); B=$(cat /tmp/.ck_b); rm -f /tmp/.ck_a /tmp/.ck_b
  SUM=$(python3 -c "print(f'{$A+$B:.1f}')")
  echo "  two streams, BOTH on even 256B chunks: $A + $B = $SUM GiB/s"
  VERDICT=$(python3 -c "print('STILL INTERLEAVED (they share one card)' if $SUM < 32 else 'NOT interleaved (they used two cards)')")
  echo "  -> $VERDICT"
  echo "     (~24 GiB/s = one card shared => 256B stripe active;"
  echo "      ~45+ GiB/s = separate cards => interleave really off)"
else
  echo "  skipped (needs /dev/dax2.0 readable and in devdax mode)"
fi
echo; echo "WHAT TO LOOK FOR: per-card memory needs ways=1 at BOTH level 1 and level 2."
