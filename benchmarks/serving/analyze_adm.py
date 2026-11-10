#!/usr/bin/env python3
"""Admission analysis of one instrumented serving run (2026-11-10 study, Experiment A): joins the admission stream of
kvadm/sitecustomize.py (poll / adm / kv / runfail / preempt) with the per-request records of analyze_b.py and splits every
request's time before its first token into phases and, inside the waiting phases, into the reason the scheduler gives:

  phases   pre      queued -> first visit by the waiting-queue scan (first poll / first admission attempt)
           lookup   first visit -> the visit at which the LMCache lookup result is known
           admit    lookup result -> first successful block allocation (a miss starts computing; a hit's load is issued)
           load     (external hits) allocation -> the engine notices the finished load (transfer + step boundary)
           promote  (external hits) load noticed -> the allocation that puts the request in RUNNING
           compute  RUNNING -> first token (own prefill chunks and the steps given to other running requests)
  reasons  (for pre / admit / promote; each engine step [schedule_i, schedule_i+1) is charged to one reason)
           own:<gate>   the request itself was refused in that step: full (full-sequence gate), free (not enough free
                        blocks), resv (fits in the free blocks but not under the in-flight prefill reservation)
           hol:<gate>   another waiting request was refused in that step and the scan stopped there (head-of-line)
           budget       the running requests used the whole token budget: the waiting queue was not scanned
           budget_adm   the scan ran out of token budget on requests admitted ahead of this one in that step
           slots        max_num_seqs running requests
           preempt      a preemption in that step (the waiting queue is not scanned)
           pending      visited, LMCache lookup still pending (reason of the lookup phase)
           other        none of the above (e.g. a step that scanned and admitted without reaching the request)
Request categories as in hitcat_d.py (host >= 50 % of the prompt retrieved from LMCache, GPU >= 50 % from the prefix
cache, 10-50 %, miss < 10 %).
Outputs <out>/<tag>-adm-requests.csv, <out>/<tag>-adm-kv.csv (per-step occupancy, decimated to >= 0.25 s) and
<out>/tables-adm-<tag>.md; prints the tables.
usage: analyze_adm.py <out> <tag> [budget=2048] [slots=16] [case=trace|all|<case,case,...>]"""
import bisect, csv, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_b import analyze

def q(v, p):
    v = sorted(x for x in v if x is not None); return v[min(len(v) - 1, int(p * len(v)))] if v else None
def f1(v, d=2): return "–" if v is None else f"{v:.{d}f}"
CATS = ("host≥50%", "GPU≥50%", "10–50%", "miss<10%", "mixed")
def cat_of(P, c, h):
    return "miss<10%" if c < 0.1 * P else "10–50%" if c < 0.5 * P else "host≥50%" if h >= 0.5 * P else "GPU≥50%" if c - h >= 0.5 * P else "mixed"

def load_adm(out, tag):
    polls, adms, pre, kv, runfail = {}, {}, {}, [], []
    for f in glob.glob(f"{out}/{tag}-vllmevt.adm.*.jsonl"):
        for l in open(f):
            d = json.loads(l); e = d.get("ev")
            if e == "poll": polls.setdefault(d["rid"], []).append(d)
            elif e == "adm": adms.setdefault(d["rid"], []).append(d)
            elif e == "preempt": pre.setdefault(d["rid"], []).append(d)
            elif e == "kv": kv.append(d)
            elif e == "runfail": runfail.append(d)
    kv.sort(key=lambda d: d["i"])
    arrived = {}                       # request id -> instant the engine received its finished load (step stream, "end" events)
    for f in glob.glob(f"{out}/{tag}-vllmevt.step.*.jsonl"):
        for l in open(f):
            if '"end"' not in l: continue
            d = json.loads(l)
            if d.get("ev") == "end":
                for rid in d.get("fr") or (): arrived.setdefault(rid, d["t"])
    return polls, adms, pre, kv, runfail, arrived

