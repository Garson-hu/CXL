#!/bin/bash
#SBATCH -p a100
#SBATCH -w c33
#SBATCH -t 06:00:00
#SBATCH -c 16
#SBATCH -J cf-pilot
#SBATCH -o /home/ghu4/CXL/experimental_results/2026-10-27-reuse-window-prefetch/train/pilot-%j.out
module load cuda 2>/dev/null
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}
PY=/home/ghu4/hvac/rlibrary/miniconda3/envs/hvac_tf/bin/python
O=/home/ghu4/CXL/experimental_results/2026-10-27-reuse-window-prefetch/train
hostname; nvidia-smi -L; free -g | head -2
# cold parallel-file-system read bandwidth from this node (test split of the full dataset, files 3000..): 1 / 4 / 8 / 16 / 32 streams
$PY - <<'PYEOF'
import os, time, threading
D = "/mnt/beegfs/ghu4/hvac/cosmoUniverse_2019_05_4parE_tf_v2/test"; names = sorted(os.listdir(D))[3000:]
def rd(files, acc):
    n = 0
    for f in files:
        with open(os.path.join(D, f), "rb") as fh:
            while True:
                b = fh.read(1 << 20)
                if not b: break
                n += len(b)
    acc.append(n)
pos = 0; out = []
for streams in (1, 4, 8, 16, 32):
    per = 480 // streams; groups = [names[pos + i * per: pos + (i + 1) * per] for i in range(streams)]; pos += streams * per
    acc = []; th = [threading.Thread(target=rd, args=(g, acc)) for g in groups]
    t0 = time.perf_counter(); [t.start() for t in th]; [t.join() for t in th]; dt = time.perf_counter() - t0
    out.append(f"streams {streams} GB {sum(acc)/1e9:.2f} s {dt:.1f} GBps {sum(acc)/dt/1e9:.3f}"); print("beegfs cold read from", os.uname().nodename, out[-1], flush=True)
open(os.path.expanduser("/home/ghu4/CXL/experimental_results/2026-10-27-reuse-window-prefetch/train/beegfs-bw-c33.txt"), "w").write("# cold reads of the full dataset's test split from c33, 2026-10-27\n" + "\n".join(out) + "\n")
PYEOF
cd $O && $PY train_trace.py /mnt/beegfs/ghu4/hvac/cosmoUniverse_2019_05_4parE_tf_v2_mini/train_1024 $O/pilot-1024 --epochs 2 --batch-size 4 --seed 0 2>&1 | grep -v "^I0\|cpu_feature_guard\|oneDNN\|rebuild TensorFlow"
echo PILOTDONE
