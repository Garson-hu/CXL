#!/usr/bin/env python3
"""Reuse-horizon statistics of a PUBLIC agent trace with real timestamps (RQ1-B reuse-horizon validation, 2026-10-17):
the Exgentic/agent-llm-traces dataset on Hugging Face (CDLA-Permissive-2.0; 1,781 agent sessions, OpenTelemetry-style
spans of every LLM chat call with start_time / end_time / input and output tokens / finish reason; harnesses such as
Claude Code running benchmarks such as AppWorld with hosted models). The spans are the LLM calls; the gap between the end
of one call and the start of the next is the real time the harness spent outside the model (tool execution, environment,
framework), i.e. the lead time a continue signal would have, and start-to-start is the reuse horizon of the previous
prompt's KV. Download: data/train-*-of-00039.parquet from https://huggingface.co/datasets/Exgentic/agent-llm-traces.
usage: agent_trace_public_stats.py <parquet_dir> <out_dir>"""
import collections, glob, json, os, sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.grid": True, "grid.color": "#e6e6e6", "legend.frameon": False, "svg.fonttype": "none"})
def q(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else float("nan")
rows = []; sessions = []
for f in sorted(glob.glob(f"{src}/*.parquet")):
    df = pd.read_parquet(f, columns=["harness", "benchmark", "models", "session_id", "spans"])
    for _, r in df.iterrows():
        sp = r["spans"]; sp = json.loads(sp) if isinstance(sp, str) else list(sp)
        calls = []
        for x in sp:
            a = x.get("attributes") or {}
            if isinstance(a, str):
                try: a = json.loads(a)
                except Exception: a = {}
            if a.get("gen_ai.operation.name") != "chat" and not str(x.get("name", "")).startswith("chat"): continue
            try: t0 = pd.Timestamp(x["start_time"]).timestamp(); t1 = pd.Timestamp(x["end_time"]).timestamp()
            except Exception: continue
            fr = str(a.get("gen_ai.response.finish_reasons", ""))
            calls.append(dict(t0=t0, t1=t1, in_tok=a.get("gen_ai.usage.input_tokens"), out_tok=a.get("gen_ai.usage.output_tokens"), tool=("tool" in fr)))
        calls.sort(key=lambda c: c["t0"])
        if len(calls) < 2: continue
        gaps = [calls[i + 1]["t0"] - calls[i]["t1"] for i in range(len(calls) - 1)]
        hor = [calls[i + 1]["t0"] - calls[i]["t0"] for i in range(len(calls) - 1)]
        lat = [c["t1"] - c["t0"] for c in calls]
        ins = [c["in_tok"] for c in calls if c["in_tok"] is not None]
        sessions.append(dict(harness=r["harness"], benchmark=r["benchmark"], model=str(list(r["models"]) if not isinstance(r["models"], str) else r["models"])[:60], session=r["session_id"], calls=len(calls),
                             duration_s=calls[-1]["t1"] - calls[0]["t0"], gap_p50=q(gaps, .5), gap_p90=q(gaps, .9), horizon_p50=q(hor, .5), llm_p50=q(lat, .5), in_tok_p50=q(ins, .5) if ins else None, in_tok_max=max(ins) if ins else None,
                             tool_share=sum(c["tool"] for c in calls) / len(calls)))
        for i, g in enumerate(gaps): rows.append(dict(benchmark=r["benchmark"], harness=r["harness"], session=r["session_id"], step=i, gap_s=g, horizon_s=hor[i], llm_s=lat[i], in_tok=calls[i]["in_tok"], next_in_tok=calls[i + 1]["in_tok"], tool_call=calls[i]["tool"]))
S = pd.DataFrame(sessions); G = pd.DataFrame(rows)
S.to_csv(f"{out}/public-agent-sessions.csv", index=False); G.to_csv(f"{out}/public-agent-gaps.csv", index=False)
summ = dict(sessions=len(S), llm_calls=int(S["calls"].sum()), per_benchmark={},
            note="In most harnesses the chat spans end at request submission (median span length ~1 ms), so LLM latency and tool time cannot be separated; "
                 "start-to-start (horizon) is robust, end-to-start (gap) is reported on positive gaps only. Negative gaps = overlapping spans (parallel calls / sub-agents).",
            negative_gap_share=float((G["gap_s"] < 0).mean()), llm_span_lt_10ms_share=float((G["llm_s"] < 0.01).mean()))
for b, g in G.groupby("benchmark"):
    gs = [x for x in g["gap_s"].tolist() if x >= 0]; hs = g["horizon_s"].tolist(); ls = g["llm_s"].tolist(); n_s = S[S["benchmark"] == b]
    summ["per_benchmark"][b] = dict(sessions=len(n_s), calls_per_session_p50=float(n_s["calls"].median()), calls_per_session_p90=float(n_s["calls"].quantile(0.9)), session_duration_p50_s=float(n_s["duration_s"].median()),
                                    gap_p10=q(gs, .1), gap_p50=q(gs, .5), gap_p90=q(gs, .9), gap_p99=q(gs, .99), gap_share_gt_10s=sum(x > 10 for x in gs) / len(gs), gap_share_gt_60s=sum(x > 60 for x in gs) / len(gs),
                                    horizon_p10=q(hs, .1), horizon_p50=q(hs, .5), horizon_p90=q(hs, .9), horizon_p99=q(hs, .99), horizon_share_gt_10s=sum(x > 10 for x in hs) / len(hs), horizon_share_gt_30s=sum(x > 30 for x in hs) / len(hs),
                                    llm_p50=q(ls, .5), llm_p90=q(ls, .9), in_tok_p50=float(g["in_tok"].median()), in_tok_p90=float(g["in_tok"].quantile(0.9)),
                                    context_growth_per_step_p50=float((g["next_in_tok"] - g["in_tok"]).median()))
gs = [x for x in G["gap_s"].tolist() if x >= 0]; hs = G["horizon_s"].tolist()
summ["all"] = dict(gap_p10=q(gs, .1), gap_p50=q(gs, .5), gap_p90=q(gs, .9), gap_p99=q(gs, .99), horizon_p50=q(hs, .5), horizon_p90=q(hs, .9), gap_share_gt_10s=sum(x > 10 for x in gs) / len(gs), gap_share_gt_60s=sum(x > 60 for x in gs) / len(gs))
json.dump(summ, open(f"{out}/public-agent-summary.json", "w"), indent=1); print(json.dumps(summ, indent=1))
fig, axs = plt.subplots(1, 2, figsize=(12, 4.3))
for b, g in G.groupby("benchmark"):
    xs = sorted(x for x in g["horizon_s"] if x > 0); axs[0].plot(xs, [i / len(xs) for i in range(1, len(xs) + 1)], label=f"{b} (n={len(xs)})")
    xs = sorted(x for x in g["in_tok"].dropna() if x > 0); axs[1].plot(xs, [i / len(xs) for i in range(1, len(xs) + 1)], label=f"{b}")
for ax, t, xl in ((axs[0], "Reuse horizon: start of one LLM call → start of the next call of the session\n(the previous prompt's KV is re-read here; includes tool and model time)", "seconds"), (axs[1], "Prompt size per LLM call (the context that is re-read)", "input tokens")):
    ax.set_xscale("log"); ax.set_xlabel(xl); ax.set_ylabel("CDF"); ax.set_title(t, fontsize=10); ax.legend(fontsize=8)
fig.suptitle("PUBLIC TRACE: Exgentic/agent-llm-traces (real timestamps of LLM calls in agent sessions)", fontsize=10, y=1.0)
fig.tight_layout(); fig.savefig(f"{out}/fig-public-agent-gaps.png", dpi=200); fig.savefig(f"{out}/fig-public-agent-gaps.svg"); print("wrote", out)
