## a-3b-idle

| case | L | n | cached tok (median) | TTFT client ms p50 / min / max | lookup (median) | retrieve (median) | retrieve GBps (median) | kv end to sched (median) | queue to sched (median) | prefill (median) | engine to client (median) | retrieve MB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cold | 4096 | 30 | 0 | 652.0 / 650.9 / 666.6 | - | - | - | - | - | - | - | - |
| flush | 16320 | 120 | 16128 | 138.3 / 133.8 / 166.4 | - | - | - | - | - | - | - | - |
| gpu | 4096 | 30 | 4095 | 52.3 / 22.1 / 875.3 | - | - | - | - | - | - | - | - |
| host | 4096 | 30 | 4095 | 57.2 / 34.3 / 122.0 | - | - | - | - | - | - | - | - |
