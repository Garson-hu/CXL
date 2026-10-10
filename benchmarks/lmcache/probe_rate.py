#!/usr/bin/env python3
"""How fast can vLLM + LMCache on c28's 8 GB GPU serve Mooncake-trace requests? (2026-10-10, feasibility probe)
Builds token prompts from a Mooncake trace (each 512-token hash block -> a fixed pseudo-random token sequence, so
requests that share hash blocks share prefixes), sends the first N requests at once with 1 output token, and reports
prompt tokens per second and how many prompt tokens were cached. LMCache's own log lines (stored / retrieved bytes,
throughput) go to stderr. Environment: /mnt/local/ghu4/envs/lmcache.
usage: probe_rate.py <trace.jsonl> <n_requests> [max_model_len=16384] [model] [cpu_cache_GB=40]"""
import json, os, random, sys, time
os.environ.setdefault("HF_HOME", "/mnt/local/ghu4/hf")
os.environ.setdefault("LMCACHE_CHUNK_SIZE", "256"); os.environ.setdefault("LMCACHE_LOCAL_CPU", "True")
os.environ.setdefault("LMCACHE_MAX_LOCAL_CPU_SIZE", sys.argv[5] if len(sys.argv) > 5 else "40")
from vllm import LLM, SamplingParams
from vllm.inputs import TokensPrompt
from vllm.config import KVTransferConfig

trace, n = sys.argv[1], int(sys.argv[2])
max_len = int(sys.argv[3]) if len(sys.argv) > 3 else 16384
model = sys.argv[4] if len(sys.argv) > 4 else "Qwen/Qwen2.5-1.5B-Instruct"
cache = {}
def block_tokens(h):
    if h not in cache:
        rng = random.Random(h * 2654435761 + 12345); cache[h] = [rng.randrange(1000, 150000) for _ in range(512)]
    return cache[h]
prompts, skipped = [], 0
for line in open(trace):
    if len(prompts) >= n: break
    r = json.loads(line); toks = [t for h in r["hash_ids"] for t in block_tokens(h)][: r["input_length"]]
    if len(toks) > max_len - 8: toks = toks[: max_len - 8]; skipped += 1
    prompts.append(TokensPrompt(prompt_token_ids=toks))
llm = LLM(model=model, max_model_len=max_len, gpu_memory_utilization=0.85, enforce_eager=True, dtype="float16",
          kv_transfer_config=KVTransferConfig(kv_connector="LMCacheConnectorV1", kv_role="kv_both"))
total = sum(len(p["prompt_token_ids"]) for p in prompts)
t0 = time.time(); outs = llm.generate(prompts, SamplingParams(temperature=0, max_tokens=1)); dt = time.time() - t0
cached = sum((o.num_cached_tokens or 0) for o in outs)
print(f"PROBE requests {len(prompts)} (truncated to {max_len}: {skipped}), prompt tokens {total}, wall {dt:.1f} s, "
      f"{total / dt:.0f} prompt tokens/s, vLLM-cached tokens {cached} ({cached / total:.1%}), computed {(total - cached) / dt:.0f} tokens/s", flush=True)
