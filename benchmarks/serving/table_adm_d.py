#!/usr/bin/env python3
"""Comparison tables of instrumented trace replays (2026-11-10 admission study, Experiment D / E): one reference run
(listed first) against other configurations of the SAME replay (same trace window, speed, host tier, GPU KV pool).
  Table D-1  run level: completion, makespan, throughput, cache shares, TTFT and request-time percentiles, token times,
             preemptions, refused admission attempts by gate, GPU KV occupancy, token-budget saturation, GPU utilization, host-tier
             traffic and occupancy (the last two from <tag>-replay.json of analyze_replay.py)
  Table D-2  per request category AS SERVED IN EACH RUN (host >= 50 % of the prompt retrieved from LMCache, GPU >= 50 %
             from the GPU prefix cache, 10-50 %, miss < 10 %): n, TTFT p50 / p95 / mean, request time p50, time per
             output token p50
  Table D-3  paired: the reference run's category fixes the request set; the same requests in every run, with the
             absolute and relative change of TTFT p50 / p95 / mean and of the request time p50 against the reference,
             and the share of requests whose TTFT is more than 10 % (and 0.1 s) lower / higher than in the reference
  Table D-4  fairness by prompt length (the same requests in every run): TTFT p50 / p95 / max and request time p50 for prompts
             shorter than 2,048 tokens, 2,048-8,191 and 8,192 or more; and the longest waits of the run
Reads <out>/<tag>-adm-requests.csv, <out>/<tag>-adm-kv.csv (analyze_adm.py), <out>/<tag>-client.jsonl and the admission
stream <out>/<tag>-vllmevt.adm.*.jsonl. Writes <out>/tables-d-<name>.md when name=<name> is given; prints the tables.
usage: table_adm_d.py <out> <reference tag> <tag> [<tag> ...] [name=<name>] [labels=a,b,c]"""
import csv, glob, json, sys
args = [a for a in sys.argv[1:] if "=" not in a]; kv = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
out, tags = args[0], args[1:]; LAB = dict(zip(tags, kv["labels"].split(","))) if "labels" in kv else {t: t for t in tags}
CATS = [("host≥50%", "host-dominant hit"), ("GPU≥50%", "GPU-prefix hit"), ("10–50%", "partial hit"), ("miss<10%", "miss"), (None, "all requests")]
def fl(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def q(v, p):
    v = sorted(x for x in v if x is not None); return v[min(len(v) - 1, int(p * len(v)))] if v else None
def mean(v):
    v = [x for x in v if x is not None]; return sum(v) / len(v) if v else None
def f(v, d=2): return "–" if v is None else f"{v:.{d}f}"
def chg(a, b):
    """change of b against the reference a: absolute (s) and relative"""
    if a is None or b is None: return "–"
    return f"{b - a:+.2f} ({100 * (b - a) / a:+.0f} %)" if a > 0 else f"{b - a:+.2f}"
def load(tag):
    R = {}
    cl = {}
    for l in open(f"{out}/{tag}-client.jsonl"):
        r = json.loads(l); cl[r["rid"]] = r
    for r in csv.DictReader(open(f"{out}/{tag}-adm-requests.csv")):
        c = cl.get(r["rid"], {}); ot = c.get("out_tokens") or 0; ttft = fl(r["ttft"]); tot = fl(r["total"])
        R[r["rid"][len(tag) + 1:]] = dict(cat=r["cat"], ttft=ttft, total=tot, prompt=fl(r["prompt"]), cached=fl(r["cached"]) or 0, host=fl(r["host"]) or 0, out=ot,
                                          tpot=((tot - ttft) / (ot - 1)) if (ot > 1 and tot is not None and ttft is not None) else None,
                                          send=fl(r["send"]), pre=int(fl(r["preempted"]) or 0), stores=fl(r["n_stores"]) or 0, sbytes=fl(r["store_bytes"]) or 0)
    n_err = sum(1 for c in cl.values() if c.get("case") == "trace" and (c["status"] != 200 or c.get("error")))
    ref = {"full": 0, "free": 0, "resv": 0}; pre = runfail = 0; steps = []; B = None; prot = []
    for fn in glob.glob(f"{out}/{tag}-vllmevt.adm.*.jsonl"):
        for l in open(fn):
            if '"ev":"kv"' in l:
                d = json.loads(l); steps.append((d["t0"], d["free1"], d["tot"], d["runtok"], d.get("bud"), d["run"], d["wait"] + d["hold"]))
            elif '"ev":"adm"' in l:
                if '"ok":false' in l: d = json.loads(l); ref[d["gate"]] = ref.get(d["gate"], 0) + 1
            elif '"ev":"preempt"' in l: pre += 1
            elif '"ev":"runfail"' in l: runfail += 1
            elif '"ev":"policy"' in l: B = json.loads(l).get("budget")
            elif '"ev":"prot"' in l: d = json.loads(l); prot.append((d["t"], d["on"]))
    steps.sort(); B = B or max((s[4] or 2048) for s in steps)
    dur = [steps[n + 1][0] - steps[n][0] for n in range(len(steps) - 1)]; W = sum(dur) or 1e-9
    tw = lambda fn: sum(fn(steps[n]) * dur[n] for n in range(len(dur))) / W
    occ = dict(pool=steps[0][2], used=1 - tw(lambda s: s[1] / s[2]), lt25=tw(lambda s: s[1] < 0.25 * s[2]), lt10=tw(lambda s: s[1] < 0.10 * s[2]),
               sat=tw(lambda s: s[3] >= (s[4] or B)), short=tw(lambda s: (s[4] or B) != B), run=tw(lambda s: s[5]), wait=tw(lambda s: s[6]))
    ok = list(R.values()); t0 = min(r["send"] for r in ok); t1 = max(r["send"] + r["total"] for r in ok)
    prot.sort(); tp = 0.0; on_at = None                    # time with the mechanisms suspended by the starvation bound (agecap)
    for t, on in prot:
        if on and on_at is None: on_at = t
        elif not on and on_at is not None: tp += t - on_at; on_at = None
    if on_at is not None: tp += steps[-1][0] - on_at
    occ["prot"] = tp / W
    rj = {}
    try: rj = json.load(open(f"{out}/{tag}-replay.json"))
    except Exception: pass
    return dict(R=R, n_err=n_err, ref=ref, pre=pre, runfail=runfail, occ=occ, span=t1 - t0, rj=rj)
D = {t: load(t) for t in tags}; ref = D[tags[0]]
L = []
def table(title, rows):
    L.append(f"### {title}\n"); L.append("| quantity | " + " | ".join(LAB[t] for t in tags) + " |"); L.append("|---|" + "---|" * len(tags))
    for lab, fn in rows: L.append(f"| {lab} | " + " | ".join(str(fn(D[t])) for t in tags) + " |")
    L.append("")
allr = lambda d: list(d["R"].values())
table("Table D-1 — run level", [
    ("requests completed (failed)", lambda d: f"{len(d['R'])} ({d['n_err']})"),
    ("makespan: first send → last completion (s)", lambda d: f(d["span"], 0)),
    ("completed requests / s", lambda d: f(len(d["R"]) / d["span"], 3)),
    ("prompt tokens served from a cache: total / host (LMCache) / GPU prefix", lambda d: (lambda P, c, h: f"{c / P:.3f} / {h / P:.3f} / {(c - h) / P:.3f}")(sum(r["prompt"] for r in allr(d)), sum(r["cached"] for r in allr(d)), sum(r["host"] for r in allr(d)))),
    ("requests by cached share of the prompt: 0 / < 10 % / 10–50 % / 50–90 % / ≥ 90 %", lambda d: " / ".join(str(sum(1 for r in allr(d) if lo <= r["cached"] / r["prompt"] < hi)) for lo, hi in ((-1, 1e-9), (1e-9, 0.1), (0.1, 0.5), (0.5, 0.9), (0.9, 9)))),
    ("requests with a load from the host tier; tokens loaded per such request, p50", lambda d: f"{sum(1 for r in allr(d) if r['host'] > 0)}; {f(q([r['host'] for r in allr(d) if r['host'] > 0], .5), 0)}"),
    ("prompt tokens computed / s", lambda d: f(sum(r["prompt"] - r["cached"] for r in allr(d)) / d["span"], 0)),
    ("output tokens / s", lambda d: f(sum(r["out"] for r in allr(d)) / d["span"], 1)),
    ("TTFT p50 / p95 / p99 (s)", lambda d: " / ".join(f(q([r["ttft"] for r in allr(d)], p)) for p in (.5, .95, .99))),
    ("TTFT mean / max (s)", lambda d: f"{f(mean([r['ttft'] for r in allr(d)]))} / {f(max(r['ttft'] for r in allr(d)))}"),
    ("request time p50 / p95 / mean (s)", lambda d: " / ".join(f(x) for x in (q([r["total"] for r in allr(d)], .5), q([r["total"] for r in allr(d)], .95), mean([r["total"] for r in allr(d)])))),
    ("time per output token after the first, p50 / p95 (ms)", lambda d: " / ".join(f(1000 * q([r["tpot"] for r in allr(d)], p), 0) for p in (.5, .95))),
    ("preemptions (requests preempted)", lambda d: f"{d['pre']} ({sum(1 for r in allr(d) if r['pre'])})"),
    ("running requests refused their next chunk", lambda d: d["runfail"]),
    ("refused admission attempts: full-sequence gate / free blocks / in-flight reservation", lambda d: f"{d['ref'].get('full', 0)} / {d['ref'].get('free', 0)} / {d['ref'].get('resv', 0)}"),
    ("GPU KV pool (blocks); used share, time-weighted mean", lambda d: f"{d['occ']['pool']}; {d['occ']['used']:.3f}"),
    ("time with free blocks < 25 % / < 10 % of the pool", lambda d: f"{d['occ']['lt25']:.3f} / {d['occ']['lt10']:.3f}"),
    ("time in steps whose running requests use the whole token budget", lambda d: f(d["occ"]["sat"], 3)),
    ("time in steps with a shortened token budget (prototype)", lambda d: f(d["occ"]["short"], 3)),
    ("time with the mechanisms suspended by the starvation bound (`agecap`)", lambda d: f(d["occ"]["prot"], 3)),
    ("running / waiting requests, time-weighted mean", lambda d: f"{d['occ']['run']:.1f} / {d['occ']['wait']:.1f}"),
    ("GPU busy share: engine steps with tokens / NVML utilization", lambda d: f"{f(d['rj'].get('gpu_busy_steps'), 3)} / {f(d['rj'].get('gpu_util_nvml'), 3)}"),
    ("KV loaded from the host tier (GB) / host-tier occupancy max (GB) / evicted chunks", lambda d: f"{f(d['rj'].get('retrieve_GB'), 1)} / {f(d['rj'].get('l1_used_GB_max'), 1)} / {d['rj'].get('evicted_chunks', '–')}"),
    ("requests with an LMCache store; GB stored", lambda d: f"{sum(1 for r in allr(d) if r['stores'] > 0)}; {sum(r['sbytes'] for r in allr(d)) / 1e9:.1f}")])
L.append("### Table D-2 — per category as served in each run: n \\| TTFT p50 / p95 / mean (s) \\| request time p50 (s) \\| time per output token p50 (ms)\n")
L.append("| category | " + " | ".join(LAB[t] for t in tags) + " |"); L.append("|---|" + "---|" * len(tags))
for ck, cl_ in CATS:
    cells = []
    for t in tags:
        v = [r for r in allr(D[t]) if ck is None or r["cat"] == ck]
        cells.append("–" if not v else f"{len(v)} \\| {f(q([r['ttft'] for r in v], .5))} / {f(q([r['ttft'] for r in v], .95))} / {f(mean([r['ttft'] for r in v]))} \\| {f(q([r['total'] for r in v], .5))} \\| {f(1000 * q([r['tpot'] for r in v], .5) if q([r['tpot'] for r in v], .5) is not None else None, 0)}")
    L.append(f"| {cl_} | " + " | ".join(cells) + " |")
L.append("")
L.append(f"### Table D-3 — paired by the category in `{LAB[tags[0]]}`: the same requests in every run; changes against `{LAB[tags[0]]}`\n")
L.append("| category in the reference (n) | quantity | " + " | ".join(LAB[t] for t in tags) + " |"); L.append("|---|---|" + "---|" * len(tags))
for ck, cl_ in CATS:
    ks = [k for k, r in ref["R"].items() if (ck is None or r["cat"] == ck) and all(k in D[t]["R"] for t in tags)]
    if not ks: continue
    for lab, fn in (("TTFT p50 (s)", lambda v: q([r["ttft"] for r in v], .5)), ("TTFT p95 (s)", lambda v: q([r["ttft"] for r in v], .95)), ("TTFT mean (s)", lambda v: mean([r["ttft"] for r in v])),
                    ("request time p50 (s)", lambda v: q([r["total"] for r in v], .5)), ("request time mean (s)", lambda v: mean([r["total"] for r in v]))):
        a = fn([ref["R"][k] for k in ks]); cells = []
        for t in tags:
            b = fn([D[t]["R"][k] for k in ks]); cells.append(f(b) if t == tags[0] else f"{f(b)}  {chg(a, b)}")
        L.append(f"| {cl_} ({len(ks)}) | {lab} | " + " | ".join(cells) + " |")
    cells = []
    for t in tags:
        if t == tags[0]: cells.append("–"); continue
        lo = sum(1 for k in ks if D[t]["R"][k]["ttft"] < 0.9 * ref["R"][k]["ttft"] and ref["R"][k]["ttft"] - D[t]["R"][k]["ttft"] > 0.1)
        hi = sum(1 for k in ks if D[t]["R"][k]["ttft"] > 1.1 * ref["R"][k]["ttft"] and D[t]["R"][k]["ttft"] - ref["R"][k]["ttft"] > 0.1)
        cells.append(f"{100 * lo / len(ks):.0f} % / {100 * hi / len(ks):.0f} %")
    L.append(f"| {cl_} ({len(ks)}) | requests with TTFT lower / higher by > 10 % | " + " | ".join(cells) + " |")
L.append(""); L.append("### Table D-4 — by prompt length (same requests in every run): TTFT p50 / p95 / max (s) \\| request time p50 (s)\n")
L.append("| prompt tokens (n) | " + " | ".join(LAB[t] for t in tags) + " |"); L.append("|---|" + "---|" * len(tags))
common = [k for k in ref["R"] if all(k in D[t]["R"] for t in tags)]
for lab, lo, hi in (("< 2,048", 0, 2048), ("2,048–8,191", 2048, 8192), ("≥ 8,192", 8192, 10 ** 9)):
    ks = [k for k in common if lo <= ref["R"][k]["prompt"] < hi]
    if not ks: continue
    cells = []
    for t in tags:
        v = [D[t]["R"][k] for k in ks]
        cells.append(f"{f(q([r['ttft'] for r in v], .5))} / {f(q([r['ttft'] for r in v], .95))} / {f(max(r['ttft'] for r in v))} \\| {f(q([r['total'] for r in v], .5))}")
    L.append(f"| {lab} ({len(ks)}) | " + " | ".join(cells) + " |")
L.append("| requests with TTFT > 30 s / > 60 s | " + " | ".join(f"{sum(1 for r in allr(D[t]) if r['ttft'] > 30)} / {sum(1 for r in allr(D[t]) if r['ttft'] > 60)}" for t in tags) + " |")
T = "\n".join(L) + "\n"
if "name" in kv: open(f"{out}/tables-d-{kv['name']}.md", "w").write(T)
print(T)
