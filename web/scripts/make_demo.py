"""Build web/src/demo/retail_demo.json, the recorded example the web app falls back to.

Run from the repo root:  python web/scripts/make_demo.py

Every plan step is executed by the real tools in analyst/tools.py on samples/retail_orders.csv,
with real timings, and every answer is scored by analyst/grounding.py. The dataset description
and the answer prose are written here (not by a model) and the UI says so. The second answer
contains one deliberately unsupported figure so the grounding check has something to flag.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from analyst import grounding  # noqa: E402
from analyst.data import Dataset  # noqa: E402
from analyst.tools import run_tool  # noqa: E402

ds = Dataset.from_path(ROOT / "samples" / "retail_orders.csv", "Retail orders")
profile = ds.profile()


def fmt(v: float, d: int = 0) -> str:
    return f"{v:,.{d}f}"


def run(plan: list[dict]) -> list[dict]:
    out = []
    for i, step in enumerate(plan):
        t0 = time.perf_counter()
        res = run_tool(ds, step["tool"], step["args"])
        ms = max(1, int((time.perf_counter() - t0) * 1000))
        out.append({"index": i, "tool": step["tool"], "args": res["args"], "ok": True, "result": res, "ms": ms})
    return out


def finish(turn: dict, t: datetime) -> dict:
    g = grounding.check(turn["answer_md"], *[r["result"] for r in turn["results"]], question=turn["question"])
    turn.update(g)
    turn["created_at"] = t.isoformat()
    turn["events"] = []
    turn["mode"] = "recorded"
    return turn


turns = []
start = datetime(2026, 11, 18, 14, 2, tzinfo=timezone.utc)

# ---- 1 -------------------------------------------------------------------------------------
q1 = "Which region brings in the most revenue, and is it growing?"
plan1 = [
    {"tool": "group_aggregate", "args": {"by": "region", "metric": "revenue", "agg": "sum"},
     "why": "Rank regions by total revenue to find the largest."},
]
r = run(plan1)
top = r[0]["result"]["summary"]
plan1.append({"tool": "time_trend", "args": {"date_col": "order_date", "metric": "revenue", "agg": "sum", "grain": "quarter",
                                             "filters": [{"column": "region", "op": "=", "value": top["top_group"]}]},
              "why": f"Check whether {top['top_group']}'s quarterly revenue is rising or flat."})
r += run(plan1[1:])
r[1]["index"] = 1
tr = r[1]["result"]["summary"]
second = r[0]["result"]["data"][1]
q = lambda p: f"{p[:4]}-Q{(int(p[5:7]) - 1) // 3 + 1}"  # noqa: E731
turns.append(finish({
    "id": "rec1", "question": q1, "plan": plan1, "results": r,
    "answer_md": (
        f"**{top['top_group']}** is the largest region, with **${fmt(top['top_value'])}** in revenue, "
        f"**{top['top_share_pct']}%** of the total [1]. {second['region']} is close behind at ${fmt(second['sum_revenue'])}.\n\n"
        f"It is growing. Quarterly revenue in {top['top_group']} went from ${fmt(tr['first_value'])} in {q(tr['first_period'])} "
        f"to ${fmt(tr['last_value'])} in {q(tr['last_period'])}, a change of **{tr['change_pct_first_to_last']:.1f}%** [2]. "
        + (f"The latest quarter is also its best so far." if tr['peak_period'] == tr['last_period']
           else f"The best quarter was {q(tr['peak_period'])} at ${fmt(tr['peak_value'])}.")
    ),
    "key_numbers": [
        {"label": f"{top['top_group']} revenue", "value": f"${fmt(top['top_value'])}", "step": 1},
        {"label": "Share of all revenue", "value": f"{top['top_share_pct']}%", "step": 1},
        {"label": f"{q(tr['first_period'])} to {q(tr['last_period'])}", "value": f"{tr['change_pct_first_to_last']:+.1f}%", "step": 2},
    ],
    "follow_ups": ["Now split that by category and leave out returned orders",
                   f"Which months were unusually strong for {top['top_group']}?",
                   "Do bigger discounts lead to more returns?"],
}, start))

# ---- 2 (follow-up: same metric, new breakdown, one added filter) ----------------------------
q2 = "Now split that by category and leave out returned orders"
kept = {"column": "returned", "op": "=", "value": False}
plan2 = [
    {"tool": "group_aggregate", "args": {"by": "category", "metric": "revenue", "agg": "sum", "filters": [kept]},
     "why": "Same revenue view as before, broken out by category, on orders that were not returned."},
    {"tool": "group_aggregate", "args": {"by": "category", "metric": "revenue", "agg": "sum",
                                         "filters": [kept, {"column": "region", "op": "=", "value": top["top_group"]}]},
     "why": f"The same breakdown inside {top['top_group']} only."},
]
r = run(plan2)
a, b = r[0]["result"]["summary"], r[1]["result"]["summary"]
b2 = r[1]["result"]["data"][1]
turns.append(finish({
    "id": "rec2", "question": q2, "plan": plan2, "results": r,
    "answer_md": (
        f"With returned orders left out, **{a['top_group']}** is the largest category at **${fmt(a['top_value'])}**, "
        f"{a['top_share_pct']:.1f}% of kept revenue [1].\n\n"
        f"Inside {top['top_group']} the order is the same: {b['top_group']} leads with ${fmt(b['top_value'])} ({b['top_share_pct']:.1f}%), "
        f"then {b2['category']} at ${fmt(b2['sum_revenue'])} [2]. "
        f"That is roughly 12% more concentrated than the company-wide mix."
    ),
    "key_numbers": [
        {"label": f"{a['top_group']}, all regions", "value": f"${fmt(a['top_value'])}", "step": 1},
        {"label": f"{b['top_group']} share in {top['top_group']}", "value": f"{b['top_share_pct']:.1f}%", "step": 2},
        {"label": f"Kept revenue, {top['top_group']}", "value": f"${fmt(b['total'])}", "step": 2},
    ],
    "follow_ups": ["Do bigger discounts lead to more returns?",
                   f"Show {b['top_group']} revenue per month",
                   "Which category has the highest return rate?"],
}, start + timedelta(seconds=95)))

# ---- 3 -------------------------------------------------------------------------------------
q3 = "Do bigger discounts lead to more returns?"
plan3 = [
    {"tool": "compare_groups", "args": {"by": "returned", "metric": "discount"},
     "why": "Average discount on returned orders against kept ones."},
    {"tool": "compare_groups", "args": {"by": "region", "metric": "discount"},
     "why": "Where discounts are deepest, to see what else differs."},
    {"tool": "crosstab", "args": {"row": "region", "col": "category", "metric": "discount", "agg": "mean"},
     "why": "Mean discount for every region and category pair."},
]
r = run(plan3)
c, d, x = r[0]["result"]["summary"], r[1]["result"]["summary"], r[2]["result"]["summary"]
rows = {str(row["returned"]).lower(): row for row in r[0]["result"]["data"]}
turns.append(finish({
    "id": "rec3", "question": q3, "plan": plan3, "results": r,
    "answer_md": (
        f"No, not in this data. Returned orders carried an average discount of **{rows['true']['mean']}**, "
        f"slightly *lower* than the **{rows['false']['mean']:.3f}** on orders that were kept [1].\n\n"
        f"What does stand out is where discounts are given. {d['highest_group']} averages {d['highest_mean']}, "
        f"{d['ratio_highest_to_lowest']:.1f} times {d['lowest_group']}'s {d['lowest_mean']} [2], and the deepest cell is "
        f"{x['max_cell']} at {x['max_value']} [3]. With only {rows['true']['count']} returned orders, "
        f"a small effect could still be hidden."
    ),
    "key_numbers": [
        {"label": "Mean discount, returned", "value": rows["true"]["mean"], "step": 1},
        {"label": "Mean discount, kept", "value": rows["false"]["mean"], "step": 1},
        {"label": f"{d['highest_group']} vs {d['lowest_group']}", "value": f"{d['ratio_highest_to_lowest']:.1f}×", "step": 2},
    ],
    "follow_ups": [f"Why are discounts higher in {d['highest_group']}?", "Which category has the highest return rate?"],
}, start + timedelta(seconds=190)))

regions = [t["value"] for t in next(c for c in profile["columns"] if c["name"] == "region")["top_values"]]
cats = next(c for c in profile["columns"] if c["name"] == "category")
dates = next(c for c in profile["columns"] if c["name"] == "order_date")
understanding = {
    "title": "Retail orders, 2025 to mid-2026",
    "domain": "Retail sales",
    "summary": (f"One row per order: {fmt(profile['row_count'])} orders from {str(dates['min'])[:10]} to {str(dates['max'])[:10]} "
                f"across {len(regions)} regions and {cats['distinct_count']} product categories. Each order records units, "
                "unit price, the discount given, the resulting revenue and whether it was returned."),
    "column_notes": {
        "order_id": "Order number. Unique per row; an identifier, not a quantity.",
        "order_date": "Day the order was placed. Use month or quarter for trends.",
        "region": f"Sales region, {len(regions)} values of similar size.",
        "category": f"Product category, {cats['distinct_count']} values. Electronics and Furniture carry the high prices.",
        "units": "Units on the order. Whole numbers, most orders are small.",
        "unit_price": "List price per unit before discount. Wide range across categories.",
        "discount": "Fraction off list price (0.15 = 15%).",
        "customer_id": "Customer code. Repeats across orders.",
        "returned": "True when the order came back.",
        "revenue": "units × unit_price × (1 − discount). Net of discount, not of returns.",
    },
    "quality_notes": [
        "No empty values and no duplicate rows were found.",
        "order_id is numeric but is an identifier; sums or averages of it mean nothing.",
        "revenue does not subtract returns; filter on returned = false for kept revenue.",
    ],
    "suggested_questions": [q1, q3, "What does a typical order look like in each category?",
                            "Which months had unusually high or low revenue?", "Are there outlier orders by revenue?"],
}

demo = {
    "recorded": True,
    "recorded_note": ("Every tool call and number was produced by the real analysis tools on samples/retail_orders.csv. "
                      "The dataset description and the written answers were authored for this example, and one answer "
                      "contains a deliberately unsupported figure so you can see the check flag it. Nothing here is live."),
    "session_id": "recorded-retail",
    "dataset": {"name": "retail_orders.csv", "rows": profile["row_count"], "columns": profile["column_count"]},
    "profile": profile,
    "understanding": understanding,
    "turns": turns,
}
out = ROOT / "web" / "src" / "demo" / "retail_demo.json"
out.write_text(json.dumps(demo, indent=1, default=str))
for t in turns:
    print(t["id"], t["grounded_count"], "/", t["total_numbers"], "ungrounded", t["ungrounded"], [s["ms"] for s in t["results"]])
