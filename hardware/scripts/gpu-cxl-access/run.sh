#!/bin/bash
# Build and run the GPU <-> CXL access test on c28 (2026-11-12). See the header of gpu_cxl.cu for what each step shows.
# Preconditions: /dev/dax0.0 is root:kmem 0660 and you are in kmem; no vLLM / LMCache / other job uses the GPU or the CXL
# devices; nothing needs bytes [240 GiB, 240 GiB + 256 MiB) of /dev/dax0.0 (242.5 GiB) -- the test overwrites them.
# usage: hardware/scripts/gpu-cxl-access/run.sh | tee hardware/results/$(date +%F)-gpu-cxl-access.log
set -u
cd "$(dirname "$0")" || exit 1
gcc -O2 -Wall -o cxl_cpu cxl_cpu.c || exit 1
/usr/local/cuda/bin/nvcc -O2 -arch=sm_89 -o gpu_cxl gpu_cxl.cu || exit 1
DEV=/dev/dax0.0; OFF=$((240 * 1024)); LEN=256        # offset and length in MiB
echo "# $(date '+%F %T') $(hostname)  dev=$DEV offset=${OFF}MiB len=${LEN}MiB"
./gpu_cxl $DEV $OFF $LEN;         echo "# exit $?"; echo
./gpu_cxl $DEV $OFF $LEN --noreg; echo "# exit $?"
