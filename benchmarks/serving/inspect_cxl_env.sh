#!/usr/bin/env bash
# Environment record of the CXL-vs-NVMe serving study (2026-11-12): read-only inspection of c28 (CPU, DRAM, GPU and its PCIe link,
# NVMe device / file system / mount options, CXL topology: memdevs, decoders, regions, DAX devices, permissions, current users,
# software versions). Nothing is reconfigured. usage: inspect_cxl_env.sh > <results>/env/inspect-<date>.txt
set -u
PY=/mnt/local/ghu4/envs/lmcache/bin/python
h() { echo; echo "===== $* ====="; }
h "node / time"; hostname; date -Is; uname -r
h "slurm allocation"; squeue -u "$USER" -o "%i %P %j %T %M %l %e %R" 2>/dev/null
h "CPU"; lscpu | grep -E "Model name|Socket|Core|Thread|^CPU\(s\)|NUMA|L3|MHz" 
h "memory"; free -g | head -2; numactl --hardware 2>/dev/null; grep -E "MemTotal|MemFree|MemAvailable|Cached|Shmem:|HugePages_Total|Hugepagesize" /proc/meminfo
h "kernel command line"; cat /proc/cmdline
h "GPU"; nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,pcie.link.gen.current,pcie.link.gen.max,pcie.link.width.current,pcie.link.width.max --format=csv
GPUBDF=$(nvidia-smi --query-gpu=pci.bus_id --format=csv,noheader | head -1 | sed 's/^0000//' | tr 'A-Z' 'a-z')
echo "GPU PCI address: $GPUBDF"; lspci -s "${GPUBDF#:}" -vv 2>/dev/null | grep -E "LnkCap:|LnkSta:" 
h "NVMe"; lsblk -o NAME,MODEL,SIZE,TYPE,MOUNTPOINT,FSTYPE,SCHED,ROTA /dev/nvme1n1 2>/dev/null; findmnt -no SOURCE,FSTYPE,OPTIONS /mnt/local; df -h /mnt/local | tail -1
for f in queue/scheduler queue/nr_requests queue/read_ahead_kb queue/max_sectors_kb queue/logical_block_size queue/physical_block_size queue/write_cache; do echo "nvme1n1/$f: $(cat /sys/block/nvme1n1/$f 2>/dev/null)"; done
cat /sys/class/nvme/nvme1/model /sys/class/nvme/nvme1/firmware_rev 2>/dev/null; echo "NVMe PCIe link: current $(cat /sys/class/nvme/nvme1/device/current_link_speed) x$(cat /sys/class/nvme/nvme1/device/current_link_width), max $(cat /sys/class/nvme/nvme1/device/max_link_speed) x$(cat /sys/class/nvme/nvme1/device/max_link_width)"
h "DAX devices: permissions"; ls -l /dev/dax*; id
h "daxctl list -RDM"; daxctl list -RDM 2>&1
h "cxl list -MRDu (memdevs, regions, decoders)"; cxl list -M -u 2>&1; cxl list -R -u 2>&1; cxl list -D -u 2>&1 | head -150
h "sysfs: DAX devices"
for d in /sys/bus/dax/devices/dax*; do n=$(basename "$d"); echo "$n size=$(cat "$d/size") align=$(cat "$d/align" 2>/dev/null) target_node=$(cat "$d/target_node" 2>/dev/null) resource=$(cat "$d/resource" 2>/dev/null) driver=$(basename "$(readlink -f "$d/driver")") parent=$(basename "$(readlink -f "$d/..")")"; done
h "sysfs: CXL decoders (interleave)"
for d in /sys/bus/cxl/devices/decoder*; do n=$(basename "$d"); echo "$n ways=$(cat "$d/interleave_ways" 2>/dev/null) gran=$(cat "$d/interleave_granularity" 2>/dev/null) start=$(cat "$d/start" 2>/dev/null) size=$(cat "$d/size" 2>/dev/null) targets=$(cat "$d/target_list" 2>/dev/null) mode=$(cat "$d/mode" 2>/dev/null) region=$(cat "$d/region" 2>/dev/null)"; done
h "CXL memdevs (PCI)"; for m in /sys/bus/cxl/devices/mem*; do echo "$(basename "$m") -> $(basename "$(readlink -f "$m/..")") serial=$(cat "$m/serial" 2>/dev/null) ram=$(cat "$m/ram/size" 2>/dev/null) numa=$(cat "$m/numa_node" 2>/dev/null)"; done
lspci 2>/dev/null | grep -i -E "cxl|0502|Micron|Montage" | head
h "/proc/iomem (CXL / dax ranges; needs root for addresses)"; grep -i -E "cxl|dax|soft reserved" /proc/iomem | head -20
h "mounts that involve dax / famfs (not touched by this study)"; findmnt -t famfs,fuse.famfs 2>/dev/null; grep -E "dax|famfs" /proc/mounts
h "current users of the DAX devices (own processes visible only)"; for d in dax0.0 dax1.0 dax2.0; do echo "$d: $(grep -l "/dev/$d" /proc/[0-9]*/maps 2>/dev/null | tr '\n' ' ')"; done
h "software"; $PY - <<'PYV'
import importlib.metadata as m, sys
print("python", sys.version.split()[0])
for p in ("vllm", "lmcache", "torch", "transformers", "aiofiles", "numpy"):
    try: print(p, m.version(p))
    except Exception as e: print(p, "?", e)
import torch; print("torch cuda", torch.version.cuda, "cudnn", torch.backends.cudnn.version())
PYV
git -C /home/ghu4/CXL log --oneline -1; git -C /home/ghu4/CXL branch --show-current
