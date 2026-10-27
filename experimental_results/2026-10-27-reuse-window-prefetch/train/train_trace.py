#!/usr/bin/env python3
"""Real CosmoFlow training run with an EXPLICIT per-epoch sample schedule and an access trace (2026-10-27 exploratory study).
Uses the group's CosmoFlow TensorFlow benchmark (~/hvac/benchmark/cosmoflow-benchmark-master: model, parse function, config) and
its TFRecord data, but builds the input pipeline here so that the epoch order is an explicit seeded permutation (NoPFS-style:
the order of EVERY epoch is known from the seed at job start) and every file pull and every training step is time-stamped.
Writes to <out>/: schedule.txt ("E <epoch> <t_computed_s> <t_epoch_start_s> <n> <ids...>"), reads.txt ("R <t_s> <epoch> <pos> <id> <bytes>":
the moment the tf.data pipeline pulls the file, i.e. the read of the whole TFRecord), batches.txt ("B <t_s> <epoch> <step> <loss>"), files.txt
(id -> name, bytes), run.json (settings, speeds). t = seconds since the process start (monotonic).
usage: train_trace.py <data_dir with train/> <out_dir> [--n-train N] [--epochs E] [--batch-size 4] [--seed 0] [--parse-par 1] [--prefetch 4] [--gpu 0]"""
import argparse, json, os, sys, time
BENCH = os.path.expanduser("~/hvac/benchmark/cosmoflow-benchmark-master"); sys.path.insert(0, BENCH)
ap = argparse.ArgumentParser(); ap.add_argument("data_dir"); ap.add_argument("out"); ap.add_argument("--n-train", type=int, default=0)
ap.add_argument("--epochs", type=int, default=3); ap.add_argument("--batch-size", type=int, default=4); ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--parse-par", type=int, default=1); ap.add_argument("--prefetch", type=int, default=4); ap.add_argument("--gpu", type=int, default=0)
ap.add_argument("--lr", type=float, default=0.001); ap.add_argument("--read-par", type=int, default=1, help="files read concurrently (tf.data interleave cycle length); 1 = the benchmark's sequential reader")
A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
T0 = time.monotonic(); now = lambda: time.monotonic() - T0
import numpy as np, yaml
import tensorflow as tf
gpus = tf.config.list_physical_devices("GPU")
if gpus:
    tf.config.set_visible_devices(gpus[A.gpu], "GPU"); tf.config.experimental.set_memory_growth(gpus[A.gpu], True)
def _parse_data(sample_proto, shape, apply_log=False):   # verbatim from the benchmark's data/cosmo.py (imported here to avoid its horovod import)
    feature_spec = dict(x=tf.io.FixedLenFeature([], tf.string), y=tf.io.FixedLenFeature([4], tf.float32))
    parsed_example = tf.io.parse_single_example(sample_proto, features=feature_spec)
    x = tf.io.decode_raw(parsed_example['x'], tf.int16)
    x = tf.cast(tf.reshape(x, shape), tf.float32)
    y = parsed_example['y']
    if apply_log: x = tf.math.log(x + tf.constant(1.))
    else: x /= (tf.reduce_sum(x) / np.prod(shape))
    return x, y
from models import get_model
cfg = yaml.safe_load(open(os.path.join(BENCH, "configs", "cosmo.yaml")))
shape = cfg["data"]["sample_shape"]; apply_log = cfg["data"].get("apply_log", True); compression = cfg["data"].get("compression", "GZIP")
# ---- files ----
tdir = os.path.join(A.data_dir, "train"); names = sorted(f for f in os.listdir(tdir) if f.endswith(".tfrecord"))
if A.n_train: names = names[:A.n_train]
N = len(names); sizes = np.array([os.stat(os.path.join(tdir, f)).st_size for f in names], dtype=np.int64)
with open(os.path.join(A.out, "files.txt"), "w") as f:
    for i, (nm, sz) in enumerate(zip(names, sizes)): f.write(f"{i} {nm} {sz}\n")
