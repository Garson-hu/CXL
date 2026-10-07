#!/usr/bin/env python3
"""Smoke test of the LMCache + vLLM environment on the 8 GB GPU (env /mnt/local/ghu4/envs/lmcache; HF_HOME on the local disk):
loads a small model, runs a long shared-prefix prompt twice and reports the time to first token of each, with LMCache's
CPU offload holding the prefix. usage: smoke_vllm_lmcache.py [model]"""
import os, sys, time
os.environ.setdefault("HF_HOME", "/mnt/local/ghu4/hf")
os.environ.setdefault("LMCACHE_CHUNK_SIZE", "256"); os.environ.setdefault("LMCACHE_LOCAL_CPU", "True"); os.environ.setdefault("LMCACHE_MAX_LOCAL_CPU_SIZE", "8")
from vllm import LLM, SamplingParams
from vllm.config import KVTransferConfig
model = sys.argv[1] if len(sys.argv) > 1 else "Qwen/Qwen2.5-1.5B-Instruct"
llm = LLM(model=model, max_model_len=8192, gpu_memory_utilization=0.85, enforce_eager=True, dtype="float16",
          kv_transfer_config=KVTransferConfig(kv_connector="LMCacheConnectorV1", kv_role="kv_both"))
prefix = ("The following is a long technical document about memory systems. " * 300)[:12000]
sp = SamplingParams(temperature=0, max_tokens=16)
for i, q in enumerate(["Summarize it in one sentence.", "What is its main topic?"]):
    t0 = time.time(); out = llm.generate([prefix + "\n\nQuestion: " + q], sp); dt = time.time() - t0
    m = out[0].metrics
    print(f"run {i}: total {dt:.2f} s, time to first token {(m.first_token_time - m.arrival_time) if m and m.first_token_time else float('nan'):.3f} s, prompt tokens {len(out[0].prompt_token_ids)}, text: {out[0].outputs[0].text[:60]!r}", flush=True)
