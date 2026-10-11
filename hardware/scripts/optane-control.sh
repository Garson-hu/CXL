#!/usr/bin/env bash
#SBATCH -p cascade
#SBATCH -N 1
#SBATCH -t 01:30:00
#SBATCH -J optane-control
#SBATCH -o /home/ghu4/CXL/experimental_results/2026-10-06-optane-control/slurm-%j.out
# Optane control for the paper's "why not persistent memory" question (c35/c36: Cascade Lake, DDR4, 1 TB Optane as
# KMEM-DAX NUMA nodes). Three questions: how fast can PM absorb NT writes (vs threads)? does a write stream redirected
# from DRAM to PM free the DRAM reader, the way it does on CXL? and how fast are PM reads? Same membench as the
# 2026-09-08 DRAM write-drain matrix; reader = 4T stream-read on the DRAM node DN, its first 4 cpus; writers on its
# other cpus; buffers on the DRAM node or on the PM node attached to that socket. Data pattern: membench writes a
# non-zero constant (data-carrying lines).
set -u
cd /home/ghu4/CXL
OUT=experimental_results/2026-10-06-optane-control; mkdir -p $OUT
{ date; hostname; numactl -H; lscpu | grep -E "Model name|Socket|NUMA|Thread|Core"; cat /sys/bus/dax/devices/*/mode 2>/dev/null; ls /sys/bus/node/devices/ ; } > $OUT/machine-state.txt 2>&1
B=$OUT/membench-cascade
gcc -O3 -g -Wall -march=native -pthread benchmarks/memory/membench.c -o $B -lnuma || { echo "build failed" >&2; exit 1; }
# PM node = the CPU-less node; DRAM node DN = the CPU node closest to it (the socket the PM DIMMs share channels with).
# (2026-10-11: attempt 1 read the distance table by position and failed on c35's node ids 0,1,3; it then measured
#  socket 0 only. Reader, writers and DRAM buffers now all sit on the PM's socket.)
read PM DN < <(python3 - <<'PY'
import subprocess, re
out = subprocess.run(["numactl", "-H"], capture_output=True, text=True).stdout
cpuless = [int(m.group(1)) for m in re.finditer(r"node (\d+) cpus:[ \t]*\n", out)]
withcpu = [int(m.group(1)) for m in re.finditer(r"node (\d+) cpus:[ \t]*\d", out)]
lines = out[out.index("node distances"):].splitlines()
cols = [int(x) for x in lines[1].split()[1:]]
dist = {int(r.split(":")[0]): dict(zip(cols, (int(x) for x in r.split(":")[1].split()))) for r in lines[2:] if ":" in r}
pm = cpuless[0]
print(pm, min(withcpu, key=lambda n: dist[n][pm]))
PY
)
echo "PM node $PM, DRAM node $DN (CPUs of node $DN run reader and writers)" | tee -a $OUT/machine-state.txt
D=4; AGG_D=10; REPS=3
HDR="tag,node,mode,threads,size_per_thread_bytes,read_pct,duration_sec,total_bytes,bandwidth_gib_s,avg_latency_ns,victim_latency_ns,aggressor_bandwidth_gib_s,total_bandwidth_gib_s,rep"
MAT=$OUT/matrix.csv; AGG=$OUT/aggressor.csv; ERR=$OUT/stderr.log
echo "$HDR" > $MAT; echo "$HDR" > $AGG
reader() { row=$($B --mode=stream-read --node=$DN --cpu-node=$DN --threads=4 --cpu-offset=0 --duration=$D --tag="$1" --csv 2>>$ERR); echo "$row,$rep" >> $MAT; }
writer_bg() { $B --mode="$1" --node=$2 --cpu-node=$DN --threads="$3" --cpu-offset=4 --duration="$5" --tag="$4" --csv 2>>$ERR | sed "s/\$/,$rep/" >> $AGG & AGGPID=$!; }
for rep in $(seq 1 $REPS); do
  echo "=== rep $rep $(date +%T) ==="
  reader "ro-idle"
  # PM and DRAM write-only capacity vs threads, NT and plain stores; PM read capacity
  for node in $PM $DN; do
    for W in 1 2 4 8; do
      writer_bg stream-write-nt $node $W "wo-nt-node$node-w$W" $D; wait $AGGPID
      writer_bg stream-write $node $W "wo-plain-node$node-w$W" $D; wait $AGGPID
    done
    row=$($B --mode=stream-read --node=$node --cpu-node=$DN --threads=8 --cpu-offset=4 --duration=$D --tag="ro-node$node-t8" --csv 2>>$ERR); echo "$row,$rep" >> $MAT
  done
  # the reader beside writers: into DRAM vs into PM, 4 / 8 / 16 writer threads, NT and plain
  for node in $DN $PM; do
    for W in 1 2 4; do                                     # 8 cores per socket: 4 reader + up to 4 writers
      for mode in stream-write-nt stream-write; do
        writer_bg $mode $node $W "rw-$mode-node$node-w$W" $AGG_D; sleep 2.5
        reader "rw-$mode-node$node-w$W"; wait $AGGPID
      done
    done
  done
done
echo "DONE $(date +%T)" | tee -a $OUT/progress.txt
