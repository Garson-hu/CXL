#!/usr/bin/env python3
"""Experiment C (2026-11-04): a calibrated discrete-event model of one vLLM + LMCache server, used ONLY as an offline
scheduling reference (SIMULATED; never a measurement). It replays a measured request sequence (arrival instants, prompt
lengths, output lengths and the tier each request was served from) through:
  GPU   one engine step at a time. A step takes  c_step + sum over its prefill tokens of r(p) + n_decode * c_dec  where
        r(p) = r0 + r1 * p is the measured per-token prefill cost at prompt position p, c_step the fixed step cost, c_dec
        the per-sequence decode cost; a step carries at most `chunk` prefill tokens (vLLM's token budget) and at most
        `max_seqs` sequences; a request's first token comes out at the end of the step that completes its prefill.
  loads a host hit must first move L * kv_bytes bytes over one transfer channel of bandwidth `bw` (FIFO, one at a time =
        LMCache's single GPU worker; `n_ch` channels for the 4-worker configuration), after a lookup of `lookup` s; the
        load's completion is noticed at the end of the engine step in which it completes (`notice`: the granularity of
        get_transfer_results) and the request then waits `ready` s before it can be scheduled (measured median).
Policies:
  vllm      what the inspected scheduler does: waiting requests in arrival order, requests that hold KV blocks (whose
            load finished) before fresh ones, loads started as soon as the request is first considered (async), the GPU
            never waits for a load (ready requests run while loads are in flight)
  zero      the same with instantaneous loads (ZERO-DELAY reference: an upper bound on what hiding retrieval could give)
  srpt      CLAIRVOYANT: among the requests whose KV is ready, the one with the least remaining prefill work first
            (the mean-TTFT-optimal order for a single server); loads as in `vllm`
  hits      ready host / GPU hits before cold requests (what --scheduling-policy priority with hits_first approximates)
usage (library): sim = Sim(params); res = sim.run(requests, policy)  ->  list of dicts with ttft_s per request
usage (cli):     sched_sim.py <requests.csv of analyze_b.py> <grp> <params.json> [policy ...]"""
import csv, heapq, json, sys

DEFAULT = dict(r0=0.000134, r1=9.4e-9, c_step=0.010, c_dec=0.0003, chunk=2048, max_seqs=16, kv_bytes=36864, bw=12.0e9, n_ch=1, lookup=0.0013, ready=0.003, notice=True)

