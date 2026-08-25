#!/usr/bin/env bash
# check-cxl-memory.sh — verify NUMA node 1 (CXL) is online with capacity.
# Returns 0 if ready, non-zero with actionable message if not.
set -u

REQUIRED_NODE=${1:-1}

if ! command -v numactl >/dev/null 2>&1; then
  echo "ERROR: numactl not installed."
  exit 10
fi

# Find node 1 line in numactl --hardware
size_line=$(numactl --hardware | awk -v n="$REQUIRED_NODE" '$1=="node" && $2==n && $3=="size:"')
if [[ -z "$size_line" ]]; then
  echo "ERROR: NUMA node $REQUIRED_NODE is not registered."
  echo "  numactl --hardware shows:"
  numactl --hardware | grep -E '^(available|node)' | head -10
  exit 11
fi

# Parse "node 1 size: NNNN MB"
size_mb=$(echo "$size_line" | awk '{print $4}')
if [[ "$size_mb" -le 0 ]]; then
  cat <<EOF
ERROR: NUMA node $REQUIRED_NODE is registered but has 0 MB online memory.

This is the known c28 blocker. Ask the admin to run:

    sudo daxctl online-memory dax2.0

Then re-check with:

    numactl --hardware
    cat /sys/devices/system/node/node$REQUIRED_NODE/meminfo

(If only dax2.0 was converted to system-ram, dax0.0 and dax1.0 are still
FAMFS-mounted; do not ask admin to touch them without coordinating.)
EOF
  exit 12
fi

echo "OK: NUMA node $REQUIRED_NODE has $size_mb MB online."
echo "    distances:"
numactl --hardware | sed -n '/^node distances/,$p' | head -10
exit 0
