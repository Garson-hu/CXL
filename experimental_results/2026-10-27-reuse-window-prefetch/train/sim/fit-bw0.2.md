exp  : fit RMSE 0.0251; leave-one-capacity-out RMSE 0.0715 max |err| 0.2024
   C       30 GiB: H0 0.018 H1 0.790 tau 49.5 s rmse 0.0441
   C       60 GiB: H0 0.075 H1 1.000 tau 23.8 s rmse 0.0394
   C      120 GiB: H0 0.368 H1 1.000 tau 5.5 s rmse 0.0169
   C      180 GiB: H0 1.000 H1 1.000 tau 0.2 s rmse 0.0000
   C      360 GiB: H0 1.000 H1 1.000 tau 0.2 s rmse 0.0000
   C      inf GiB: H0 1.000 H1 1.000 tau 0.2 s rmse 0.0000
rat  : fit RMSE 0.0457; leave-one-capacity-out RMSE 0.0696 max |err| 0.18
   C       30 GiB: H0 0.018 H1 0.886 tau 41.2 s rmse 0.0685
   C       60 GiB: H0 0.075 H1 1.000 tau 13.8 s rmse 0.0859
   C      120 GiB: H0 0.368 H1 1.000 tau 2.2 s rmse 0.0215
   C      180 GiB: H0 1.000 H1 1.000 tau 0.2 s rmse 0.0000
   C      360 GiB: H0 1.000 H1 1.000 tau 0.2 s rmse 0.0000
   C      inf GiB: H0 1.000 H1 1.000 tau 0.2 s rmse 0.0000
ramp : fit RMSE 0.0228; leave-one-capacity-out RMSE 0.0825 max |err| 0.2477
   C       30 GiB: H0 0.018 H1 0.778 W* 85.5 s rmse 0.0257
   C       60 GiB: H0 0.075 H1 0.997 W* 41.2 s rmse 0.0267
   C      120 GiB: H0 0.368 H1 0.986 W* 8.0 s rmse 0.0417
   C      180 GiB: H0 1.000 H1 1.000 W* 0.2 s rmse 0.0000
   C      360 GiB: H0 1.000 H1 1.000 W* 0.2 s rmse 0.0000
   C      inf GiB: H0 1.000 H1 1.000 W* 0.2 s rmse 0.0000
best form by leave-one-capacity-out: rat
held-out sweep all-bw0.25.csv: RMSE 0.2303 with the fitted (H1, tau) and the held-out sweep's own H0
wrote /home/ghu4/CXL/experimental_results/2026-10-27-reuse-window-prefetch/train/sim/fit.json
