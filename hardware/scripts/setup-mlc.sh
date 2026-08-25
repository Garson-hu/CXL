#!/usr/bin/env bash
# Locate Intel MLC or print instructions to install it.
# Run this BEFORE mlc-sweep.sh so you don't burn salloc time on missing deps.
set -u

# 1. Already in PATH?
if command -v mlc >/dev/null 2>&1; then
  echo "mlc found: $(command -v mlc)"
  mlc --help 2>&1 | head -3
  exit 0
fi

# 2. Common alternative locations
for cand in /opt/mlc/Linux/mlc /usr/local/bin/mlc "$HOME/mlc/Linux/mlc" "$HOME/bin/mlc"; do
  if [[ -x "$cand" ]]; then
    echo "mlc found at $cand — add to PATH with:"
    echo "    export PATH=\"$(dirname "$cand"):\$PATH\""
    exit 0
  fi
done

# 3. Not found — tell the user how to get it
cat <<'EOF'
mlc NOT FOUND.

Intel MLC is a free binary but requires accepting Intel's EULA. Download manually:

    https://www.intel.com/content/www/us/en/download/736633/intel-memory-latency-checker-intel-mlc.html

After download:

    mkdir -p ~/mlc && cd ~/mlc
    tar xf <downloaded-tarball>
    export PATH="$HOME/mlc/Linux:$PATH"
    mlc --help        # should print usage

Then re-run this script to confirm.

Fallback if MLC is blocked: use `numactl --membind` + a simple bandwidth test
(STREAM, `sysbench memory`, or a small C loop). Less precise but workable.
EOF
exit 1
