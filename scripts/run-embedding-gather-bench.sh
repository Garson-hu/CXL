#!/usr/bin/env bash
# run-embedding-gather-bench.sh — embedding gather sweep across placements
# and access distributions. Output: benchmarks/results/<timestamp>-embedding/
set -u

ROOT=$(cd "$(dirname "$0")/.." && pwd)
PY="$ROOT/benchmarks/embedding/embbench.py"

TS=$(date +%Y-%m-%d-%H-%M-%S)
OUT="$ROOT/benchmarks/results/${TS}-embedding"
mkdir -p "$OUT"

PLACES=(dram)
"$ROOT/scripts/check-cxl-memory.sh" 1 >/dev/null 2>&1 && PLACES+=(cxl interleave skew)

# Default sweep — ~5 GiB table (small enough to also fit DRAM for a comparison).
# To exercise CXL-resident only, bump --rows.
ROWS=10000000
ROW_DIM=128
BATCH=4096
STEPS=200

first=1
for place in "${PLACES[@]}"; do
  for dist in uniform zipf; do
    tag="${place}-${dist}"
    [[ "$first" == "1" ]] && tag="header:${tag}"
    python3 "$PY" \
      --rows="$ROWS" --row-dim="$ROW_DIM" --batch="$BATCH" --steps="$STEPS" \
      --dist="$dist" --place="$place" --tag="$tag" --csv \
      >> "$OUT/embbench.csv" 2>>"$OUT/run.log"
    first=0
  done
done

{
  echo "=== date ==="; date
  echo "=== numactl --hardware ==="; numactl --hardware
} > "$OUT/env.log"

echo "done. results in $OUT"
