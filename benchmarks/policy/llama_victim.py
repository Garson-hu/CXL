#!/usr/bin/env python3
"""llama.cpp CPU decoding as a victim: runs llama-simple (greedy, one long generation; it flushes stdout after
every token, and our copy takes -t) pinned to the given cpus and stamps every token: "TOK <ns>" lines, plus
"T <ns> <tok/s over the last 500 ms>" every 500 ms, until SIGTERM or the generation ends.
A token = one read() chunk; chunks arrive one flush apart, so the count matches llama-bench's tg rate.
usage: llama_victim.py <threads> <cpulist> <n_tokens>"""
import os, signal, subprocess, sys, time
threads, cpus, n = sys.argv[1], sys.argv[2], sys.argv[3]
LL = os.path.expanduser("~/apps/llama.cpp/build/bin/llama-simple"); M = "/mnt/local/ghu4/models/qwen2.5-7b-instruct-q8_0-00001-of-00003.gguf"
prompt = "Write a very long, detailed history of the city of Raleigh, North Carolina, decade by decade, with many names, dates and places."
cmd = ["taskset", "-c", cpus, LL, "-m", M, "-t", threads, "-n", n, prompt]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
def on_term(s, f): p.terminate()
signal.signal(signal.SIGTERM, on_term)
count, last, tw = 0, time.monotonic_ns(), 0
print(f"READY {last}", flush=True)
while True:
    b = os.read(p.stdout.fileno(), 4096)                              # one chunk per flushed token
    if not b: break
    t = time.monotonic_ns(); count += 1; tw += 1; print(f"TOK {t}")
    if t - last >= 500_000_000:
        print(f"T {t} {tw / ((t - last) / 1e9):.2f}", flush=True); last, tw = t, 0
p.wait()
try: print(f"END {time.monotonic_ns()} tokens={count}", flush=True)
except BrokenPipeError: pass
