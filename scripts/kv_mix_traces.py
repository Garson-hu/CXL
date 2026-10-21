#!/usr/bin/env python3
"""CONSTRUCTED mixed-workload traces from the real Mooncake traces (RQ1-B admission study, 2026-10-20): the request
streams are real, their combination is not. Hash ids get a per-trace namespace so that the two traces never share
blocks. Output in the agent-trace jsonl format read by kv_agent_replay.py (task = request index, t_lookup, hashes).
  interleave  conversation and tool-agent requests merged by their original timestamps (both span ~3537 s)
  phase       the whole conversation trace followed by the whole tool-agent trace (shifted so that it starts when the
              conversation ends): a workload phase change at t = 3537 s
usage: kv_mix_traces.py <workloads_dir> <out_dir>"""
import json, os, sys
W, O = sys.argv[1], sys.argv[2]; os.makedirs(O, exist_ok=True)
def load(name, ns):
    rows = []
    for l in open(f"{W}/mooncake_{name}_trace.jsonl"):
        r = json.loads(l); rows.append(dict(t=r["timestamp"] / 1000.0, hashes=[f"{ns}{h}" for h in r["hash_ids"]], input_length=r["input_length"]))
    rows.sort(key=lambda r: r["t"]); return rows
C = load("conversation", "c"); T = load("toolagent", "t")
def write(name, rows):
    with open(f"{O}/{name}.jsonl", "w") as f:
        for i, r in enumerate(sorted(rows, key=lambda r: r["t"])):
            f.write(json.dumps(dict(task=i, call=1, rid=f"{name}{i}", t_submit=r["t"], t_lookup=r["t"], t_resp=None, t_dec=None, decision=None, t_task_end=r["t"], outcome="trace", hashes=r["hashes"], found=None, input_length=r["input_length"])) + "\n")
    print(name, len(rows), "requests")
write("mix-interleave", C + T)
shift = C[-1]["t"] - T[0]["t"] + 1.0
write("mix-phase", C + [dict(r, t=r["t"] + shift) for r in T])
