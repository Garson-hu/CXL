#!/bin/bash
# B1 gate, second half: NO system call between the two markers, i.e. on the path
# reserve -> copy_to -> commit -> release, including claiming new segments on CXL and DRAM.
out=$(mktemp); strace -f -o "$out" build/test_policy --datapath 2>/dev/null
n=$(awk '/DATAPATH-BEGIN/{on=1;next} /DATAPATH-END/{on=0} on' "$out" | wc -l)
tot=$(wc -l < "$out")
echo "  strace: $tot syscalls in the whole run, $n between the data-path markers (320 reservations, 2.5 GiB copied)"
awk '/DATAPATH-BEGIN/{on=1;next} /DATAPATH-END/{on=0} on' "$out" | head -5
rm -f "$out"; [ "$n" -eq 0 ] && echo PASS || { echo FAIL; exit 1; }