class Sim:
    def __init__(self, p): self.p = dict(DEFAULT, **p)
    def prefill_time(self, p0, n):
        """time of n prefill tokens starting at position p0"""
        r0, r1 = self.p["r0"], self.p["r1"]; return n * r0 + r1 * (n * p0 + n * (n - 1) / 2)
    def run(self, reqs, policy="vllm"):
        """reqs: list of dict(rid, t_arr, L, tier in host/gpu/cold, out, bytes) sorted by t_arr. Returns per-request results."""
        P = self.p; n = len(reqs); t = 0.0
        prefill_left = [0] * n; pos = [0] * n; out_left = [0] * n; state = ["new"] * n; first = [None] * n; done = [None] * n
        load_done = [None] * n; load_q = []; chans = [0.0] * P["n_ch"]; ready_at = [None] * n
        for i, r in enumerate(reqs):
            if r["tier"] == "cold": prefill_left[i] = r["L"]; pos[i] = 0
            else: prefill_left[i] = 1; pos[i] = r["L"] - 1          # a full hit recomputes the last token
            out_left[i] = max(1, r["out"]) - 1
        waiting = []; running = []; ai = 0; res = {}
        def start_load(i, now):
            k = min(range(P["n_ch"]), key=lambda c: chans[c]); s = max(now + P["lookup"], chans[k]); e = s + reqs[i]["bytes"] / P["bw"]; chans[k] = e
            load_done[i] = e; state[i] = "loading"
        while True:
            while ai < n and reqs[ai]["t_arr"] <= t:
                waiting.append(ai); state[ai] = "waiting"; ai += 1
            # loads: in the real system the lookup+load start when the scheduler first considers the request; model: at the step boundary after arrival
            for i in waiting:
                if state[i] == "waiting" and reqs[i]["tier"] == "host":
                    if policy == "zero": state[i] = "ready"; ready_at[i] = t
                    else: start_load(i, t)
                elif state[i] == "waiting": state[i] = "ready"; ready_at[i] = t
            # loads that finished before now become ready (noticed at the step boundary)
            for i in waiting:
                if state[i] == "loading" and load_done[i] <= t: state[i] = "ready"; ready_at[i] = load_done[i] + P["ready"]
            # schedule a step: running (decode / continuing prefill) first, then ready waiting requests by policy
            budget = P["chunk"]; tokens = 0.0; n_dec = 0; batch = []
            for i in list(running):
                if prefill_left[i] > 0:
                    k = min(prefill_left[i], budget); tokens += self.prefill_time(pos[i], k); batch.append((i, k)); budget -= k
                else:
                    n_dec += 1; batch.append((i, 0)); budget -= 1
            cands = [i for i in waiting if state[i] == "ready" and ready_at[i] <= t]
            if policy == "srpt": cands.sort(key=lambda i: (prefill_left[i], ready_at[i]))
            elif policy == "hits": cands.sort(key=lambda i: (0 if reqs[i]["tier"] != "cold" else 1, ready_at[i]))
            else:  # vllm / zero: holders (loaded host hits) first, then arrival order
                cands.sort(key=lambda i: (0 if reqs[i]["tier"] == "host" else 1, i))
            for i in cands:
                if budget <= 0 or len(running) >= P["max_seqs"]: break
                k = min(prefill_left[i], budget); tokens += self.prefill_time(pos[i], k); batch.append((i, k)); budget -= k
                running.append(i); waiting.remove(i); state[i] = "running"
            if not batch:
                # idle: jump to the next event (arrival or load completion)
                nxt = [reqs[ai]["t_arr"]] if ai < n else []
                nxt += [load_done[i] for i in waiting if state[i] == "loading"] + [ready_at[i] for i in waiting if state[i] == "ready" and ready_at[i] > t]
                if not nxt: break
                t = max(t, min(nxt)); continue
            dt = P["c_step"] + tokens + n_dec * P["c_dec"]; t_end = t + dt
            for i, k in batch:
                if k > 0:
                    prefill_left[i] -= k; pos[i] += k
                    if prefill_left[i] == 0: first[i] = t_end
                else:
                    out_left[i] -= 1
                if prefill_left[i] == 0 and out_left[i] <= 0 and done[i] is None:
                    done[i] = t_end; running.remove(i); state[i] = "done"
            t = t_end
        return [dict(rid=r["rid"], tier=r["tier"], L=r["L"], t_arr=r["t_arr"], ttft_s=(first[i] - r["t_arr"]) if first[i] is not None else None, done_s=done[i]) for i, r in enumerate(reqs)]

def load_requests(path, grp):
    R = []
    for r in csv.DictReader(open(path)):
        if r["grp"] != grp or r["status"] != "200": continue
        R.append(dict(rid=r["rid"], t_arr=float(r["send_mono"]), L=int(float(r["prompt_tokens"])), tier=r["tier"], out=8, bytes=float(r["retrieve_bytes"] or 0), ttft_meas=float(r["ttft_client_ms"]) / 1000))
    R.sort(key=lambda x: x["t_arr"]); t0 = R[0]["t_arr"]
    for r in R: r["t_arr"] -= t0
    return R

if __name__ == "__main__":
    path, grp, pj = sys.argv[1:4]; policies = sys.argv[4:] or ["vllm", "zero", "srpt", "hits"]
    P = json.load(open(pj)) if pj != "-" else {}; R = load_requests(path, grp)
    for r in R: r["bytes"] = r["bytes"] or (r["L"] * DEFAULT["kv_bytes"] if r["tier"] == "host" else 0)
    sim = Sim(P)
    def q(v, p): v = sorted(v); return v[min(len(v) - 1, int(round(p * (len(v) - 1))))]
    meas = [r["ttft_meas"] for r in R]; print(f"measured   n={len(R)} TTFT mean {sum(meas)/len(meas)*1000:.0f} ms p50 {q(meas,.5)*1000:.0f} p95 {q(meas,.95)*1000:.0f} p99 {q(meas,.99)*1000:.0f}")
    for pol in policies:
        res = sim.run(R, pol); v = [x["ttft_s"] for x in res if x["ttft_s"] is not None]
        print(f"{pol:10s} n={len(v)} TTFT mean {sum(v)/len(v)*1000:.0f} ms p50 {q(v,.5)*1000:.0f} p95 {q(v,.95)*1000:.0f} p99 {q(v,.99)*1000:.0f}")