def main(out, tag, B=2048, SLOTS=16, case="trace"):
    rows, _, _ = analyze(out, tag)
    polls, adms, pre, kv, runfail, arrived = load_adm(out, tag)
    if not kv: print(f"{tag}: no admission stream"); return None
    T0 = [d["t0"] for d in kv]; I0 = kv[0]["i"]; N = len(kv)
    kvi = {d["i"]: n for n, d in enumerate(kv)}
    # per-step facts: visited request ids, the refused attempt (at most one: the scan breaks), preemptions
    visited = {}; refused = {}; preempt_steps = set()
    for rid, L in polls.items():
        for d in L: visited.setdefault(d["i"], set()).add(rid)
    for rid, L in adms.items():
        for d in L:
            visited.setdefault(d["i"], set()).add(rid)
            if not d["ok"]: refused[d["i"]] = d
    for rid, L in pre.items():
        for d in L: preempt_steps.add(d["i"])
    def step_reason(n, rid):
        """reason charged to request `rid` for step n (index into kv) when the request was waiting and not admitted in it"""
        d = kv[n]; i = d["i"]; vis = visited.get(i, ())
        if rid in vis:
            r = refused.get(i)
            if r is not None and r["rid"] == rid: return "own:" + r["gate"]
            return "pending"
        if i in preempt_steps: return "preempt"
        r = refused.get(i)
        if r is not None: return "hol:" + r["gate"]
        bud = d.get("bud", B)                                # the step's own token budget (a KVADM_POLICY may shorten a step)
        if d["runtok"] >= bud: return "budget"
        if d["tok"] >= bud: return "budget_adm"
        if d["run"] >= SLOTS: return "slots"
        return "other"
    def span(t_a, t_b, rid, acc):
        """charge [t_a, t_b) to reasons, step by step"""
        if t_a is None or t_b is None or t_b <= t_a: return
        n = max(0, bisect.bisect_right(T0, t_a) - 1)
        while n < N and T0[n] < t_b:
            lo = max(t_a, T0[n]); hi = min(t_b, T0[n + 1] if n + 1 < N else t_b)
            if hi > lo: k = step_reason(n, rid); acc[k] = acc.get(k, 0.0) + (hi - lo)
            n += 1
    R = []
    for r in rows:
        if r["status"] != 200 or (case != "all" and r["case"] not in case.split(",")) or not r.get("irid"): continue
        rid = r["irid"]; P = r["prompt_tokens"]; c = r.get("cached_tokens") or 0; h = r.get("retrieve_tokens") or 0
        base = r["send_mono"]; ab = lambda ms: None if ms is None else base + ms / 1000
        tq = ab(r.get("queued_ms")); tft = ab(r.get("first_token_engine_ms")) or ab(r.get("first_token_client_ms"))
        pl = sorted(polls.get(rid, []), key=lambda d: d["t"]); al = sorted(adms.get(rid, []), key=lambda d: d["t"])
        ev_t = [d["t"] for d in pl] + [d["t"] for d in al]
        t_visit = min(ev_t) if ev_t else None
        res = [d for d in pl if d["ext"] is not None]
        t_res = res[0]["t"] if res else (al[0]["t"] if al else None)
        ok = [d for d in al if d["ok"]]
        first_ok = ok[0] if ok else None
        is_load = bool(first_ok and first_ok["as"])
        t_adm = first_ok["t"] if first_ok else None
        t_arr = (arrived.get(rid) or ab(r.get("kv_arrived_ms"))) if is_load else None
        prom = [d for d in ok if d["comp"] > 0 and not d["as"]]
        t_run = (prom[0]["t"] if prom else None) if is_load else t_adm
        d = dict(rid=r["rid"], cat=cat_of(P, c, h), prompt=P, cached=c, host=h, ttft=r["ttft_client_ms"] / 1000, total=r["total_ms"] / 1000,
                 ext=first_ok["ext"] if first_ok else None, loc=first_ok["loc"] if first_ok else None,
                 need_now=first_ok["now"] if first_ok else None, need_full=first_ok["full"] if first_ok else None,
                 free_at_adm=first_ok["free"] if first_ok else None,
                 n_polls=len(pl), n_polls_result=len(res), n_refused=sum(1 for x in al if not x["ok"]),
                 n_ref_full=sum(1 for x in al if x["gate"] == "full"), n_ref_free=sum(1 for x in al if x["gate"] == "free"), n_ref_resv=sum(1 for x in al if x["gate"] == "resv"),
                 preempted=len(pre.get(rid, [])), store_bytes=r.get("store_bytes") or 0, n_stores=r.get("n_stores") or 0, send=base, trace_s=r.get("trace_s"),
                 case=r["case"], grp=r.get("grp"), t_q=tq, t_visit=t_visit, t_res=t_res, t_adm=t_adm, t_arr=t_arr, t_run=t_run, t_ft=tft,
                 first_free=(al[0]["free"] if al else None), first_ok=(al[0]["ok"] if al else None), first_gate=(al[0]["gate"] if al else None),
                 first_now=(al[0]["now"] if al else None), first_full=(al[0]["full"] if al else None), first_resv=(al[0]["resv"] if al else None))
        first_ref = next((x for x in al if not x["ok"]), None)
        if first_ref: d.update(ref_free=first_ref["free"], ref_now=first_ref["now"], ref_full=first_ref["full"], ref_resv=first_ref["resv"], ref_gate=first_ref["gate"])
        ph = {}
        ph["pre"] = (tq, t_visit); ph["lookup"] = (t_visit, t_res); ph["admit"] = (t_res, t_adm)
        if is_load: ph["load"] = (t_adm, t_arr); ph["promote"] = (t_arr, t_run)
        ph["compute"] = (t_run, tft)
        for k, (a, b) in ph.items(): d["ph_" + k] = (b - a) if (a is not None and b is not None) else None
        for k in ("pre", "lookup", "admit", "promote"):
            if k in ph:
                acc = {}; span(ph[k][0], ph[k][1], rid, acc)
                for kk, v in acc.items(): d[f"w_{k}_{kk}"] = v
        acc = {}; span(tq, t_run, rid, acc)       # every waiting step from queueing to RUNNING, load included
        for kk, v in acc.items(): d["w_" + kk] = v
        d["wait_total"] = (t_run - tq) if (t_run is not None and tq is not None) else None
        if tq is not None:                                   # engine state at the first schedule() after the request was queued
            a = kv[min(N - 1, bisect.bisect_left(T0, tq))]
            d.update(arr_run=a["run"], arr_infl=a["infl"], arr_sat=int(a["runtok"] >= a.get("bud", B)), arr_free=a["free0"] / a["tot"], arr_wait=a["wait"] + a["hold"])
        R.append(d)
    if not R: print(f"{tag}: no requests"); return None
    keys = sorted({k for d in R for k in d}, key=lambda k: (k.startswith("w_"), k.startswith("ph_"), k))
    with open(f"{out}/{tag}-adm-requests.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
        for d in R: w.writerow({k: ("" if d.get(k) is None else (f"{d[k]:.4f}" if isinstance(d[k], float) else d[k])) for k in keys})
    with open(f"{out}/{tag}-adm-kv.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["t", "free", "tot", "run", "wait", "hold", "wfr", "wfrb", "infl", "resv", "runtok", "tok", "dfree"]); last = -1e9
        for d in kv:
            if d["t0"] - last >= 0.25:
                last = d["t0"]; w.writerow([f"{d['t0']:.3f}", d["free1"], d["tot"], d["run"], d["wait"], d["hold"], d["wfr"], d["wfrb"], d["infl"], d["resv"], d["runtok"], d["tok"], d["dfree"]])
    # ---------------- tables
    L = [f"## Admission analysis of `{tag}` ({len(R)} requests, {N} engine steps, pool {kv[0]['tot']} blocks, token budget {B})\n"]
    L.append("### Table 1 — time before the first token by phase (seconds; median / mean per request of the category)\n")
    L.append("| category | n | prompt tok p50 | blocks loaded or first chunk p50 | TTFT p50 / p95 | pre | lookup | admit | load | promote | compute |"); L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    mm = lambda v: "–" if not [x for x in v if x is not None] else f"{q(v, .5):.2f} / {sum(x for x in v if x is not None) / len([x for x in v if x is not None]):.2f}"
    for cname in CATS:
        v = [d for d in R if d["cat"] == cname]
        if not v: continue
        L.append(f"| {cname} | {len(v)} | {q([d['prompt'] for d in v], .5):.0f} | {f1(q([d['need_now'] for d in v], .5), 0)} | {q([d['ttft'] for d in v], .5):.2f} / {q([d['ttft'] for d in v], .95):.2f} | "
                 + " | ".join(mm([d.get('ph_' + k) for d in v]) for k in ("pre", "lookup", "admit", "load", "promote", "compute")) + " |")
    reasons = sorted({k[2:] for d in R for k in d if k.startswith("w_") and not k.startswith(("w_pre_", "w_lookup_", "w_admit_", "w_promote_"))})
    L.append("\n### Table 2 — waiting time from queueing to RUNNING by reason (mean seconds per request; share of the category's waiting time in brackets)\n")
    L.append("| category | n | wait mean (s) | " + " | ".join(reasons) + " |"); L.append("|---|---|---|" + "---|" * len(reasons))
    for cname in CATS:
        v = [d for d in R if d["cat"] == cname]
        if not v: continue
        tot = sum(sum(d.get("w_" + k, 0.0) for k in reasons) for d in v) or 1e-9
        L.append(f"| {cname} | {len(v)} | {sum(d['wait_total'] or 0 for d in v) / len(v):.2f} | " + " | ".join(f"{sum(d.get('w_' + k, 0.0) for d in v) / len(v):.2f} [{100 * sum(d.get('w_' + k, 0.0) for d in v) / tot:.0f}%]" for k in reasons) + " |")
    for phn in ("pre", "lookup", "admit", "promote"):
        rs = sorted({k[len(phn) + 3:] for d in R for k in d if k.startswith(f"w_{phn}_")})
        if not rs: continue
        L.append(f"\n### Table 3-{phn} — the `{phn}` phase by reason (mean seconds per request)\n")
        L.append("| category | n | " + " | ".join(rs) + " |"); L.append("|---|---|" + "---|" * len(rs))
        for cname in CATS:
            v = [d for d in R if d["cat"] == cname]
            if v: L.append(f"| {cname} | {len(v)} | " + " | ".join(f"{sum(d.get(f'w_{phn}_{k}', 0.0) for d in v) / len(v):.2f}" for k in rs) + " |")
    L.append("\n### Table 4 — refused admission attempts (each ends that step's scan of the waiting queue)\n")
    allref = [x for Lx in adms.values() for x in Lx if not x["ok"]]
    L.append("| kind of attempt | refused attempts | gate full / free / resv | blocks needed now p50 | full-sequence blocks p50 | free blocks p50 (p10–p90) | reservation p50 (max) |"); L.append("|---|---|---|---|---|---|---|")
    for name, sel in (("external load (first admission)", lambda x: x["as"]), ("compute, no computed tokens (miss / GPU-prefix hit)", lambda x: not x["as"] and x["comp"] == 0),
                      ("promotion after a load", lambda x: not x["as"] and x["comp"] > 0)):
        v = [x for x in allref if sel(x)]
        if v: L.append(f"| {name} | {len(v)} | {sum(1 for x in v if x['gate'] == 'full')} / {sum(1 for x in v if x['gate'] == 'free')} / {sum(1 for x in v if x['gate'] == 'resv')} | {q([x['now'] for x in v], .5)} | {q([x['full'] for x in v], .5)} | "
                      f"{q([x['free'] for x in v], .5)} ({q([x['free'] for x in v], .1)}–{q([x['free'] for x in v], .9)}) | {q([x['resv'] for x in v], .5)} ({max(x['resv'] for x in v)}) |")
    nreq_ref = sum(1 for d in R if d["n_refused"]); L.append(f"\nRequests refused at least once: {nreq_ref} of {len(R)}; preemptions: {sum(len(v) for v in pre.values())}; running requests that could not get their next chunk: {len(runfail)}.")
    okload = [x for Lx in adms.values() for x in Lx if x["ok"] and x["as"]]
    if okload: L.append(f"Admitted external loads: {len(okload)}; reservation passed at admission p50 {q([x['resv'] for x in okload], .5)} / max {max(x['resv'] for x in okload)} blocks; free blocks at admission p50 {q([x['free'] for x in okload], .5)}.")
    # occupancy, time-weighted
    dur = [(kv[n + 1]["t0"] - kv[n]["t0"]) for n in range(N - 1)]; W = sum(dur) or 1e-9
    def tw(key, fn=lambda x: x): return sum(fn(kv[n][key]) * dur[n] for n in range(N - 1)) / W
    tot = kv[0]["tot"]
    L.append("\n### Table 5 — GPU KV occupancy over the run (time-weighted)\n")
    L.append("| quantity | value |"); L.append("|---|---|")
    L.append(f"| used share of the pool, mean | {1 - tw('free1') / tot:.3f} |")
    for thr in (0.5, 0.25, 0.1, 0.05):
        L.append(f"| time with free blocks < {thr:.0%} of the pool | {sum(dur[n] for n in range(N - 1) if kv[n]['free1'] < thr * tot) / W:.3f} |")
    L.append(f"| blocks held by loads in transfer, mean / max | {tw('wfrb'):.0f} / {max(d['wfrb'] for d in kv)} |")
    L.append(f"| in-flight prefill reservation after schedule(), mean / max | {tw('resv'):.0f} / {max(d['resv'] for d in kv)} |")
    L.append(f"| steps whose running requests used the whole token budget (share of time) | {sum(dur[n] for n in range(N - 1) if kv[n]['runtok'] >= kv[n].get('bud', B)) / W:.3f} |")
    if any(d.get("bud", B) != B for d in kv): L.append(f"| steps with a shortened token budget (share of time) | {sum(dur[n] for n in range(N - 1) if kv[n].get('bud', B) != B) / W:.3f} |")
    L.append(f"| running requests, mean / max | {tw('run'):.1f} / {max(d['run'] for d in kv)} |")
    L.append(f"| waiting + kv-holding requests, mean / max | {tw('wait') + tw('hold'):.1f} / {max(d['wait'] + d['hold'] for d in kv)} |")
    L.append("\n### Table 6 — engine state at arrival, and TTFT conditional on it (seconds, p50 [n])\n")
    L.append("| category | n | arrives with a prefill in flight | arrives in a budget-saturated step | free share of the pool at arrival p50 / p10 | TTFT, no prefill in flight | TTFT, prefill in flight | TTFT, free share ≥ 0.25 | TTFT, free share < 0.25 |"); L.append("|---|---|---|---|---|---|---|---|---|")
    pq = lambda v: "–" if not v else f"{q(v, .5):.2f} [{len(v)}]"
    for cname in CATS:
        v = [d for d in R if d["cat"] == cname and d.get("arr_infl") is not None]
        if not v: continue
        L.append(f"| {cname} | {len(v)} | {sum(1 for d in v if d['arr_infl'] > 0) / len(v):.2f} | {sum(d['arr_sat'] for d in v) / len(v):.2f} | {q([d['arr_free'] for d in v], .5):.2f} / {q([d['arr_free'] for d in v], .1):.2f} | "
                 f"{pq([d['ttft'] for d in v if d['arr_infl'] == 0])} | {pq([d['ttft'] for d in v if d['arr_infl'] > 0])} | {pq([d['ttft'] for d in v if d['arr_free'] >= 0.25])} | {pq([d['ttft'] for d in v if d['arr_free'] < 0.25])} |")
    T = "\n".join(L) + "\n"; open(f"{out}/tables-adm-{tag}.md", "w").write(T); print(T)
    return R

if __name__ == "__main__":
    kvs = dict(a.split("=", 1) for a in sys.argv[3:] if "=" in a)
    main(sys.argv[1], sys.argv[2], int(kvs.get("budget", 2048)), int(kvs.get("slots", 16)), kvs.get("case", "trace"))
