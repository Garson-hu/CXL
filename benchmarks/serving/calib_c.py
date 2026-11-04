#!/usr/bin/env python3
"""Calibrate the parameters of sched_sim.py from measured runs (Experiment C, 2026-11-04):
  r0, r1, c_step   from the cold requests of an A run: engine prefill time (scheduled -> first token) vs L fitted as
                   c_step + r0 L + r1 L (L - 1) / 2 (least squares over the per-L medians)
  bw, lookup, ready  from the host hits of the same run: median effective transfer bandwidth at L >= 4096, median lookup
                   time, median transfer end -> scheduled
  c_dec            from a B run's engine-step log: median duration of decode-only steps as a function of the batch size
                   (slope; the intercept is c_step)
Writes params.json and prints the fit and its residuals.
usage: calib_c.py <A timeline csv> [<B steps csv>] <params.json>"""
import csv, json, sys

def med(v): v = sorted(v); return v[len(v) // 2]
def lstsq(X, y):
    """ordinary least squares for a few columns (normal equations, Gauss elimination)"""
    n = len(X[0]); A = [[sum(X[i][a] * X[i][b] for i in range(len(X))) for b in range(n)] for a in range(n)]; B = [sum(X[i][a] * y[i] for i in range(len(X))) for a in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(A[r][c])); A[c], A[p] = A[p], A[c]; B[c], B[p] = B[p], B[c]
        for r in range(c + 1, n):
            f = A[r][c] / A[c][c]; A[r] = [A[r][k] - f * A[c][k] for k in range(n)]; B[r] -= f * B[c]
    x = [0.0] * n
    for c in range(n - 1, -1, -1): x[c] = (B[c] - sum(A[c][k] * x[k] for k in range(c + 1, n))) / A[c][c]
    return x

a_csv = sys.argv[1]; b_csv = sys.argv[2] if len(sys.argv) > 3 else None; out = sys.argv[-1]
rows = [r for r in csv.DictReader(open(a_csv)) if r["status"] == "200"]
cold = {}; host = []
for r in rows:
    if r["case"] == "cold" and r["prefill_ms"]: cold.setdefault(int(float(r["L"])), []).append(float(r["prefill_ms"]) / 1000)
    if r["case"] == "host" and r["retrieve_GBps"]: host.append(r)
Ls = sorted(cold); y = [med(cold[L]) for L in Ls]; X = [[1.0, L, L * (L - 1) / 2] for L in Ls]
c_step, r0, r1 = lstsq(X, y)
print("prefill fit: c_step=%.4f s r0=%.3e s/token r1=%.3e s/token^2" % (c_step, r0, r1))
for L, yy, xx in zip(Ls, y, X): print(f"  L={L:6d} measured {yy*1000:8.1f} ms  fit {(c_step + r0*xx[1] + r1*xx[2])*1000:8.1f} ms")
bw = med([float(r["retrieve_GBps"]) for r in host if float(r["L"]) >= 4096]) * 1e9
lookup = med([float(r["lookup_ms"]) for r in host if r["lookup_ms"]]) / 1000; ready = med([float(r["kv_end_to_sched_ms"]) for r in host if r["kv_end_to_sched_ms"]]) / 1000
floor = med([float(r["prefill_ms"]) for r in host if r["prefill_ms"]]) / 1000
print(f"host hits: bw={bw/1e9:.2f} GB/s lookup={lookup*1000:.2f} ms ready(transfer end -> scheduled)={ready*1000:.2f} ms 1-token step floor={floor*1000:.1f} ms")
P = dict(r0=r0, r1=r1, c_step=max(c_step, 0.0), c_min=floor, bw=bw, lookup=lookup, ready=ready)
if b_csv:
    S = [r for r in csv.DictReader(open(b_csv)) if r["t_end"]]; dec = {}
    for s in S:
        tok, run = int(s["tok"]), int(s["run"])
        if 0 < tok <= run and run > 0 and tok == run: dec.setdefault(run, []).append(float(s["t_end"]) - float(s["t1"]))      # pure decode steps: one token per running request
    ks = sorted(k for k in dec if len(dec[k]) >= 5)
    if len(ks) >= 2:
        X = [[1.0, k] for k in ks]; yy = [med(dec[k]) for k in ks]; c0, c_dec = lstsq(X, yy)
        print("decode steps: c0=%.4f s + %.5f s per sequence; per batch size: %s" % (c0, c_dec, {k: round(med(dec[k]) * 1000, 1) for k in ks}))
        P["c_dec"] = max(c_dec, 0.0); P["c_step_decode"] = c0
json.dump(P, open(out, "w"), indent=1); print("written", out, P)
