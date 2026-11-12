#!/usr/bin/env bash
# GPU memory used by the LMCache server alone as a function of the host memory it registers with CUDA (cudaHostRegister of the pinned
# DRAM L1 and of the Device-DAX L1 arenas). CXL-vs-NVMe study, 2026-11-12. No vLLM, no requests: the server is started, the GPU's
# used memory is read once it is healthy, the server is stopped. usage: vram_registered.sh > <results>/env/vram-registered.txt
B=/mnt/local/ghu4/envs/lmcache/bin; export HF_HOME=/mnt/local/ghu4/hf LMCACHE_DISABLE_BANNER=1 TMPDIR=/mnt/local/ghu4/tmp
one() { # label, then lmcache server args
  label=$1; shift; before=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
  taskset -c 120-127 $B/lmcache server --host 127.0.0.1 --port 5555 --http-host 127.0.0.1 --http-port 8200 --chunk-size 256 --eviction-policy LRU --max-gpu-workers 1 --max-cpu-workers 1 --supported-transfer-mode lmcache_driven "$@" > /tmp/vram-$$.log 2>&1 &
  pid=$!; t0=$(date +%s.%N)
  for i in $(seq 1 600); do curl -s -o /dev/null http://127.0.0.1:8200/healthcheck && break; sleep 0.5; kill -0 $pid 2>/dev/null || break; done
  t1=$(date +%s.%N); sleep 2
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits); proc=$(nvidia-smi --query-compute-apps=used_memory --format=csv,noheader,nounits | head -1)
  rss=$(awk '/VmRSS/{print $2}' /proc/$pid/status 2>/dev/null)
  echo "$label | GPU used before ${before} MiB, with the server ${used} MiB (process entry ${proc} MiB) | start-up $(echo "$t1 - $t0" | bc | cut -c1-5) s | RSS $((rss / 1024)) MiB"
  kill -INT $pid; wait $pid 2>/dev/null; sleep 2; rm -f /tmp/vram-$$.log
}
echo "# $(date -Is) $(hostname) GPU $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)"
one "DRAM L1 8 GiB"                 --l1-size-gb 8
one "DRAM L1 80 GiB"                --l1-size-gb 80
one "DRAM L1 160 GiB"               --l1-size-gb 160
one "DRAM L1 320 GiB"               --l1-size-gb 320
one "Device-DAX L1 80 GiB (dax1.0)"  --l1-size-gb 80 --l1-devdax-path /dev/dax1.0 --no-l1-use-lazy --shm-name ""
one "Device-DAX L1 269.5 GiB (dax1.0)" --l1-size-gb 269.5 --l1-devdax-path /dev/dax1.0 --no-l1-use-lazy --shm-name ""
one "hybrid: DRAM 80 GiB + dax1.0 269.5 GiB" --l1-size-gb 80 --l1-devdax-path /dev/dax1.0 --no-l1-use-lazy --shm-name "" --l2-adapter '{"type":"dax","slot_bytes":9437184,"devices":[{"device_path":"/dev/dax1.0","max_dax_size_gb":269.5}]}'
one "DRAM L1 80 GiB + DAX L2 512 GiB (not registered)" --l1-size-gb 80 --l2-adapter '{"type":"dax","slot_bytes":9437184,"devices":[{"device_path":"/dev/dax1.0","max_dax_size_gb":269.5},{"device_path":"/dev/dax0.0","max_dax_size_gb":242.5}]}'
