#!/usr/bin/env python3
"""Real agent runs for the RQ1-B runtime validation (2026-10-17): the OpenAI Agents SDK run loop (0.24.0, unmodified)
drives Qwen2.5-1.5B-Instruct on a vLLM + LMCache server with the three local tools of agent_tasks.py. Only logging is
added: RunHooks (the SDK's own lifecycle callbacks) and a model wrapper that tags every chat-completion call with an
X-Request-Id header (vLLM uses it as the request id, so LMCache's events can be joined to the agent's events).

Events (one JSON line each, wall clock time.time() like the LMCache events):
  task_start {task, kind, prompt}           agent_start
  llm_start {n_items}                       llm_submit {rid, n_items}     (HTTP request about to be sent)
  llm_response {rid, t_submit, in_tokens, out_tokens, cached_tokens, tool_calls, decision}   (HTTP response parsed)
  llm_end {decision}                        (the SDK's on_llm_end: the runtime now knows continue / end)
  tool_start {tool} tool_call {tool, args} tool_done {tool, dur_s, rc} tool_end {tool, result_chars}   (dur_s = measured wall time of the tool)
  agent_end {output_chars}                  task_end {n_calls, ok, answer}   task_abort {reason, n_calls}
usage: run_agent.py <url> <model> <out.jsonl> <n_tasks> <workers> [max_turns=6] [seed=11]"""
import asyncio, dataclasses, importlib, json, os, sys, time, contextvars
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
agent_tasks = importlib.import_module(os.environ.get("AGENT_WORKLOAD", "agent_tasks"))   # agent_tasks (short synthetic-latency tools) or agent_tasks_lt (real long tools)
REAL_TOOLS = hasattr(agent_tasks, "TOOL_DOCS")                                             # lt workload: tools run as subprocesses, measured wall time
from agents import Agent, Runner, RunConfig, ModelSettings, RunHooks, function_tool, set_tracing_disabled
from agents.exceptions import MaxTurnsExceeded
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from openai import AsyncOpenAI

url, model_name, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
N, K = int(sys.argv[4]), int(sys.argv[5]); MAX_TURNS = int(sys.argv[6]) if len(sys.argv) > 6 else 6; SEED = int(sys.argv[7]) if len(sys.argv) > 7 else 11
set_tracing_disabled(True)
OUT = open(out_path, "a", buffering=1); CUR = contextvars.ContextVar("task")
def log(ev, **kw):
    c = CUR.get(None); d = {"t": time.time(), "ev": ev}
    if c: d["task"] = c["task"]
    d.update(kw); OUT.write(json.dumps(d) + "\n")

class TracedModel(OpenAIChatCompletionsModel):
    async def get_response(self, system_instructions, input, model_settings, tools, output_schema, handoffs, tracing, *a, **kw):
        c = CUR.get(); c["call"] += 1; rid = f"agt{c['task']:04d}c{c['call']:02d}"
        ms = dataclasses.replace(model_settings, extra_headers={**(model_settings.extra_headers or {}), "X-Request-Id": rid})
        n_items = len(input) if isinstance(input, list) else 1
        log("llm_submit", rid=rid, n_items=n_items); t0 = time.time()
        resp = await super().get_response(system_instructions, input, ms, tools, output_schema, handoffs, tracing, *a, **kw)
        calls = [getattr(it, "name", "?") for it in resp.output if getattr(it, "type", "") == "function_call"]
        u = resp.usage; det = getattr(u, "input_tokens_details", None)
        log("llm_response", rid=rid, t_submit=t0, in_tokens=u.input_tokens, out_tokens=u.output_tokens, cached_tokens=getattr(det, "cached_tokens", None) if det else None,
            tool_calls=calls, decision="continue" if calls else "end")
        return resp

