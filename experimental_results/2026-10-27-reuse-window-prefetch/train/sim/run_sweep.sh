#!/bin/bash
# Training part of the 2026-10-27 exploratory study: future-window prefetch sweeps on the REAL CosmoFlow access trace (train/run-61440,
# 3 epochs of 61,440 TFRecord samples = 178 GB on the A100 node c33, explicit seeded schedule, parallel input pipeline).
# Windows 0..1200 s x capacities 30/60/120/180/360 GiB and unbounded x storage bandwidth (measured cold BeeGFS reads from c33:
# 0.064 GB/s single stream, 0.33 at 4, 0.52 at 8, 0.82 at 32 streams; 2.0 = an NVMe-class store; inf = ideal) x schedule availability
# (all = every epoch's order known at job start; epoch = known at the epoch's start; none = no prefetch) x demand speed (1x = the
# measured trainer, 4x / 16x = faster trainers or several trainers sharing the link). Epoch 0 is the cold start; epochs 1-2 are scored.
set -u
cd /home/ghu4/CXL
R=experimental_results/2026-10-27-reuse-window-prefetch/train/run-61440; S=experimental_results/2026-10-27-reuse-window-prefetch/train/sim
W=0,5,10,25,50,100,150,200,300,600,1200; CAPS=30,60,120,180,360,inf
for bw in 0.064 0.33 0.82 2.0 1000; do
  lab=all-bw$bw; [ -f $S/$lab.csv ] || nohup python3 scripts/train_prefetch_sim.py $R $S/$lab.csv --windows $W --caps-gib $CAPS --bw-gbps $bw --avail all --label "avail all, B=$bw GB/s" > $S/$lab.log 2>&1 &
done
for bw in 0.33 0.82; do
  lab=epoch-bw$bw; [ -f $S/$lab.csv ] || nohup python3 scripts/train_prefetch_sim.py $R $S/$lab.csv --windows $W --caps-gib $CAPS --bw-gbps $bw --avail epoch --label "avail epoch, B=$bw GB/s" > $S/$lab.log 2>&1 &
done
for sp in 4 16; do
  lab=all-bw0.82-x$sp; [ -f $S/$lab.csv ] || nohup python3 scripts/train_prefetch_sim.py $R $S/$lab.csv --windows $W --caps-gib $CAPS --bw-gbps 0.82 --avail all --speed $sp --label "avail all, B=0.82 GB/s, trainer x$sp" > $S/$lab.log 2>&1 &
done
lab=all-bw0.82-noprotect; [ -f $S/$lab.csv ] || nohup python3 scripts/train_prefetch_sim.py $R $S/$lab.csv --windows $W --caps-gib 60,180 --bw-gbps 0.82 --avail all --no-protect --label "naive prefetcher (no window protection), B=0.82 GB/s" > $S/$lab.log 2>&1 &
lab=none; [ -f $S/$lab.csv ] || nohup python3 scripts/train_prefetch_sim.py $R $S/$lab.csv --windows 0 --caps-gib 15,30,45,60,90,120,150,180,240,360,inf --bw-gbps 0.82 --avail none --label "no prefetch (LRU retention only)" > $S/$lab.log 2>&1 &
# fine windows 0.1-25 s at B = 0.25 / 0.33 / 0.82 GB/s (C = 60 / 180 GiB) to resolve the knee; bandwidths near the trainer's demand
# (0.15 / 0.20 / 0.25 GB/s vs 0.217 GB/s consumed) for the bandwidth-bound regime (added 2026-10-27 15:40 after the first look)
for bw in 0.25 0.33 0.82; do
  lab=fine-bw$bw; [ -f $S/$lab.csv ] || nohup python3 scripts/train_prefetch_sim.py $R $S/$lab.csv --windows 0,0.1,0.25,0.5,1,2,5,10,25 --caps-gib 60,180 --bw-gbps $bw --avail all --label "fine windows, avail all, B=$bw GB/s" > $S/$lab.log 2>&1 &
done
for bw in 0.15 0.2 0.25; do
  lab=all-bw$bw; [ -f $S/$lab.csv ] || nohup python3 scripts/train_prefetch_sim.py $R $S/$lab.csv --windows $W --caps-gib $CAPS --bw-gbps $bw --avail all --label "avail all, B=$bw GB/s" > $S/$lab.log 2>&1 &
done
wait
echo "SWEEPDONE $(date)"
# NOTE 2026-10-27 16:05: the first pass of every sweep above was discarded and rerun after a simulator fix — the window protection of a
# resident entry was a single flag consumed by its first use, so an entry demanded in two epochs inside one window lost its protection
# (spurious cold misses at W >= 200 s); pins are now counts of pending in-window demands (train_prefetch_sim.py).
# NOTE 2026-10-27 16:30: third pass after a bookkeeping change — prefetch bytes are now counted for the scored epochs only (as the demand
# misses are), so the storage-traffic columns compare like with like; hit rates are unchanged (the second pass is kept in pass2/ for the record).
# ---- added 2026-10-27 16:40 for the figure revision (same simulator as the third pass, scripts/train_prefetch_sim.py unchanged since
# commit 7ad141b): the requested figures need (a) the measured 8-stream BeeGFS point 0.52 GB/s (the real run read 8 files concurrently)
# and (b) the fine windows 0.1-2 s at EVERY capacity, plus the finer capacity grid 15-360 GiB of none.csv at W > 0. Full grids:
# windows 0-1200 s x capacities 15..360 GiB, inf at B = 0.52 (grid-bw0.52) and B = 0.20 (grid-bw0.2); fine windows at 60 / 180 GiB
# for B = 0.064 and 0.15 (fine-bw0.064, fine-bw0.15). Overlapping points must reproduce the third-pass CSVs exactly (checked).
WG=0,0.1,0.25,0.5,1,2,5,10,25,50,100,150,200,300,600,1200; CG=15,30,45,60,90,120,150,180,240,360,inf
for bw in 0.52 0.2; do
  lab=grid-bw$bw; [ -f $S/$lab.csv ] || nohup python3 scripts/train_prefetch_sim.py $R $S/$lab.csv --windows $WG --caps-gib $CG --bw-gbps $bw --avail all --label "avail all, B=$bw GB/s" > $S/$lab.log 2>&1 &
done
for bw in 0.064 0.15; do
  lab=fine-bw$bw; [ -f $S/$lab.csv ] || nohup python3 scripts/train_prefetch_sim.py $R $S/$lab.csv --windows 0,0.1,0.25,0.5,1,2,5,10,25 --caps-gib 60,180 --bw-gbps $bw --avail all --label "fine windows, avail all, B=$bw GB/s" > $S/$lab.log 2>&1 &
done
wait
echo "GRIDDONE $(date)"
