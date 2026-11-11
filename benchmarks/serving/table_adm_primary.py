#!/usr/bin/env python3
"""Primary evaluation of one trace replay across server configurations (2026-11-10 admission study, Experiment D): one row per
configuration with the eight quantities the study brief lists. Request classes are fixed by the STOCK run (listed first): its
host-dominant hits and its misses are followed through every other run; changes of the means against the stock run in brackets.
Columns: (1) host-dominant hits TTFT p50 / mean, and the same for the GPU-prefix hits; (2) all requests TTFT p50 / p95 / mean; (3) misses TTFT p50 / mean; (4) completed
requests per second and output tokens per second over the makespan (first send to last completion); (5) request time mean / p95;
(6) admission delay = time from queueing to RUNNING, mean, of the stock run's host-dominant hits / misses; (7) GPU KV memory pressure:
time-weighted share of the pool in use, share of time with less than 25 % of the pool free, refused admission attempts; (8) GPU busy:
share of time in engine steps that computed tokens / NVML utilization (from <tag>-replay.json).
Reads <dir>/<tag>-adm-requests.csv, <dir>/<tag>-client.jsonl, <dir>/<tag>-replay.json and the admission stream.
usage: table_adm_primary.py <dir> <stock tag> <tag> [<tag> ...] [labels=<a>|<b>|...]"""
import csv, glob, json, sys
args = [a for a in sys.argv[1:] if not a.startswith("labels=")]; d, tags = args[0], args[1:]
labs = dict(zip(tags, next((a.split("=", 1)[1].split("|") for a in sys.argv[1:] if a.startswith("labels=")), tags)))
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def q(v, p):
    v = sorted(x for x in v if x is not None); return v[min(len(v) - 1, int(p * len(v)))] if v else None
def mean(v):
    v = [x for x in v if x is not None]; return sum(v) / len(v) if v else None
def load(tag):
    out = {}
    for l in open(f"{d}/{tag}-client.jsonl"):
        r = json.loads(l); out[r["rid"]] = r.get("out_tokens") or 0
    R = {r["rid"][len(tag) + 1:]: dict(cat=r["cat"], ttft=fl(r["ttft"]), total=fl(r["total"]), send=fl(r["send"]), wait=fl(r["wait_total"]) or 0.0, out=out.get(r["rid"], 0))
         for r in csv.DictReader(open(f"{d}/{tag}-adm-requests.csv"))}
    steps = []; ref = 0
    for fn in glob.glob(f"{d}/{tag}-vllmevt.adm.*.jsonl"):
        for l in open(fn):
            if '"ev":"kv"' in l: x = json.loads(l); steps.append((x["t0"], x["free1"], x["tot"]))
            elif '"ev":"adm"' in l and '"ok":false' in l: ref += 1
    steps.sort(); dur = [steps[n + 1][0] - steps[n][0] for n in range(len(steps) - 1)]; W = sum(dur) or 1e-9
    used = 1 - sum(steps[n][1] / steps[n][2] * dur[n] for n in range(len(dur))) / W
    lt25 = sum(dur[n] for n in range(len(dur)) if steps[n][1] < 0.25 * steps[n][2]) / W
    v = list(R.values()); span = max(r["send"] + r["total"] for r in v) - min(r["send"] for r in v)
    try: rj = json.load(open(f"{d}/{tag}-replay.json"))
    except Exception: rj = {}
    return dict(R=R, span=span, used=used, lt25=lt25, ref=ref, rj=rj)
D = {t: load(t) for t in tags if glob.glob(f"{d}/{t}-adm-requests.csv")}; tags = [t for t in tags if t in D]; S = D[tags[0]]["R"]
cls = {c: [k for k, r in S.items() if r["cat"] == c] for c in ("host≥50%", "GPU≥50%", "miss<10%")}
f = lambda v, n=2: "–" if v is None else f"{v:.{n}f}"
def pct(b, a): return "" if a in (None, 0) or b is None else f" ({100 * (b - a) / a:+.0f} %)"
print(f"| configuration | host-dominant hits (n = {len(cls['host≥50%'])}): TTFT p50 / mean (s) | GPU-prefix hits (n = {len(cls['GPU≥50%'])}): TTFT p50 / mean (s) | all requests: TTFT p50 / p95 / mean (s) | misses (n = {len(cls['miss<10%'])}): TTFT p50 / mean (s) | requests / s; output tokens / s | request time mean / p95 (s) | "
      "admission delay, mean (s): hits / misses | pool in use; time with < 25 % free; refused attempts | GPU busy: steps / NVML |")
print("|---|---|---|---|---|---|---|---|---|---|")
base = {}
for t in tags:
    R = D[t]["R"]; v = list(R.values()); first = t == tags[0]
    def cm(c, key): return mean([R[k][key] for k in cls[c] if k in R])
    def cq(c, key, p): return q([R[k][key] for k in cls[c] if k in R], p)
    cur = dict(h=cm("host≥50%", "ttft"), g=cm("GPU≥50%", "ttft"), a=mean([r["ttft"] for r in v]), m=cm("miss<10%", "ttft"), rt=mean([r["total"] for r in v]), wh=cm("host≥50%", "wait"), wm=cm("miss<10%", "wait"))
    if first: base = cur
    p = (lambda k: "") if first else (lambda k: pct(cur[k], base[k]))
    rj = D[t]["rj"]
    print(f"| {labs[t]} | {f(cq('host≥50%', 'ttft', .5))} / {f(cur['h'])}{p('h')} | {f(cq('GPU≥50%', 'ttft', .5))} / {f(cur['g'])}{p('g')} | {f(q([r['ttft'] for r in v], .5))} / {f(q([r['ttft'] for r in v], .95), 1)} / {f(cur['a'])}{p('a')} | {f(cq('miss<10%', 'ttft', .5))} / {f(cur['m'])}{p('m')} | "
          f"{len(v) / D[t]['span']:.3f}; {sum(r['out'] for r in v) / D[t]['span']:.1f} | {f(cur['rt'], 1)}{p('rt')} / {f(q([r['total'] for r in v], .95), 1)} | {f(cur['wh'])} / {f(cur['wm'])} | "
          f"{D[t]['used']:.2f}; {D[t]['lt25']:.2f}; {D[t]['ref']} | {f(rj.get('gpu_busy_steps'))} / {f(rj.get('gpu_util_nvml'))} |")
