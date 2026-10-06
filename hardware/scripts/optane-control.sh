#!/usr/bin/env bash
#SBATCH -p cascade
#SBATCH -N 1
#SBATCH -t 01:30:00
#SBATCH -J optane-control
#SBATCH -o /home/ghu4/CXL/experimental_results/2026-10-06-optane-control/slurm-%j.out
# Optane control for the paper's "why not persistent memory" question (c35/c36: Cascade Lake, DDR4, 1 TB Optane as
# KMEM-DAX NUMA nodes). Three questions: how fast can PM absorb NT writes (vs threads)? does a write stream redirected
# from DRAM to PM free the DRAM reader, the way it does on CXL? and how fast are PM reads? Same membench as the
# 2026-09-08 DRAM write-drain matrix; reader = 4T stream-read on the DRAM node, cpus 0-3; writers on cpus 4.. of the
# same socket; buffers on the DRAM node or on the PM node attached to that socket. Data pattern: membench writes a
# non-zero constant (data-carrying lines).
set -u
cd /home/ghu4/CXL
OUT=experimental_results/2026-10-06-optane-control; mkdir -p $OUT
{ date; hostname; numactl -H; lscpu | grep -E "Model name|Socket|NUMA|Thread|Core"; cat /sys/bus/dax/devices/*/mode 2>/dev/null; ls /sys/bus/node/devices/ ; } > $OUT/machine-state.txt 2>&1
B=$OUT/membench-cascade
gcc -O3 -g -Wall -march=native -pthread benchmarks/memory/membench.c -o $B -lnuma || { echo "build failed" >&2; exit 1; }
# DRAM node 0; PM node = the CPU-less node with the smallest distance to node 0
PM=$(python3 - <<'PY'
import subprocess, re
out = subprocess.run(["numactl", "-H"], capture_output=True, text=True).stdout
cpuless = [int(m.group(1)) for m in re.finditer(r"node (\d+) cpus:\s*\n", out)]
dist = {}
rows = out[out.index("node distances"):].splitlines()[2:]
for r in rows:
    if ":" in r:
        n = int(r.split(":")[0]); dist[n] = [int(x) for x in r.split(":")[1].split()]
cand = [(dist[0][n], n) for n in cpuless if n in dist[0] or True] if dist else []
cand = [(dist[0][n], n) for n in cpuless]
print(min(cand)[1] if cand else 2)
PY
)
echo "DRAM node 0, PM node $PM" | tee -a $OUT/machine-state.txt
D=4; AGG_D=10; REPS=3
HDR="tag,node,mode,threads,size_per_thread_bytes,read_pct,duration_sec,total_bytes,bandwidth_gib_s,avg_latency_ns,victim_latency_ns,aggressor_bandwidth_gib_s,total_bandwidth_gib_s,rep"
MAT=$OUT/matrix.csv; AGG=$OUT/aggressor.csv; ERR=$OUT/stderr.log
echo "$HDR" > $MAT; echo "$HDR" > $AGG
reader() { row=$($B --mode=stream-read --node=0 --threads=4 --cpu-offset=0 --duration=$D --tag="$1" --csv 2>>$ERR); echo "$row,$rep" >> $MAT; }
writer_bg() { $B --mode="$1" --node=$2 --threads="$3" --cpu-offset=4 --duration="$5" --tag="$4" --csv 2>>$ERR | sed "s/\$/,$rep/" >> $AGG & AGGPID=$!; }
for rep in $(seq 1 $REPS); do
  echo "=== rep $rep $(date +%T) ==="
  reader "ro-idle"
  # PM and DRAM write-only capacity vs threads, NT and plain stores; PM read capacity
  for node in $PM 0; do
    for W in 1 2 4 8 16; do
      writer_bg stream-write-nt $node $W "wo-nt-node$node-w$W" $D; wait $AGGPID
      writer_bg stream-write $node $W "wo-plain-node$node-w$W" $D; wait $AGGPID
    done
    row=$($B --mode=stream-read --node=$node --threads=8 --cpu-offset=4 --duration=$D --tag="ro-node$node-t8" --csv 2>>$ERR); echo "$row,$rep" >> $MAT
  done
  # the reader beside writers: into DRAM vs into PM, 4 / 8 / 16 writer threads, NT and plain
  for node in 0 $PM; do
    for W in 4 8 16; do
      for mode in stream-write-nt stream-write; do
        writer_bg $mode $node $W "rw-$mode-node$node-w$W" $AGG_D; sleep 2.5
        reader "rw-$mode-node$node-w$W"; wait $AGGPID
      done
    done
  done
done
echo "DONE $(date +%T)" | tee -a $OUT/progress.txt
