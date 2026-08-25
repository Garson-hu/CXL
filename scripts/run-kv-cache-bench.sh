#!/usr/bin/env bash
# run-kv-cache-bench.sh — sweep KV-cache-shape benchmark across placements.
# Output: benchmarks/results/<timestamp>-kvcache/*.csv
set -u

ROOT=$(cd "$(dirname "$0")/.." && pwd)
PY="$ROOT/benchmarks/kvcache/kvbench.py"

TS=$(date +%Y-%m-%d-%H-%M-%S)
OUT="$ROOT/benchmarks/results/${TS}-kvcache"
mkdir -p "$OUT"

PLACES=(dram)
"$ROOT/scripts/check-cxl-memory.sh" 1 >/dev/null 2>&1 && PLACES+=(cxl interleave split)

# Model-ish defaults: Llama-3-8B-shape KV cache
LAYERS=32
HEADS=32
HEAD_DIM=128
SEQ=2048
BATCH=1
TOKENS=64

first=1
for place in "${PLACES[@]}"; do
  tag="$place"
  [[ "$first" == "1" ]] && tag="header:${tag}"
  python3 "$PY" \
    --layers="$LAYERS" --heads="$HEADS" --head-dim="$HEAD_DIM" \
    --seq-len="$SEQ" --batch="$BATCH" --tokens="$TOKENS" \
    --place="$place" --tag="$tag" --csv \
    >> "$OUT/kvbench.csv" 2>>"$OUT/run.log"
  first=0
done

{
  echo "=== date ==="; date
  echo "=== numactl --hardware ==="; numactl --hardware
} > "$OUT/env.log"

echo "done. results in $OUT"
