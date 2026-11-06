# Raw data of docs/experiments/2026-11-04-cxl-serving-scheduling-gap.md

Start with `SUMMARY.md` in this directory: the self-contained summary of the experiment (question, platform, every run,
results per family, cross-cutting findings, answers to the brief's questions, limitations, data map, how to regenerate).

Collected from `/mnt/local/ghu4/results/2026-11-04-cxl-serving-scheduling-gap` on 2026-11-05 with `benchmarks/serving/collect_small.sh`. One directory per experiment
family (`A`, `B`, `C`, `E`, `F`, `replay` = Experiment D and the lighter-load sweep, `smoke`, `inspect`);
`*/flawed/` holds the quarantined runs listed in the report's §15.C. Per run `<tag>`: `<tag>-meta.txt`
(configuration and the monotonic/wall clock pair), `<tag>-driver.txt` (driver output), `<tag>-client.jsonl` (one
record per request as the client saw it), `<tag>-requests.csv` (per-request timeline joined from the hooks),
`<tag>-scenarios.csv` / `<tag>-replay.json` (per-group summaries). Tables (`tables*.md`) and figures (`figs/`)
are what the report embeds; `experiment-matrix.{csv,md}` is the §15.B matrix (`matrix.py`).

The bulky per-run logs stay on c28's local NVMe at `/mnt/local/ghu4/results/2026-11-04-cxl-serving-scheduling-gap` (not in git; ≈ 950 MB): `<tag>-steps.csv` (engine step
log), `<tag>-kvevents.jsonl` (LMCache event mirror), `<tag>-gpu.txt` / `<tag>-cpu.txt` (samplers),
`<tag>-vllmevt.*.jsonl` (vLLM request/step events), `<tag>-server.log`, `<tag>-lmcache.log`, `<tag>-status.txt`.
