#!/usr/bin/env python3
"""Fit the training window-hit relationship H = f(W, C) (Task B4 of the 2026-10-27 exploratory study) on the sweep CSVs of
train_prefetch_sim.py. For one sweep (one storage bandwidth / availability / speed), the curves H(W) per capacity C are fitted with
three simple forms, each anchored at the measured no-prefetch point H0(C) = H(W = 0) and a plateau H1(C):
   exp:  H = H0 + (H1 - H0) (1 - exp(-W / tau))              rat:  H = H0 + (H1 - H0) W / (W + tau)
   ramp: H = H0 + (H1 - H0) min(1, W / W*)                   (a knee: linear until the window covers the fetch latency, then flat)
with (H1, tau | W*) fitted per capacity by least squares on a grid, then tau(C) / H1(C) summarized. Validation: leave-one-capacity-out
(fit the per-capacity parameters on the other capacities, predict the held-out curve by interpolating the parameters in log C) and
a held-out sweep (another bandwidth) if given. Prints the per-form errors and writes <dir>/fit.json for the figure.
usage: train_window_fit.py <sim dir> <sweep csv> [--held-out other.csv]"""
import csv, json, math, os, sys
D = sys.argv[1]; F = sys.argv[2]; HO = sys.argv[sys.argv.index("--held-out") + 1] if "--held-out" in sys.argv else None
def load(f):
    rows = list(csv.DictReader(open(f))); cur = {}
    for r in rows:
        C = float(r["cap_gib"]); cur.setdefault(C, []).append((float(r["window_s"]), float(r["hit_rate"])))
    return {C: sorted(v) for C, v in cur.items()}
cur = load(f"{D}/{F}" if not os.path.isabs(F) else F)
FORMS = {"exp": lambda W, p: 1 - math.exp(-W / p), "rat": lambda W, p: W / (W + p), "ramp": lambda W, p: min(1.0, W / p)}
def fit_curve(pts, form):
    H0 = pts[0][1]; best = None
    for p in [0.25 * 1.2 ** k for k in range(60)]:                                   # tau / W* from 0.25 s to ~14,000 s
        g = [FORMS[form](W, p) for W, _ in pts]; num = sum((h - H0) * gi for (W, h), gi in zip(pts, g)); den = sum(gi * gi for gi in g)
        a = num / den if den > 0 else 0.0; a = max(0.0, min(1.0 - H0, a)); err = sum((H0 + a * gi - h) ** 2 for (W, h), gi in zip(pts, g))
        if best is None or err < best[0]: best = (err, p, H0 + a)
    return dict(H0=H0, H1=best[2], p=best[1], rmse=math.sqrt(best[0] / len(pts)))
def predict(form, H0, H1, p, W): return H0 + (H1 - H0) * FORMS[form](W, p)
out = dict(sweep=F, forms={}); caps = sorted(c for c in cur if c < 1e9)
for form in FORMS:
    per = {C: fit_curve(cur[C], form) for C in cur}
    # leave-one-capacity-out: interpolate p and H1 in log C from the neighbours
    loo = []
    for C in caps:
        others = [c for c in caps if c != C]
        lo = max([c for c in others if c < C], default=None); hi = min([c for c in others if c > C], default=None)
        if lo is None or hi is None: continue
        w = (math.log(C) - math.log(lo)) / (math.log(hi) - math.log(lo))
        p = math.exp((1 - w) * math.log(per[lo]["p"]) + w * math.log(per[hi]["p"])); H1 = (1 - w) * per[lo]["H1"] + w * per[hi]["H1"]; H0 = cur[C][0][1]
        loo += [(h, predict(form, H0, H1, p, W)) for W, h in cur[C]]
    rm = math.sqrt(sum((a - b) ** 2 for a, b in loo) / len(loo)) if loo else None
    out["forms"][form] = dict(per_capacity={str(C): per[C] for C in per}, rmse_fit=math.sqrt(sum(per[C]["rmse"] ** 2 * len(cur[C]) for C in per) / sum(len(cur[C]) for C in per)), rmse_loo=rm, max_abs_loo=(max(abs(a - b) for a, b in loo) if loo else None))
    print(f"{form:5s}: fit RMSE {out['forms'][form]['rmse_fit']:.4f}; leave-one-capacity-out RMSE {rm if rm is None else round(rm, 4)} max |err| {out['forms'][form]['max_abs_loo'] if out['forms'][form]['max_abs_loo'] is None else round(out['forms'][form]['max_abs_loo'], 4)}")
    for C in sorted(per): print(f"   C {C:>8g} GiB: H0 {per[C]['H0']:.3f} H1 {per[C]['H1']:.3f} {'tau' if form != 'ramp' else 'W*'} {per[C]['p']:.1f} s rmse {per[C]['rmse']:.4f}")
best = min(out["forms"], key=lambda f: (out["forms"][f]["rmse_loo"] if out["forms"][f]["rmse_loo"] is not None else 9))
out["best"] = best; print("best form by leave-one-capacity-out:", best)
pts = []
for C in cur:
    f_ = out["forms"][best]["per_capacity"][str(C)]
    pts += [dict(C=C, W=W, measured=h, fitted=predict(best, f_["H0"], f_["H1"], f_["p"], W), held_out=False) for W, h in cur[C]]
if HO:
    ho = load(HO); errs = []
    for C in ho:
        if str(C) not in out["forms"][best]["per_capacity"]: continue
        f_ = out["forms"][best]["per_capacity"][str(C)]; H0 = ho[C][0][1]
        for W, h in ho[C]:
            pr = predict(best, H0, f_["H1"], f_["p"], W); errs.append((h - pr) ** 2); pts.append(dict(C=C, W=W, measured=h, fitted=pr, held_out=True))
    out["held_out"] = dict(file=HO, rmse=math.sqrt(sum(errs) / len(errs)) if errs else None); print(f"held-out sweep {os.path.basename(HO)}: RMSE {out['held_out']['rmse']:.4f} with the fitted (H1, {'tau' if best != 'ramp' else 'W*'}) and the held-out sweep's own H0")
out["points"] = pts; out["form"] = {"exp": "H = H0 + (H1 − H0)(1 − e^(−W/τ))", "rat": "H = H0 + (H1 − H0) W/(W + τ)", "ramp": "H = H0 + (H1 − H0) min(1, W/W*)"}[best]
json.dump(out, open(f"{D}/fit.json", "w"), indent=1); print("wrote", f"{D}/fit.json")
