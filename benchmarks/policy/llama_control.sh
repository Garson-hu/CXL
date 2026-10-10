#!/bin/bash
# Control for the drift of llama.cpp's token rate (2026-10-10): llama_victim alone (80 threads, cpus 0-79, no server,
# no other load) for <seconds>, so its time per token can be compared with a run beside a workload at the same
# number of generated tokens.  usage: llama_control.sh <out_file> [seconds=720]
python3 "$(dirname "$0")/llama_victim.py" 80 0-79 100000 > "$1" 2>&1 &
pid=$!; sleep "${2:-720}"; kill -TERM $pid; wait $pid