print(f"[{now():.1f}] {N} training files, {sizes.sum() / 1e9:.1f} GB ({sizes.sum() / 2**30:.1f} GiB), mean {sizes.mean() / 1e6:.2f} MB", flush=True)
# ---- the schedule: every epoch's permutation from the seed, computed NOW (job start) ----
sched = open(os.path.join(A.out, "schedule.txt"), "w"); perms = []
for e in range(A.epochs):
    t0 = time.perf_counter(); p = np.random.default_rng(A.seed * 1000003 + e).permutation(N); perms.append(p)
    sched.write(f"E {e} {now():.6f} -1 {N} " + " ".join(map(str, p.tolist())) + "\n")
    print(f"[{now():.1f}] epoch {e} schedule: permutation of {N} ids computed in {1e3 * (time.perf_counter() - t0):.2f} ms ({p.nbytes / 1e6:.2f} MB)", flush=True)
sched.flush()
# ---- the pipeline: explicit order -> log the pull -> read the whole TFRecord -> parse -> batch -> prefetch ----
reads = open(os.path.join(A.out, "reads.txt"), "w"); epoch_now = [0]; pos_now = [0]
def _log_pull(idx):
    i = int(idx); reads.write(f"R {now():.6f} {epoch_now[0]} {pos_now[0]} {i} {int(sizes[i])}\n"); pos_now[0] += 1
    return idx
def make_epoch_dataset(perm):
    files = [os.path.join(tdir, names[i]) for i in perm]
    ds = tf.data.Dataset.from_tensor_slices((tf.constant(files), tf.constant(perm.astype(np.int64))))
    ds = ds.map(lambda f, i: (f, tf.py_function(_log_pull, [i], tf.int64)), num_parallel_calls=1)
    if A.read_par > 1: ds = ds.interleave(lambda f, i: tf.data.TFRecordDataset(f, compression_type=compression), cycle_length=A.read_par, block_length=1, num_parallel_calls=A.read_par)
    else: ds = ds.flat_map(lambda f, i: tf.data.TFRecordDataset(f, compression_type=compression))
    ds = ds.map(lambda proto: _parse_data(proto, shape=shape, apply_log=apply_log), num_parallel_calls=A.parse_par)
    ds = ds.batch(A.batch_size, drop_remainder=True).prefetch(A.prefetch)
    return ds
# ---- model, as the benchmark builds it ----
model = get_model(**cfg["model"])
opt = tf.keras.optimizers.SGD(learning_rate=A.lr, momentum=cfg["optimizer"].get("momentum", 0.9))
model.compile(optimizer=opt, loss=cfg["train"]["loss"] if "train" in cfg and "loss" in cfg["train"] else "mse", metrics=["mean_absolute_error"])
bl = open(os.path.join(A.out, "batches.txt"), "w")
class Steps(tf.keras.callbacks.Callback):
    def on_train_batch_end(self, batch, logs=None): bl.write(f"B {now():.6f} {epoch_now[0]} {batch} {logs.get('loss', float('nan')):.5f}\n")
steps = N // A.batch_size; speeds = []
print(f"[{now():.1f}] model built; {steps} steps per epoch at batch {A.batch_size}; starting", flush=True)
for e in range(A.epochs):
    epoch_now[0] = e; pos_now[0] = 0; te = now(); sched.write(f"S {e} {te:.6f}\n"); sched.flush()
    h = model.fit(make_epoch_dataset(perms[e]), epochs=1, steps_per_epoch=steps, callbacks=[Steps()], verbose=0)
    dt = now() - te; speeds.append(N / dt); reads.flush(); bl.flush()
    print(f"[{now():.1f}] epoch {e}: {N} samples in {dt:.1f} s = {N / dt:.2f} samples/s ({N / dt * sizes.mean() / 1e6:.1f} MB/s of files), loss {h.history['loss'][0]:.5f}", flush=True)
json.dump(dict(data_dir=A.data_dir, n_train=N, bytes=int(sizes.sum()), epochs=A.epochs, batch_size=A.batch_size, seed=A.seed, parse_par=A.parse_par, prefetch=A.prefetch, read_par=A.read_par,
               samples_per_s=speeds, gpu=[g.name for g in gpus], host=os.uname().nodename), open(os.path.join(A.out, "run.json"), "w"), indent=1)
reads.close(); bl.close(); sched.close(); print(f"[{now():.1f}] done", flush=True)
