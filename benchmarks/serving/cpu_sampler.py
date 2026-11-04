#!/usr/bin/env python3
"""Host CPU sampler for the 2026-11-04 serving study, until SIGTERM / SIGINT. Every `interval_ms` it prints
  "G <mono_ns> <group> <busy fraction of the group's cpus over the last interval>"   from /proc/stat (user+nice+system+irq+softirq+steal over total)
  "P <mono_ns> <name> <cpu seconds consumed so far (utime+stime of all threads)> <rss_MiB>"   from /proc/<pid>/stat
Processes that exit are dropped silently; a group is a cpu list like 96-119,124.
usage: cpu_sampler.py <interval_ms> group=<cpulist>[ group=<cpulist>...] [pid:<name>=<pid> ...]"""
import os, signal, sys, threading, time

interval = int(sys.argv[1]) / 1000; groups = {}; pids = {}
for a in sys.argv[2:]:
    k, v = a.split("=", 1)
    if k.startswith("pid:"): pids[k[4:]] = int(v)
    else:
        cpus = set()
        for part in v.split(","):
            if "-" in part: lo, hi = part.split("-"); cpus.update(range(int(lo), int(hi) + 1))
            else: cpus.add(int(part))
        groups[k] = cpus
stop = threading.Event(); signal.signal(signal.SIGTERM, lambda s, f: stop.set()); signal.signal(signal.SIGINT, lambda s, f: stop.set())
CLK = os.sysconf("SC_CLK_TCK"); PAGE = os.sysconf("SC_PAGE_SIZE")

def read_stat():
    out = {}
    for line in open("/proc/stat"):
        if line.startswith("cpu") and line[3] != " ":
            f = line.split(); n = int(f[0][3:]); v = [int(x) for x in f[1:9]]
            busy = v[0] + v[1] + v[2] + v[5] + v[6] + v[7]; out[n] = (busy, sum(v))
    return out

def read_pid(pid):
    try:
        with open(f"/proc/{pid}/stat") as f: s = f.read()
        r = s[s.rindex(")") + 2:].split(); utime, stime, rss = int(r[11]), int(r[12]), int(r[21])
        return (utime + stime) / CLK, rss * PAGE >> 20
    except Exception: return None

print(f"# cpu_sampler start {time.monotonic_ns()} wall {time.time():.6f} interval_ms {sys.argv[1]} groups {list(groups)} pids {pids}", flush=True)
prev = read_stat()
while not stop.is_set():
    stop.wait(interval); cur = read_stat(); t = time.monotonic_ns()
    for g, cpus in groups.items():
        b = sum(cur[c][0] - prev[c][0] for c in cpus if c in cur and c in prev); tot = sum(cur[c][1] - prev[c][1] for c in cpus if c in cur and c in prev)
        print(f"G {t} {g} {b / tot if tot else 0:.4f}")
    prev = cur
    for name, pid in list(pids.items()):
        r = read_pid(pid)
        if r is None: pids.pop(name); continue
        print(f"P {t} {name} {r[0]:.3f} {r[1]}")
    sys.stdout.flush()
print(f"# cpu_sampler end {time.monotonic_ns()}", flush=True)
