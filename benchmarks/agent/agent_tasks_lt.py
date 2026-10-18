"""Long-tool agent workload for the RQ1-B reuse-horizon validation (2026-10-17): a data-engineering assistant whose tools
REALLY execute (pandas scans of multi-million-row CSV files, a pytest suite, model-written Python in a subprocess).
Tool durations are measured wall-clock of real work on c28's CPUs, not sleeps; they depend on the dataset size
(1.5M–6M rows) and on how many agents run tools at the same time. Deterministic (seeded) data and tasks.

  python agent_tasks_lt.py gen [root]        generate the datasets (once; ~2 GB under /mnt/local/ghu4/agent-data)
  python agent_tasks_lt.py tool <name> <arg> run one tool call (used as a subprocess by run_agent.py)
  python agent_tasks_lt.py tasks <n>         print the task list"""
import json, os, re, subprocess, sys, time

ROOT = os.environ.get("AGENT_DATA_ROOT", "/mnt/local/ghu4/agent-data")
NAMES = ["orders_eu", "orders_us", "orders_apac", "sensors_plant_a", "sensors_plant_b", "sensors_plant_c", "weblogs_jan", "weblogs_feb", "weblogs_mar",
         "payments_q1", "payments_q2", "payments_q3", "inventory_2024", "inventory_2025", "shipments_north", "shipments_south", "tickets_support",
         "tickets_sales", "energy_meters", "water_meters", "fleet_telemetry", "ad_impressions", "ad_clicks", "returns_2025"]
REGIONS = ["north", "south", "east", "west", "central"]; PRODUCTS = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]; STATUS = ["ok", "late", "cancelled", "refunded"]
def rows_of(i): return 1_500_000 + (i * 7919 * 53) % 4_500_001   # 1.5M … 6.0M rows, deterministic per dataset (CSV 100–420 MB)

def gen(root=ROOT):
    import numpy as np, pandas as pd
    os.makedirs(root, exist_ok=True); man = {}
    for i, n in enumerate(NAMES):
        p = f"{root}/{n}.csv"; N = rows_of(i)
        if not os.path.exists(p):
            rng = np.random.default_rng(100 + i)
            df = pd.DataFrame({"id": np.arange(N), "region": rng.choice(REGIONS, N), "product": rng.choice(PRODUCTS, N), "units": rng.integers(0, 50, N),
                               "price": np.round(rng.uniform(1, 500, N), 2), "status": rng.choice(STATUS, N, p=[0.8, 0.1, 0.06, 0.04]),
                               "ts": pd.to_datetime("2025-01-01") + pd.to_timedelta(rng.integers(0, 365 * 86400, N), unit="s")})
            if i % 5 == 1: df.loc[rng.integers(0, N, 3), "price"] = -1.0                    # planted defects: some checks fail
            if i % 5 == 3: df.loc[rng.integers(0, N, 5), "units"] = -3
            df.to_csv(p, index=False)
        man[n] = dict(rows=N, bytes=os.path.getsize(p)); print(n, N, flush=True)
    json.dump(man, open(f"{root}/manifest.json", "w"), indent=1)
    tests = f'''import os, pandas as pd, pytest
NAME = os.environ["DS"]; ROOT = "{root}"
@pytest.fixture(scope="module")
def df(): return pd.read_csv(f"{{ROOT}}/{{NAME}}.csv")
def test_ids_unique(df): assert df["id"].is_unique
def test_no_null_ids(df): assert df["id"].notna().all()
def test_price_positive(df): assert (df["price"] > 0).all()
def test_units_non_negative(df): assert (df["units"] >= 0).all()
def test_status_values(df): assert set(df["status"].unique()) <= {set(STATUS)!r}
def test_region_values(df): assert set(df["region"].unique()) <= {set(REGIONS)!r}
def test_product_values(df): assert set(df["product"].unique()) <= {set(PRODUCTS)!r}
def test_timestamps_parse(df): assert pd.to_datetime(df["ts"]).notna().all()
def test_timestamps_in_2025(df): t = pd.to_datetime(df["ts"]); assert (t.dt.year == 2025).all()
def test_row_count(df): assert len(df) > 100000
def test_no_duplicate_rows(df): assert not df.sort_values(["region", "product", "ts", "id"]).duplicated(subset=["region", "product", "ts", "units", "price"]).any() or True
def test_group_totals_consistent(df): g = df.groupby(["region", "product"])["units"].sum(); assert abs(g.sum() - df["units"].sum()) == 0
def test_price_units_correlation_finite(df): assert pd.notna(df[["price", "units"]].corr().iloc[0, 1])
'''
    open(f"{root}/test_dataset.py", "w").write(tests)

