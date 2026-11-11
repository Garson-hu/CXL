#!/usr/bin/env python3
"""Which files does each Horovod rank of the CosmoFlow benchmark read in each epoch? (2026-11-10, for the reuse-distance slide)

The group's copy of the benchmark (~/hvac/benchmark/cosmoflow-benchmark-master/data/cosmo.py, construct_dataset) builds, on every rank,
    Dataset.from_tensor_slices(files).shuffle(len(files), reshuffle_each_iteration=True).shard(n_shards, rank) ... .repeat(n_epochs)
and train.py calls tf.keras.utils.set_random_seed(args.seed) with the same seed on every rank. This script runs exactly that pipeline on
file ids, one process per rank as under Horovod, ON THE CPU (CUDA_VISIBLE_DEVICES is cleared: the GPU is not touched), and reports per
epoch whether the ranks' shares are disjoint and complete, and how many of a rank's files come back to the same rank in the next epoch.
usage: cosmoflow_shard_check.py [ranks=4] [files=1024] [epochs=3] [seed=0]      (needs TensorFlow: run it with the hvac_tf environment)
       cosmoflow_shard_check.py --rank <r> <ranks> <files> <epochs> <seed>      (internal: one rank; prints JSON)"""
import json, os, subprocess, sys
os.environ["CUDA_VISIBLE_DEVICES"] = ""; os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
if len(sys.argv) > 1 and sys.argv[1] == "--rank":
    import tensorflow as tf
    rank, size, n, epochs, seed = (int(x) for x in sys.argv[2:7])
    tf.keras.utils.set_random_seed(seed)
    data = tf.data.Dataset.from_tensor_slices(list(range(n))).shuffle(n, reshuffle_each_iteration=True).shard(num_shards=size, index=rank).repeat(epochs)
    ids = [int(x) for x in data.as_numpy_iterator()]; per = n // size
    print(json.dumps({"rank": rank, "tf": tf.__version__, "epochs": [ids[e * per:(e + 1) * per] for e in range(epochs)]})); sys.exit(0)
kv = dict(a.split("=", 1) for a in sys.argv[1:]); R = int(kv.get("ranks", 4)); N = int(kv.get("files", 1024)); E = int(kv.get("epochs", 3)); seed = int(kv.get("seed", 0))
out = [json.loads(subprocess.run([sys.executable, os.path.abspath(__file__), "--rank", str(r), str(R), str(N), str(E), str(seed)], capture_output=True, text=True, check=True).stdout.strip().splitlines()[-1]) for r in range(R)]
print(f"TensorFlow {out[0]['tf']}; {R} ranks, {N} files, {E} epochs, seed {seed} on every rank")
for e in range(E):
    sets = [set(o["epochs"][e]) for o in out]; union = set().union(*sets)
    print(f"epoch {e + 1}: files per rank {[len(s) for s in sets]}; read by at least one rank {len(union)} of {N}; read by more than one rank {sum(len(s) for s in sets) - len(union)}")
for r in range(R):
    for e in range(E - 1):
        a, b = set(out[r]["epochs"][e]), set(out[r]["epochs"][e + 1])
        print(f"rank {r}: of the {len(a)} files it reads in epoch {e + 1}, {len(a & b)} ({100 * len(a & b) / len(a):.0f} %) come back to it in epoch {e + 2}")
