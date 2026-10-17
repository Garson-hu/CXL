"""Deterministic agent workload for the RQ1-B runtime validation (2026-10-17): a synthetic corpus of facility reports,
three local tools (search, read, calculate) and task prompts that need 0-5 tool calls. Everything is seeded, so a run
is reproducible; tool latencies are a workload parameter (AGENT_TOOL_LATENCY_SCALE, default 1.0 = search 1.5 s,
read 1.0 s, calculate 0.3 s, standing in for remote search/API/sandbox tools; 0 disables them)."""
import os, random, re

N_FACILITIES = 48
BIRDS = ["Kestrel", "Heron", "Osprey", "Plover", "Curlew", "Gannet", "Merlin", "Sandpiper", "Kite", "Avocet", "Bittern", "Lapwing"]
REGIONS = ["North Ridge", "East Basin", "South Delta", "West Plateau", "Central Valley", "Coastal Reach"]
SECTORS = ["cold storage", "assembly", "data processing", "packaging", "water treatment", "fabrication"]

def _rid(rng): return "SR-" + "".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(5))

def _doc(rng, i):
    name = f"{BIRDS[i % len(BIRDS)]}-{i // len(BIRDS) + 1:02d}"; region = REGIONS[i % len(REGIONS)]; sector = SECTORS[(i * 7) % len(SECTORS)]; rid = _rid(rng)
    m = {y: dict(energy=rng.randrange(1200, 9800), water=rng.randrange(3000, 48000), head=rng.randrange(40, 620), uptime=round(rng.uniform(91.0, 99.8), 1), inc=rng.randrange(0, 14), cost=rng.randrange(180, 2600) * 1000) for y in (2024, 2025)}
    lead = rng.choice(["M. Okafor", "L. Brandt", "S. Tanaka", "R. Delgado", "A. Novák", "P. Mensah", "J. Kowalski", "H. Lindqvist"])
    text = f"""Site report {rid}: Facility {name} ({region}), {sector}. Reporting year 2025, with 2024 shown for comparison.

1. Overview. Facility {name} is a {sector} site in the {region} district. It was commissioned in {rng.randrange(1998, 2021)} and has a floor area of {rng.randrange(4, 60) * 1000} square metres. The site lead is {lead}. The site operates {rng.choice(['two', 'three'])} shifts on weekdays and a reduced weekend shift. The 2025 review covers utilities, workforce, reliability and incidents, and closes with the outlook for 2026.

2. Utilities. Electricity use in 2025 was {m[2025]['energy']} MWh, compared with {m[2024]['energy']} MWh in 2024. The change follows the {rng.choice(['replacement of the chiller plant', 'addition of a second production line', 'switch to LED lighting in the main hall', 'extension of the night shift', 'installation of rooftop photovoltaics', 'retrofit of the compressed-air system'])}. Water use in 2025 was {m[2025]['water']} cubic metres ({m[2024]['water']} cubic metres in 2024). Utility cost in 2025 was {m[2025]['cost']} USD.

3. Workforce. Headcount at the end of 2025 was {m[2025]['head']} ({m[2024]['head']} at the end of 2024). Contractor hours were {rng.randrange(800, 24000)} for the year. Training completion was {rng.randrange(72, 100)} percent.

4. Reliability. Uptime in 2025 was {m[2025]['uptime']} percent of scheduled hours ({m[2024]['uptime']} percent in 2024). Unplanned downtime came mainly from {rng.choice(['a transformer fault in March', 'conveyor failures in the second quarter', 'a cooling-water leak in August', 'network outages in the first quarter', 'a boiler inspection overrun', 'storm damage to the switchyard'])}. Planned maintenance windows were {rng.randrange(4, 18)} per year.

5. Incidents. {m[2025]['inc']} recordable incidents were logged in 2025 ({m[2024]['inc']} in 2024). None resulted in lost time beyond {rng.randrange(0, 9)} days. Near-miss reports were {rng.randrange(5, 90)}.

6. Outlook. For 2026 the site expects {rng.choice(['flat', 'rising', 'falling'])} energy use, a {rng.choice(['stable', 'growing', 'shrinking'])} headcount and {rng.choice(['one', 'two', 'no'])} major capital projects. The main risk is {rng.choice(['grid capacity', 'water allocation', 'staff retention', 'equipment age', 'permit renewal', 'supplier concentration'])}."""
    return dict(id=rid, name=name, region=region, sector=sector, lead=lead, m=m, text=text)

def corpus(seed=7):
    rng = random.Random(seed); return [_doc(rng, i) for i in range(N_FACILITIES)]

DOCS = corpus(); BY_ID = {d["id"]: d for d in DOCS}; BY_NAME = {d["name"].lower(): d for d in DOCS}
_LAT = {"search_reports": 1.5, "read_report": 1.0, "calculate": 0.3}
def latency(tool): return _LAT.get(tool, 0.0) * float(os.environ.get("AGENT_TOOL_LATENCY_SCALE", "1.0"))

# ------------------------------------------------------------------ tools (pure functions; the runner adds the latency)
def search_reports(query: str) -> str:
    q = [w for w in re.findall(r"[a-z0-9-]+", query.lower()) if len(w) >= 3]
    scored = []
    for d in DOCS:
        hay = f"{d['name']} {d['region']} {d['sector']} {d['id']}".lower(); s = sum(3 if w in d["name"].lower() else 1 for w in q if w in hay)
        if s: scored.append((-s, d["id"], d))
    scored.sort()
    if not scored: return "No reports matched. Try the facility name (for example 'Heron-02') or a region."
    return "\n".join(f"{d['id']}: Facility {d['name']} ({d['region']}, {d['sector']}) - site report 2025" for _, _, d in scored[:5])