# ------------------------------------------------------------------ tools (real execution)
def _manifest(): return json.load(open(f"{ROOT}/manifest.json"))
def _name(arg):
    a = re.sub(r"[^a-z0-9_]", "", arg.strip().lower().replace("-", "_").replace(".csv", ""))
    return a if a in NAMES else None

def list_datasets(arg: str) -> str:
    m = _manifest(); return "\n".join(f"{n}: {m[n]['rows']} rows" for n in NAMES)

def profile_dataset(arg: str) -> str:
    import pandas as pd
    n = _name(arg)
    if not n: return f"Unknown dataset '{arg}'. Call list_datasets to see the names."
    df = pd.read_csv(f"{ROOT}/{n}.csv")
    out = [f"dataset {n}: {len(df)} rows, columns {list(df.columns)}"]
    for c in ("units", "price"): out.append(f"{c}: mean {df[c].mean():.3f}, median {df[c].median():.3f}, p90 {df[c].quantile(0.9):.3f}, min {df[c].min()}, max {df[c].max()}, std {df[c].std():.3f}")
    out.append("status counts: " + ", ".join(f"{k} {v}" for k, v in df["status"].value_counts().items()))
    out.append("regions: " + ", ".join(sorted(df["region"].unique())) + "; products: " + ", ".join(sorted(df["product"].unique())))
    return "\n".join(out)

def aggregate(arg: str) -> str:
    """arg: '<dataset>: <sum|mean|count|max|min> <column> by <column>'  e.g. 'orders_eu: sum units by region'"""
    import pandas as pd
    m = re.match(r"\s*([A-Za-z0-9_\-\.]+)\s*[:,]\s*(sum|mean|count|max|min|median)\s+(\w+)(?:\s+by\s+(\w+))?\s*$", arg, re.I)
    if not m: return "Argument format: '<dataset>: <sum|mean|count|max|min|median> <column> by <column>', e.g. 'orders_eu: sum units by region'."
    n = _name(m.group(1)); op, col, by = m.group(2).lower(), m.group(3).lower(), (m.group(4) or "").lower()
    if not n: return f"Unknown dataset '{m.group(1)}'. Call list_datasets to see the names."
    df = pd.read_csv(f"{ROOT}/{n}.csv")
    if col not in df.columns and op != "count": return f"Unknown column '{col}'. Columns: {list(df.columns)}"
    if by and by not in df.columns: return f"Unknown group column '{by}'. Columns: {list(df.columns)}"
    if by:
        g = df.groupby(by)[col if col in df.columns else "id"]; r = getattr(g, "size" if op == "count" else op)()
        r = r.sort_values(ascending=False); return f"{op} of {col} by {by} in {n}:\n" + "\n".join(f"  {k}: {v:.2f}" if isinstance(v, float) else f"  {k}: {v}" for k, v in r.items())
    v = len(df) if op == "count" else getattr(df[col], op)(); return f"{op} of {col} in {n}: {v:.2f}" if isinstance(v, float) else f"{op} of {col} in {n}: {v}"

def run_checks(arg: str) -> str:
    n = _name(arg)
    if not n: return f"Unknown dataset '{arg}'. Call list_datasets to see the names."
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"{ROOT}/test_dataset.py"], env=dict(os.environ, DS=n), capture_output=True, text=True, timeout=600)
    lines = [l for l in r.stdout.strip().split("\n") if l.strip()]
    summary = lines[-1] if lines else "(no output)"; fails = [l for l in lines if l.startswith("FAILED")]
    return f"checks on {n}: {summary}" + ("\n" + "\n".join(fails[:10]) if fails else "")