class Hooks(RunHooks):
    async def on_agent_start(self, ctx, agent): log("agent_start")
    async def on_llm_start(self, ctx, agent, system_prompt, input_items): log("llm_start", n_items=len(input_items))
    async def on_llm_end(self, ctx, agent, response):
        calls = [getattr(it, "name", "?") for it in response.output if getattr(it, "type", "") == "function_call"]
        log("llm_end", decision="continue" if calls else "end", tool_calls=calls)
    async def on_tool_start(self, ctx, agent, tool): log("tool_start", tool=tool.name)
    async def on_tool_end(self, ctx, agent, tool, result): log("tool_end", tool=tool.name, result_chars=len(str(result)))
    async def on_agent_end(self, ctx, agent, output): log("agent_end", output_chars=len(str(output)))

SHORT_DOCS = {"search_reports": "Search the site reports. Argument: a facility name such as 'Heron-02', a region or a sector. Returns up to five report ids with facility names.",
              "read_report": "Read one site report in full. Argument: the report id, for example 'R-012'.",
              "calculate": "Evaluate an arithmetic expression, for example '(4820 + 3310) / 2'. Returns the numeric result."}
def make_tool(name, fn):
    async def impl(arg: str) -> str:
        log("tool_call", tool=name, args=arg[:160]); t0 = time.time()
        if REAL_TOOLS:                                                                 # real execution in a subprocess (parallel across agents)
            proc = await asyncio.create_subprocess_exec(sys.executable, agent_tasks.__file__, "tool", name, arg, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=os.environ)
            out, err = await proc.communicate(); res = out.decode(errors="replace")
            if proc.returncode: res = (res + f"\nError: tool failed (rc={proc.returncode}): {err.decode(errors='replace').strip().split(chr(10))[-1][:200]}")
            log("tool_done", tool=name, dur_s=time.time() - t0, rc=proc.returncode, result_chars=len(res)); return res[:4000]
        lat = agent_tasks.latency(name)
        if lat > 0: await asyncio.sleep(lat)
        res = fn(arg); log("tool_done", tool=name, dur_s=time.time() - t0, rc=0, result_chars=len(res)); return res
    impl.__name__ = name
    doc = (agent_tasks.TOOL_DOCS if REAL_TOOLS else SHORT_DOCS)[name]
    impl.__doc__ = doc
    return function_tool(impl, name_override=name, description_override=doc)

async def main():
    client = AsyncOpenAI(base_url=f"{url}/v1", api_key="EMPTY", timeout=600, max_retries=0)
    tools = [make_tool(n, f) for n, f in agent_tasks.TOOLS.items()]
    agent = Agent(name="site-analyst", instructions=agent_tasks.SYSTEM, tools=tools, model=TracedModel(model=model_name, openai_client=client),
                  model_settings=ModelSettings(temperature=0.0, max_tokens=256, parallel_tool_calls=False))
    tasks = agent_tasks.make_tasks(N, SEED); q = asyncio.Queue()
    for t in tasks: q.put_nowait(t)
    hooks = Hooks(); cfg = RunConfig(tracing_disabled=True)
    log("run_start", n_tasks=N, workers=K, max_turns=MAX_TURNS, seed=SEED, latency_scale=os.environ.get("AGENT_TOOL_LATENCY_SCALE", "1.0"), model=model_name, workload=agent_tasks.__name__, real_tools=REAL_TOOLS)
    async def worker(w):
        while True:
            try: t = q.get_nowait()
            except asyncio.QueueEmpty: return
            CUR.set({"task": t["task"], "call": 0})
            log("task_start", kind=t["kind"], prompt=t["prompt"], expected=t["expected"], expected_calls=t["expected_calls"], worker=w)
            try:
                res = await Runner.run(agent, input=t["prompt"], max_turns=MAX_TURNS, hooks=hooks, run_config=cfg)
                ans = str(res.final_output); ok = (t["expected"] is None) or (str(t["expected"]) in ans.replace(",", ""))
                log("task_end", n_calls=CUR.get()["call"], ok=ok, answer=ans[:300])
            except MaxTurnsExceeded as e:
                log("task_abort", reason="max_turns", n_calls=CUR.get()["call"], err=str(e)[:200])
            except Exception as e:
                log("task_abort", reason="error", n_calls=CUR.get()["call"], err=repr(e)[:300])
    await asyncio.gather(*(worker(w) for w in range(K)))
    log("run_end")

asyncio.run(main())