def read_report(report_id: str) -> str:
    rid = report_id.strip().upper().replace(" ", "")
    if not rid.startswith("SR-"): rid = "SR-" + rid
    d = BY_ID.get(rid)
    return d["text"] if d else f"Unknown report id '{report_id}'. Report ids are codes such as SR-7K2QX that only search_reports returns; search first, then read."

def calculate(expression: str) -> str:
    e = expression.replace(",", "").replace("^", "**")
    if not re.fullmatch(r"[0-9eE+\-*/().\s%]+", e): return "Error: only numbers and + - * / ( ) are allowed."
    try: v = eval(e, {"__builtins__": {}}, {})
    except Exception as ex: return f"Error: {ex}"
    return f"{v:.4f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)

TOOLS = {"search_reports": search_reports, "read_report": read_report, "calculate": calculate}

# ------------------------------------------------------------------ prompts
SYSTEM = """You are the site-operations analyst assistant of a company that runs 48 industrial facilities. You answer questions about the facilities from their 2025 site reports, which you can only see through the tools below. Never answer from memory: every number in your answer must come from a report you read in this conversation.

Tools
- search_reports(query): returns up to five matching report ids with the facility name and region. Search by facility name (for example "Osprey-03"), by region (for example "East Basin") or by sector.
- read_report(report_id): returns the full text of one report. Report ids are random codes such as SR-7K2QX; they cannot be guessed and are only given by search_reports. Read every report you need in full before you compute anything.
- calculate(expression): evaluates an arithmetic expression such as (4820 + 3310) / 2. Use it for every sum, difference, ratio or percentage; do not do arithmetic in your head.

Procedure
1. Identify every facility the question mentions. Call search_reports once per facility to get its report id. Never call read_report with an id that search_reports has not returned in this conversation.
2. Call read_report for each id. Extract the requested metric for the requested year. The reports give 2025 figures and 2024 figures side by side; take care to use the year the question asks for.
3. If the question asks for a total, a difference, an average or a comparison, call calculate with the exact numbers from the reports.
4. When the answer is complete, reply with one or two plain sentences that state the numbers and their units, and stop. Do not call any tool after you have the answer, and do not ask the user questions.

Metric definitions
- Electricity use is reported in MWh for the whole year.
- Water use is reported in cubic metres for the whole year.
- Headcount is the number of employees at the end of the year, contractors excluded.
- Uptime is the percentage of scheduled hours in which the site produced; a difference between two uptimes is expressed in percentage points.
- Recordable incidents are counted per year; near-miss reports are a separate figure.
- Utility cost is in USD for the whole year.

Rules
- Make exactly one tool call per step and wait for its result before deciding the next call; later calls depend on earlier results.
- If search_reports returns several candidates, choose the one whose facility name matches the question exactly.
- If a report cannot be found, say so in the final answer instead of guessing.
- Keep the final answer short. Do not repeat the report text. Do not add recommendations.
- Units: write MWh, cubic metres, percent, percentage points and USD exactly as the reports do.
- Rounding: keep one decimal for percentages and whole numbers for everything else.
- If a value for 2024 is asked, use the 2024 figure, otherwise use 2025."""

KINDS = ["energy", "water_total", "uptime_cmp", "headcount", "nocall", "incidents_diff"]
WEIGHTS = [0.25, 0.22, 0.2, 0.13, 0.08, 0.12]

def make_tasks(n, seed=11):
    rng = random.Random(seed); out = []
    for i in range(n):
        k = rng.choices(KINDS, WEIGHTS)[0]; a, b = rng.sample(DOCS, 2); y = 2025
        if k == "energy": p = f"What was the electricity use of facility {a['name']} in {y}, in MWh?"; exp = a["m"][y]["energy"]; calls = 2
        elif k == "water_total": p = f"What was the combined {y} water use of facilities {a['name']} and {b['name']}, in cubic metres?"; exp = a["m"][y]["water"] + b["m"][y]["water"]; calls = 5
        elif k == "uptime_cmp": p = f"Which of facilities {a['name']} and {b['name']} had the higher uptime in {y}, and by how many percentage points?"; exp = round(abs(a["m"][y]["uptime"] - b["m"][y]["uptime"]), 1); calls = 5
        elif k == "headcount": p = f"How many employees did facility {a['name']} have at the end of {y}?"; exp = a["m"][y]["head"]; calls = 2
        elif k == "incidents_diff": p = f"How many more recordable incidents did facility {a['name']} log in {y} than in 2024? Give the difference."; exp = a["m"][y]["inc"] - a["m"][2024]["inc"]; calls = 3
        else: p = rng.choice(["In one sentence, what does the uptime metric in the site reports measure?", "In one sentence, what is the difference between a recordable incident and a near-miss report?", "In one sentence, which unit do the site reports use for water use?"]); exp = None; calls = 0
        out.append(dict(task=i, kind=k, prompt=p, expected=exp, expected_calls=calls, facilities=[a["name"], b["name"]] if k in ("water_total", "uptime_cmp") else ([a["name"]] if k != "nocall" else [])))
    return out

if __name__ == "__main__":
    import sys
    try:
        from transformers import AutoTokenizer; tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")
        print("system prompt tokens:", len(tok(SYSTEM)["input_ids"])); print("doc tokens (first 5):", [len(tok(d["text"])["input_ids"]) for d in DOCS[:5]])
    except Exception as e: print("tokenizer unavailable:", e)
    for t in make_tasks(int(sys.argv[1]) if len(sys.argv) > 1 else 6): print(t)
    print(search_reports("Heron-02")); print(read_report(DOCS[1]["id"])[:300]); print(calculate("(4820 + 3310) / 2"))
