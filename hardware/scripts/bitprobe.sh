#!/usr/bin/env bash
# Probe which address bit (if any) selects a card, on a devdax window.
CP=benchmarks/memory/cxlprobe; T=/tmp/claude-412504/-home-ghu4-CXL/08b11bc0-e9a5-4c10-9317-554894de6271/scratchpad
solo() { $CP --mode=daxstride --dax=$1 --dax-offset=$2 --size=4G --threads=8 --secs=3 \
         --stride=$3 --chunk=$4 --offset=$5 --cpu-offset=0 --tag=s 2>/dev/null | grep -o 'bw=[0-9.]*' | cut -d= -f2; }
corun() { # dax offA strideA chunkA clsA offB strideB chunkB clsB
  $CP --mode=daxstride --dax=$1 --dax-offset=$2 --size=4G --threads=8 --secs=4 \
      --stride=$3 --chunk=$4 --offset=$5 --cpu-offset=0  --tag=A 2>/dev/null | grep -o 'bw=[0-9.]*' | cut -d= -f2 > $T/.A &
  P1=$!
  $CP --mode=daxstride --dax=$1 --dax-offset=$6 --size=4G --threads=8 --secs=4 \
      --stride=$7 --chunk=$8 --offset=$9 --cpu-offset=16 --tag=B 2>/dev/null | grep -o 'bw=[0-9.]*' | cut -d= -f2 > $T/.B &
  P2=$!
  wait $P1 $P2
  python3 -c "a=$(cat $T/.A); b=$(cat $T/.B); print(f'{a:5.1f} + {b:5.1f} = {a+b:5.1f}')"
}
D=$1; NAME=$2
echo "=== $NAME  ($D) ==="
echo "  full window, all chunks, 8T : $(solo $D 32G 256 256 0) GiB/s"
echo "  full window, all chunks,16T : $($CP --mode=daxstream --dax=$D --dax-offset=32G --size=8G --threads=16 --secs=3 --tag=s 2>/dev/null | grep -o 'bw=[0-9.]*' | cut -d= -f2) GiB/s"
echo "  --- single-bit class selection (solo bw; ~half of full = bit isolates a card) ---"
for b in 8 9 10 11 12 14 16; do
  ch=$((1<<b)); st=$((ch*2))
  [ $st -gt 2097152 ] && continue
  lo=$(solo $D 32G $st $ch 0); hi=$(solo $D 32G $st $ch $ch)
  printf "  bit %-2s (chunk %7s B): class0=%5s  class1=%5s GiB/s\n" $b $ch $lo $hi
done
