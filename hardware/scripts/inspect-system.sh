#!/usr/bin/env bash
# c28 system inspection. Output captured to stdout; redirect to hardware/results/.
set -u
echo "=== date ==="; date
echo "=== hostname ==="; hostname
echo
echo "=== nvidia-smi ==="; nvidia-smi 2>&1 || echo "(no nvidia-smi / no GPUs)"
echo
echo "=== lscpu ==="; lscpu
echo
echo "=== free -h ==="; free -h
echo
echo "=== numactl --hardware ==="; numactl --hardware
echo
echo "=== /proc/cmdline ==="; cat /proc/cmdline
echo
echo "=== /sys/bus/cxl/devices/ ==="; ls -la /sys/bus/cxl/devices/ 2>&1 || echo "(no /sys/bus/cxl)"
echo
echo "=== dmesg | grep -i cxl ==="; dmesg 2>/dev/null | grep -i cxl | head -200
echo
echo "=== lspci CXL ==="; lspci | grep -iE 'cxl|cz120|micron' || echo "(no CXL devices visible via lspci)"
echo
echo "=== kernel ==="; uname -a
echo
echo "=== /sys/devices/system/node ==="; ls /sys/devices/system/node/ | grep '^node'