def python_exec(arg: str) -> str:
    """Runs model-written Python with pandas; the dataset directory is ROOT; stdout is returned (truncated)."""
    code = arg.strip()
    if code.startswith("```"): code = re.sub(r"^```[a-z]*\n|\n```$", "", code)
    pre = f"import os, sys, json, math\nimport pandas as pd, numpy as np\nROOT = {ROOT!r}\ndef load(name): return pd.read_csv(f'{{ROOT}}/{{name}}.csv')\n"
    try:
        r = subprocess.run([sys.executable, "-c", pre + code], capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired: return "Error: the code ran for more than 120 s and was stopped."
    out = (r.stdout or "")[-1500:]; err = (r.stderr or "").strip().split("\n")[-1][:300] if r.returncode else ""
    return (out if out.strip() else "(no output; use print)") + (f"\nError: {err}" if err else "")

TOOLS = {"list_datasets": list_datasets, "profile_dataset": profile_dataset, "aggregate": aggregate, "run_checks": run_checks, "python_exec": python_exec}
TOOL_DOCS = {
    "list_datasets": "List the available datasets and their row counts. Argument: ignored (pass '').",
    "profile_dataset": "Load one dataset and return its row count, columns, basic statistics of units and price, status counts, regions and products. Argument: the dataset name, for example 'orders_eu'. Takes a few seconds.",
    "aggregate": "Compute one aggregate over a dataset. Argument: '<dataset>: <sum|mean|count|max|min|median> <column> by <column>', for example 'orders_eu: sum units by region' or 'payments_q1: mean price'. Returns the values per group. Takes a few seconds.",
    "run_checks": "Run the data-quality test suite (13 pytest checks) on one dataset. Argument: the dataset name. Returns the pytest summary and the failed checks. Takes tens of seconds on large datasets.",
    "python_exec": "Run Python code with pandas available; use load('<dataset>') to get a DataFrame and print() the result. Argument: the code. Use only when the other tools cannot answer.",
}
SYSTEM = """You are a data-engineering assistant for an analytics team. You answer questions about 24 operational datasets (orders, sensors, web logs, payments, inventory, shipments, tickets, meters, telemetry, ads, returns), each a CSV with the columns id, region, product, units, price, status and ts. You can only see the data through the tools; every number in your answer must come from a tool result in this conversation.

Tools
- list_datasets(''): the dataset names and row counts.
- profile_dataset(name): row count, columns and basic statistics of one dataset.
- aggregate('<dataset>: <op> <column> by <column>'): one aggregate, with op one of sum, mean, count, max, min, median; the 'by' part is optional. Example: aggregate('orders_eu: sum units by region').
- run_checks(name): runs the 13 data-quality checks on one dataset and reports passed and failed checks.
- python_exec(code): runs Python with pandas; load('<dataset>') returns the DataFrame; print the result. Use it only when the other tools cannot answer the question.

Procedure
1. Read the question and decide which dataset(s) and which tool each step needs. Use the dataset names exactly as given in the question.
2. Make exactly one tool call per step and wait for its result before the next call; later calls depend on earlier results.
3. When the question has several parts, do them in order: for example run the checks first, then compute the aggregate.
4. When all parts are answered, reply with two or three plain sentences that state the numbers with their units and stop. Do not call any tool after you have the answer, and do not ask the user questions.

Rules
- Never guess a number; if a tool fails, read its error message and call it again with a corrected argument.
- Do not profile a dataset that the question does not mention.
- The tools take several seconds on large datasets; that is normal.
- Round to two decimals. Units are counts for units, currency units for price.
- Quote the pytest summary line when you report checks (for example '9 passed, 1 failed')."""

KINDS = ["profile", "agg_by", "checks", "checks_then_agg", "compare", "python"]; WEIGHTS = [0.18, 0.22, 0.17, 0.2, 0.13, 0.1]
def make_tasks(n, seed=11):
    import random
    rng = random.Random(seed); out = []
    for i in range(n):
        k = rng.choices(KINDS, WEIGHTS)[0]; a, b = rng.sample(NAMES, 2); op = rng.choice(["sum", "mean", "max"]); col = rng.choice(["units", "price"]); by = rng.choice(["region", "product", "status"])
        if k == "profile": p = f"Profile the dataset {a}: how many rows does it have and what is the mean price?"; calls = 2
        elif k == "agg_by": p = f"In dataset {a}, compute the {op} of {col} by {by}. Which {by} has the largest value, and what is it?"; calls = 2
        elif k == "checks": p = f"Run the data-quality checks on dataset {a} and report how many checks passed and which ones failed."; calls = 2
        elif k == "checks_then_agg": p = f"First run the data-quality checks on dataset {a}, then compute the {op} of {col} by {by} in the same dataset. Report the check summary and the top {by}."; calls = 3
        elif k == "compare": p = f"Compare datasets {a} and {b}: which one has more rows, and what is the total units of each?"; calls = 3
        else: p = f"Using python_exec, compute the median of {col} in dataset {a} and the number of rows with status 'late'. Report both numbers."; calls = 2
        out.append(dict(task=i, kind=k, prompt=p, expected=None, expected_calls=calls, facilities=[a] if k != "compare" else [a, b]))
    return out

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "tasks"
    if cmd == "gen": gen(sys.argv[2] if len(sys.argv) > 2 else ROOT)
    elif cmd == "tool":
        t0 = time.time(); r = TOOLS[sys.argv[2]](sys.argv[3] if len(sys.argv) > 3 else ""); sys.stdout.write(r)
    else:
        for t in make_tasks(int(sys.argv[2]) if len(sys.argv) > 2 else 8): print(t)
