"""The three LLM roles (understand, plan, answer), each with a deterministic offline fallback."""

from __future__ import annotations

import difflib
import json
import re
from typing import Any

from .llm import LLM, LLMBadJSON, LLMUnavailable
from .tools import TOOL_SPECS, TOOLS, ToolError, validate_args

MAX_STEPS = 5
ANSWER_ROWS = 40
HISTORY_TURNS = 4
OFFLINE_NOTE = "LLM not configured"

_LLM_ERRORS = (LLMUnavailable, LLMBadJSON)


def _usable(llm: LLM | None) -> bool:
    return llm is not None and llm.available


def _dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=str)


# =============================================================================================
# compact views of the profile and history (what the models see)
# =============================================================================================
def _fmt(v: Any) -> str:
    if isinstance(v, float):
        if abs(v) >= 1000:
            return f"{v:,.0f}"
        return f"{v:.4g}"
    if isinstance(v, int) and not isinstance(v, bool) and abs(v) >= 10000:
        return f"{v:,}"
    return str(v)


def compact_profile(profile: dict, top_n: int = 4) -> str:
    lines = [f"Table `data`: {profile.get('row_count')} rows, {profile.get('column_count')} columns, "
             f"{profile.get('duplicate_rows', 0)} duplicate rows."]
    for c in profile.get("columns", []):
        k = c["kind"]
        bits = [k, f"{c.get('distinct_count')} distinct"]
        if c.get("null_count"):
            bits.append(f"{c['null_pct']}% null")
        if k == "numeric":
            bits.append(f"min {_fmt(c.get('min'))}, median {_fmt(c.get('median'))}, mean {_fmt(c.get('mean'))}, "
                        f"max {_fmt(c.get('max'))}")
        elif k == "datetime":
            bits.append(f"{c.get('min')} to {c.get('max')}")
        if c.get("top_values"):
            tops = ", ".join(f"{t['value']} ({t['count']})" for t in c["top_values"][:top_n])
            bits.append(f"top: {tops}")
        lines.append(f"- {c['name']}: " + "; ".join(bits))
    return "\n".join(lines)


def _short_summary(summary: dict, limit: int = 8) -> dict:
    return dict(list((summary or {}).items())[:limit])


def compact_history(history: list[dict] | None, turns: int = HISTORY_TURNS) -> str:
    if not history:
        return "(no previous turns)"
    out = []
    recent = history[-turns:]
    offset = len(history) - len(recent)
    for i, t in enumerate(recent, start=offset + 1):
        out.append(f"Turn {i} question: {t.get('question')}")
        steps = [{"tool": s.get("tool"), "args": s.get("args")} for s in (t.get("plan") or [])]
        out.append(f"Turn {i} plan: {_dumps(steps)}")
        res = []
        for j, r in enumerate(t.get("results") or [], start=1):
            if r.get("ok", True) and "result" in r:
                res.append({"step": j, "title": r["result"].get("title"), "summary": _short_summary(r["result"].get("summary"))})
            elif r.get("error"):
                res.append({"step": j, "error": r["error"][:160]})
        if res:
            out.append(f"Turn {i} results: {_dumps(res)}")
        if t.get("answer_md"):
            ans = re.sub(r"\s+", " ", t["answer_md"])[:300]
            out.append(f"Turn {i} answer (excerpt): {ans}")
    return "\n".join(out)


def _tool_specs_text() -> str:
    return _dumps(TOOL_SPECS)


# =============================================================================================
# understand
# =============================================================================================
UNDERSTAND_SYSTEM = """You write the first brief an analyst reads after opening an unfamiliar dataset.
You are given a statistical profile of the table: real measurements (row count, nulls, distinct counts, ranges, top values, sample rows). You have no documentation, so meaning comes from column names, values and stats - when you infer meaning, say "likely" or "appears to".

Style: plain, specific, calm. No hype or marketing words ("powerful", "rich", "valuable insights", "unlock", "comprehensive"). No filler. Use numbers from the profile when they matter; do not invent numbers, units or business context that the profile does not support.

Return only a JSON object with exactly these keys:
{
  "title": "3-6 word descriptive name, e.g. 'Retail orders, Jan 2025 - Jun 2026'",
  "domain": "2-4 words, e.g. 'retail sales' or 'clinical measurements'",
  "summary": "2-3 sentences: what one row appears to represent, how many rows, the time span if there is a date column, and the main measures and dimensions.",
  "column_notes": {"<every column name>": "one short sentence: what it likely means plus anything notable in its stats (range, units if obvious, skew, nulls, id-like)."},
  "quality_notes": ["0-5 concrete issues with the number that shows them: nulls, duplicate rows, constant columns, id columns, impossible or suspicious ranges, codes stored as numbers. Empty list if nothing stands out."],
  "suggested_questions": ["4-6 questions specific to these columns that the tools can answer: group comparisons, trends over time, distributions, correlations, outliers. Mix two easy ones with two or three that probe a likely business or scientific issue. Phrase them as the user would type them, using the column meanings, not raw SQL."]
}"""


def offline_understanding(profile: dict) -> dict:
    cols = profile.get("columns", [])
    by_kind: dict[str, list[str]] = {}
    for c in cols:
        by_kind.setdefault(c["kind"], []).append(c["name"])
    kinds_txt = "; ".join(f"{len(v)} {k} ({', '.join(v[:6])}{', ...' if len(v) > 6 else ''})" for k, v in by_kind.items())
    summary = f"{profile.get('row_count')} rows x {profile.get('column_count')} columns: {kinds_txt}."
    for c in cols:
        if c["kind"] == "datetime" and c.get("min"):
            summary += f" {c['name']} spans {c['min']} to {c['max']}."
            break
    summary += f" {OFFLINE_NOTE}, so this brief only reports what was measured."

    notes: dict[str, str] = {}
    for c in cols:
        k = c["kind"]
        if k == "numeric":
            txt = f"numeric; range {_fmt(c.get('min'))} to {_fmt(c.get('max'))}, mean {_fmt(c.get('mean'))}, median {_fmt(c.get('median'))}"
        elif k == "datetime":
            txt = f"date/time; {c.get('min')} to {c.get('max')}"
        elif c.get("top_values"):
            tops = ", ".join(f"{t['value']} ({t['count']})" for t in c["top_values"][:3])
            txt = f"{k}; {c.get('distinct_count')} distinct values; most common: {tops}"
        else:
            txt = f"{k}; {c.get('distinct_count')} distinct values"
        if c.get("null_count"):
            txt += f"; {c['null_count']} nulls ({c['null_pct']}%)"
        notes[c["name"]] = txt + "."

    quality = []
    n = profile.get("row_count") or 0
    if profile.get("duplicate_rows"):
        quality.append(f"{profile['duplicate_rows']} fully duplicated rows.")
    for c in cols:
        if c.get("null_count"):
            quality.append(f"{c['name']}: {c['null_count']} missing values ({c['null_pct']}%).")
        if n > 1 and c.get("distinct_count") == 1:
            quality.append(f"{c['name']}: a single constant value.")
    for c in cols:
        if n > 20 and c.get("distinct_count") == n and c["kind"] in ("numeric", "categorical"):
            quality.append(f"{c['name']}: unique for every row (likely an identifier).")
    return {
        "title": str(profile.get("name") or "Dataset"),
        "domain": "unknown",
        "summary": summary,
        "column_notes": notes,
        "quality_notes": quality[:8],
        "suggested_questions": _template_questions(profile),
        "mode": "offline",
    }


def understand(profile: dict, llm: LLM | None = None) -> dict:
    if not _usable(llm):
        return offline_understanding(profile)
    user = ("Dataset profile:\n" + compact_profile(profile, top_n=5)
            + "\n\nSample rows:\n" + _dumps(profile.get("sample_rows", [])[:5]))
    try:
        out = llm.ask_json(UNDERSTAND_SYSTEM, user)
    except _LLM_ERRORS as exc:
        res = offline_understanding(profile)
        res["note"] = f"LLM call failed ({exc.__class__.__name__}); showing measured facts only."
        return res
    base = offline_understanding(profile)
    names = [c["name"] for c in profile.get("columns", [])]
    col_notes = out.get("column_notes") if isinstance(out.get("column_notes"), dict) else {}
    col_notes = {c: str(col_notes.get(c) or base["column_notes"][c]) for c in names}
    sq = [str(q) for q in (out.get("suggested_questions") or []) if isinstance(q, (str, int, float))][:6]
    qn = [str(q) for q in (out.get("quality_notes") or []) if isinstance(q, (str, int, float))][:6]
    return {
        "title": str(out.get("title") or base["title"])[:80],
        "domain": str(out.get("domain") or "")[:60],
        "summary": str(out.get("summary") or base["summary"]),
        "column_notes": col_notes,
        "quality_notes": qn,
        "suggested_questions": sq or base["suggested_questions"],
        "mode": "llm",
    }


# =============================================================================================
# plan
# =============================================================================================
PLAN_SYSTEM = """You are the planner of a data-analysis assistant. You never compute anything and never write SQL or code. You choose calls to a fixed registry of analysis tools that run on one table named `data`; their outputs are the only facts the final answer may use.

TOOLS (name, description, args; "column" means an exact column name from the profile, "kind" is the column kind it must have):
{tool_specs}

How to plan:
1. Use 1-5 steps; usually 2-3. Step 1 must answer the question as directly as possible. Later steps add the context that would change or explain the conclusion (a breakdown by a relevant category, a trend over time, a distribution, a relationship).
2. Use only the tools above and only column names that appear in the profile, spelled exactly. Respect kinds: metric for sum/mean/median must be numeric; date_col must be datetime.
3. Choose aggregations deliberately: sum for totals (revenue, units), mean for rates/typical values (price, discount, age, a 0/1 flag gives a rate), count for "how many". A boolean or 0/1 column averaged gives a rate.
4. Filters narrow the rows: {{"column": ..., "op": ..., "value": ...}}. Categorical values must match the profile's values exactly (case included); dates as "YYYY-MM-DD"; "between" takes [low, high].
5. Follow-ups. Read the conversation. If the new question refers to earlier work ("same but by month", "now split that by category", "exclude West", "only 2025", "what about units instead"), start from the previous turn's steps and change only what was asked: swap the grain, add or change `by`, add a filter to every step it applies to, swap the metric. Keep filters the user set earlier unless they ask to drop them. If the question is new, plan from scratch.
6. If no column can answer the question, still return the closest useful steps (e.g. describe_column on the nearest column) and say in "why" what is missing. Never invent a column.
7. "why" is one short sentence in plain English saying what this step shows.

Return only JSON: {{"steps": [{{"tool": "<name>", "args": {{...}}, "why": "..."}}]}}"""


def _column_kinds(profile: dict) -> dict[str, str]:
    return {c["name"]: c["kind"] for c in profile.get("columns", [])}


def validate_steps(profile: dict, steps: Any) -> tuple[list[dict], list[dict]]:
    """Return (valid steps with repaired args, dropped [{step, error}])."""
    kinds = _column_kinds(profile)
    valid, dropped = [], []
    if isinstance(steps, dict):
        steps = steps.get("steps", [])
    if not isinstance(steps, list):
        return [], [{"step": steps, "error": "plan was not a list of steps"}]
    seen = set()
    for s in steps:
        if not isinstance(s, dict):
            dropped.append({"step": s, "error": "step is not an object"})
            continue
        tool = str(s.get("tool") or s.get("name") or "").strip()
        try:
            if tool not in TOOLS:
                raise ToolError(f"Unknown tool '{tool}'")
            args = validate_args(kinds, tool, s.get("args") or s.get("arguments") or {})
        except ToolError as exc:
            dropped.append({"step": s, "error": str(exc)})
            continue
        key = _dumps([tool, args])
        if key in seen:
            continue
        seen.add(key)
        valid.append({"tool": tool, "args": args, "why": str(s.get("why") or "").strip()[:240]})
        if len(valid) >= MAX_STEPS:
            break
    return valid, dropped


def plan_detailed(profile: dict, understanding: dict | None, question: str, history: list[dict] | None,
                  llm: LLM | None = None) -> dict:
    """{"steps", "mode": "llm"|"offline", "dropped": [...], "note"?}"""
    if _usable(llm):
        system = PLAN_SYSTEM.format(tool_specs=_tool_specs_text())
        brief = understanding or {}
        user = "\n\n".join([
            "DATASET PROFILE:\n" + compact_profile(profile),
            "DATASET BRIEF: " + str(brief.get("summary") or "(none)"),
            "CONVERSATION SO FAR:\n" + compact_history(history),
            "NEW QUESTION: " + question,
        ])
        try:
            raw = llm.ask_json(system, user)
            steps, dropped = validate_steps(profile, raw.get("steps", raw))
            if steps:
                return {"steps": steps, "mode": "llm", "dropped": dropped}
            heur = heuristic_plan(profile, question, history)
            return {"steps": heur, "mode": "heuristic", "dropped": dropped,
                    "note": "The planner returned no valid steps; used the keyword planner instead."}
        except _LLM_ERRORS as exc:
            return {"steps": heuristic_plan(profile, question, history), "mode": "offline", "dropped": [],
                    "note": f"LLM call failed ({exc.__class__.__name__}); used the keyword planner."}
    return {"steps": heuristic_plan(profile, question, history), "mode": "offline", "dropped": []}


def plan(profile: dict, understanding: dict | None, question: str, history: list[dict] | None,
         llm: LLM | None = None) -> list[dict]:
    return plan_detailed(profile, understanding, question, history, llm)["steps"]


# ---------------------------------------------------------------------------------------------
# heuristic (offline) planner
# ---------------------------------------------------------------------------------------------
_PREFERRED_METRIC = ["revenue", "sales", "amount", "profit", "income", "spend", "total", "value", "cost", "price",
                     "units", "qty", "quantity", "score", "mass", "weight", "length"]
_ID_LIKE = re.compile(r"(^id$|_id$|^id_|uuid|^index$|^row)", re.I)
_GRAIN_WORDS = [("day", r"\b(daily|per day|by day|each day)\b"), ("week", r"\b(weekly|per week|by week|each week)\b"),
                ("month", r"\b(monthly|per month|by month|each month|months?)\b"),
                ("quarter", r"\b(quarterly|per quarter|by quarter|quarters?)\b"),
                ("year", r"\b(yearly|annual(ly)?|per year|by year|each year|years?)\b")]
_SYNONYMS = {
    "margin": ["discount", "cost", "profit", "margin", "price", "return"],
    "profit": ["profit", "margin", "cost", "discount", "revenue"],
    "losing": ["discount", "return", "refund", "cost"],
    "loss": ["discount", "return", "refund", "cost"],
    "sales": ["revenue", "sales", "amount", "units"],
    "money": ["revenue", "amount", "price", "sales"],
    "weight": ["mass", "weight"],
    "size": ["mass", "length", "size"],
}


def _tokens(text: str) -> list[str]:
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t]


def _is_id(c: dict, n: int) -> bool:
    return bool(_ID_LIKE.search(c["name"])) or (n > 20 and c.get("distinct_count") == n and c["kind"] != "datetime")


def _mentions(profile: dict, question: str, synonyms: bool = True) -> list[str]:
    """Columns mentioned in the question, in order of first mention (fuzzy token match + synonyms)."""
    q_tokens = _tokens(question)
    q_text = " " + " ".join(q_tokens) + " "
    scored: list[tuple[int, int, str]] = []
    exact_tokens: set[int] = set()
    for c in profile.get("columns", []):
        ctoks = _tokens(c["name"])
        joined = " " + " ".join(ctoks) + " "
        idx = q_text.find(joined) if ctoks else -1
        if idx >= 0:
            pos = len(q_text[:idx].split())
            exact_tokens.update(range(pos, pos + len(ctoks)))
            scored.append((pos, 0, c["name"]))
    exact_names = {n for _, _, n in scored}
    for c in profile.get("columns", []):
        name = c["name"]
        if name in exact_names:
            continue
        ctoks = _tokens(name)
        pos = None
        for i, qt in enumerate(q_tokens):
            if i in exact_tokens:
                continue
            for ct in ctoks:
                if len(ct) < 3 or len(qt) < 3:
                    continue
                if (qt == ct or qt.rstrip("s") == ct.rstrip("s")
                        or (len(ct) >= 4 and qt.startswith(ct)) or (len(qt) >= 4 and ct.startswith(qt))
                        or difflib.SequenceMatcher(None, qt, ct).ratio() >= 0.85):
                    pos = i
                    break
            if pos is not None:
                break
        if pos is None and synonyms:
            for i, qt in enumerate(q_tokens):
                if any(syn in name.lower() for syn in _SYNONYMS.get(qt, [])):
                    pos = 1000 + i  # weaker than a direct mention
                    break
        if pos is not None:
            scored.append((pos, 1, name))
    return [n for _, _, n in sorted(scored)]


_ADDITIVE = re.compile(r"revenue|sales|amount|units|qty|quantity|spend|income|profit|cost|count|total|volume|"
                       r"orders|visits|clicks|sessions|sold|gross|net|budget|paid|fee")


def _agg_for(profile: dict, metric: str | None, agg: str) -> str:
    """Totals only make sense for additive measures (revenue, units...); average the rest (price, rate, age...)."""
    if agg != "sum" or not metric:
        return agg
    col = next((c for c in profile.get("columns", []) if c["name"] == metric), None)
    if col is None:
        return agg
    lo, hi = col.get("min"), col.get("max")
    if lo is not None and hi is not None and 0 <= lo and hi <= 1:
        return "mean"
    if re.search(r"price|rate|pct|percent|ratio|discount|share|avg|mean", metric.lower()):
        return "mean"
    return "sum" if _ADDITIVE.search(metric.lower()) else "mean"


def _default_metric(profile: dict, exclude: set[str] | None = None) -> str | None:
    n = profile.get("row_count") or 0
    nums = [c for c in profile.get("columns", []) if c["kind"] == "numeric" and not _is_id(c, n)
            and c["name"] not in (exclude or set())]
    for word in _PREFERRED_METRIC:
        for c in nums:
            if word in c["name"].lower():
                return c["name"]
    nums.sort(key=lambda c: -(c.get("distinct_count") or 0))
    return nums[0]["name"] if nums else None


def _default_category(profile: dict, exclude: set[str] | None = None) -> str | None:
    n = profile.get("row_count") or 0
    pool = [c for c in profile.get("columns", []) if 2 <= (c.get("distinct_count") or 0) <= 30
            and not _is_id(c, n) and c["name"] not in (exclude or set())]
    cats = [c for c in pool if c["kind"] == "categorical"] or [c for c in pool if c["kind"] == "boolean"]
    if not cats:  # low-cardinality numeric codes (e.g. 0/1 flags) can still be groups
        cats = [c for c in profile.get("columns", []) if c["kind"] == "numeric"
                and 2 <= (c.get("distinct_count") or 0) <= 8 and c["name"] not in (exclude or set())]
    return cats[0]["name"] if cats else None


def _default_date(profile: dict) -> str | None:
    for c in profile.get("columns", []):
        if c["kind"] == "datetime":
            return c["name"]
    return None


def _value_filters(profile: dict, question: str) -> list[dict]:
    """'exclude West' -> region != West; 'only North' / 'in North' -> region = North."""
    out = []
    ql = question.lower()
    for c in profile.get("columns", []):
        if c["kind"] not in ("categorical", "boolean"):
            continue
        for t in c.get("top_values", []):
            v = str(t["value"])
            if not v.strip():
                continue
            if len(v) < 2:  # single letters only count when written exactly ("exclude N")
                m = re.search(r"(?<![A-Za-z0-9])" + re.escape(v) + r"(?![A-Za-z0-9])", question)
            else:
                m = re.search(r"(?<![a-z0-9])" + re.escape(v.lower()) + r"(?![a-z0-9])", ql)
            if not m:
                continue
            before = ql[max(0, m.start() - 25):m.start()]
            if re.search(r"\b(exclud\w*|without|except|not|drop|remove|ignore|other than|minus)\b", before):
                out.append({"column": c["name"], "op": "!=", "value": v})
            elif re.search(r"\b(only|just|in|for|within|where|from)\b", before):
                out.append({"column": c["name"], "op": "=", "value": v})
    years = re.findall(r"\b(19\d{2}|20\d{2})\b", ql)
    date = _default_date(profile)
    if date and years:
        y = years[0]
        before = ql[max(0, ql.find(y) - 25):ql.find(y)]
        if re.search(r"\b(exclud\w*|without|except|not|drop|remove|ignore)\b", before):
            out.append({"column": date, "op": ">=", "value": f"{int(y) + 1}-01-01"})
        elif re.search(r"\b(in|only|during|for|of)\b", before):
            out.append({"column": date, "op": "between", "value": [f"{y}-01-01", f"{y}-12-31"]})
    return out


def _grain(question: str) -> str | None:
    ql = question.lower()
    for g, pat in _GRAIN_WORDS:
        if re.search(pat, ql):
            return g
    return None


def _by_column(profile: dict, question: str) -> str | None:
    """Column named right after by/per/across/each/split/break down."""
    kinds = _column_kinds(profile)
    n = profile.get("row_count") or 0
    cols = {c["name"]: c for c in profile.get("columns", [])}
    for m in re.finditer(r"\b(by|per|across|each|split(?: it| that)? by|broken down by|break(?:ing)? down by|for each|between|which)\s+([a-z0-9_ ]{2,40})", question.lower()):
        tail = " ".join(m.group(2).split()[:3])
        for name in _mentions(profile, tail, synonyms=False):
            if kinds[name] != "datetime" and _groupable(cols[name], n):
                return name
    return None


def _groupable(c: dict, n: int) -> bool:
    d = c.get("distinct_count") or 0
    if c["kind"] in ("categorical", "boolean"):
        return 2 <= d <= 60 and not _is_id(c, n)
    return c["kind"] == "numeric" and 2 <= d <= 10


def _apply_filters(steps: list[dict], filters: list[dict]) -> None:
    if not filters:
        return
    for s in steps:
        if s["tool"] in ("group_aggregate", "time_trend", "distribution", "top_categories", "compare_groups", "filter_rows"):
            existing = list(s["args"].get("filters") or [])
            for f in filters:
                existing = [e for e in existing if e["column"] != f["column"] or e["op"] != f["op"]] + [f]
            s["args"]["filters"] = existing


def heuristic_plan(profile: dict, question: str, history: list[dict] | None = None) -> list[dict]:
    q = question.lower()
    kinds = _column_kinds(profile)
    n_rows = profile.get("row_count") or 0
    cols = {c["name"]: c for c in profile.get("columns", [])}
    mentioned = _mentions(profile, question)
    direct = _mentions(profile, question, synonyms=False)
    date = _default_date(profile)
    by = _by_column(profile, question)
    m_grp = [c for c in direct if _groupable(cols[c], n_rows) and kinds[c] != "numeric"]
    cat = by or (m_grp[0] if m_grp else None) or _default_category(profile)
    m_num = [c for c in mentioned if kinds[c] == "numeric" and not _is_id(cols[c], n_rows) and c != cat]
    m_cat = [c for c in direct if kinds[c] in ("categorical", "boolean")]
    grain = _grain(question)
    filters = _value_filters(profile, question)
    agg = "mean" if re.search(r"\b(average|avg|mean|typical|rate)\b", q) else "sum"
    if re.search(r"\b(how many|count|number of)\b", q) and not m_num:
        agg = "count"
    metric = m_num[0] if m_num else _default_metric(profile, exclude={cat} if cat else None)
    if not re.search(r"\b(total|sum)\b", q):
        agg = _agg_for(profile, metric, agg)

    # ---- follow-up: modify the previous plan --------------------------------------------------
    prev = (history or [])[-1]["plan"] if history and history[-1].get("plan") else None
    is_followup = bool(re.search(r"^(and |also |now |then |ok |okay |what about |how about )|\b(same|that|this|those|instead|again|redo|re-do|it)\b", q))
    is_followup = is_followup or (bool(filters) and len(q.split()) <= 6 and not re.search(r"\b(show|list|rows)\b", q))
    if prev and is_followup and not re.search(r"correlat|outlier|distribution|histogram", q):
        steps = [{"tool": s["tool"], "args": json.loads(_dumps(s["args"])), "why": s.get("why", "")} for s in prev]
        changed = False
        if grain:
            has_trend = False
            for s in steps:
                if s["tool"] == "time_trend":
                    s["args"]["grain"] = grain
                    has_trend = changed = True
            if not has_trend and date:
                base = next((s for s in steps if s["tool"] in ("group_aggregate", "compare_groups")), None)
                m = (base or {}).get("args", {}).get("metric") or metric
                a = (base or {}).get("args", {}).get("agg", "mean" if base and base["tool"] == "compare_groups" else agg)
                fl = (base or {}).get("args", {}).get("filters") or []
                steps.insert(0, _step("time_trend", {"date_col": date, "metric": m, "agg": a or "sum", "grain": grain,
                                                     "filters": fl}, f"{m} per {grain}"))
                changed = True
        if by:
            for s in steps:
                if s["tool"] in ("group_aggregate", "compare_groups"):
                    s["args"]["by"] = by
                    changed = True
            if not changed:
                src = next((s for s in steps if s["args"].get("metric")), None)
                m = src["args"]["metric"] if src and not m_num else metric
                a = src["args"].get("agg", "sum") if src and not m_num else agg
                fl = (src or {}).get("args", {}).get("filters") or []
                steps.append(_step("group_aggregate", {"by": by, "metric": m, "agg": a, "filters": fl}, f"{m} by {by}"))
                changed = True
        if m_num and re.search(r"\b(instead|rather|what about|how about)\b", q):
            for s in steps:
                if "metric" in s["args"] and kinds.get(s["args"]["metric"] or "") == "numeric":
                    s["args"]["metric"] = m_num[0]
                    changed = True
        if filters:
            _apply_filters(steps, filters)
            changed = True
        if changed:
            valid, _ = validate_steps(profile, steps)
            if valid:
                return valid

    # ---- fresh plan from keywords -------------------------------------------------------------
    steps: list[dict] = []
    if re.search(r"correlat|relationship|related|associated|linked|drives?|depend", q):
        cols = m_num if len(m_num) >= 2 else None
        steps.append(_step("correlation", {"columns": cols} if cols else {}, "pairwise correlation of numeric columns"))
        if len(m_num) >= 2:
            steps.append(_step("scatter", {"x": m_num[0], "y": m_num[1]}, f"{m_num[1]} against {m_num[0]}"))
    if date and metric and (grain or re.search(r"trend|over time|growth|grow|season|evolv|change[sd]? over|timeline|history", q)):
        steps.append(_step("time_trend", {"date_col": date, "metric": metric, "agg": agg if agg != "count" else "count",
                                          "grain": grain or "month"}, f"{metric} per {grain or 'month'}"))
    if re.search(r"outlier|anomal|unusual|extreme|weird|spike", q) and (m_num or metric):
        steps.append(_step("outliers", {"column": m_num[0] if m_num else metric}, "IQR outlier check"))
    if re.search(r"distribut|spread|histogram|range of|skew", q):
        col = (m_num or mentioned or [metric])[0]
        if col:
            steps.append(_step("distribution", {"column": col}, f"distribution of {col}"))
    if re.search(r"compar|\bvs\.?\b|versus|differ|between", q) and cat and (m_num or metric):
        steps.append(_step("compare_groups", {"by": cat, "metric": m_num[0] if m_num else metric}, f"compare across {cat}"))
    if by and not any(s["tool"] in ("compare_groups",) for s in steps):
        if agg == "count" and not m_num:
            steps.append(_step("group_aggregate", {"by": by, "agg": "count"}, f"rows per {by}"))
        elif metric:
            steps.append(_step("group_aggregate", {"by": by, "metric": metric, "agg": agg}, f"{agg} of {metric} by {by}"))
    if re.search(r"\b(most common|top|frequent|popular)\b", q) and m_cat:
        steps.append(_step("top_categories", {"column": m_cat[0]}, f"most common {m_cat[0]}"))
    if re.search(r"\b(show|list|rows|examples?)\b", q) and filters and not steps:
        steps.append(_step("filter_rows", {"filters": filters}, "matching rows"))

    if not steps:
        steps = _default_steps(profile, mentioned, metric, cat, date, agg)
    _apply_filters(steps, filters)
    valid, _ = validate_steps(profile, steps)
    if not valid:
        valid, _ = validate_steps(profile, _default_steps(profile, [], _default_metric(profile), _default_category(profile), date, "sum"))
    if not valid:
        first = profile.get("columns", [{}])[0].get("name")
        valid = [_step("describe_column", {"column": first}, "overview of the first column")] if first else []
    return valid


def _step(tool: str, args: dict, why: str) -> dict:
    return {"tool": tool, "args": args, "why": why}


def _default_steps(profile: dict, mentioned: list[str], metric: str | None, cat: str | None, date: str | None,
                   agg: str) -> list[dict]:
    kinds = _column_kinds(profile)
    steps = []
    m_num = [c for c in mentioned if kinds[c] == "numeric"]
    m_other = [c for c in mentioned if kinds[c] != "numeric"]
    if cat and metric:
        steps.append(_step("group_aggregate", {"by": cat, "metric": metric, "agg": agg if agg != "count" else "sum"},
                           f"{metric} by {cat}"))
    for extra in m_num[1:3] if m_num and m_num[0] == metric else m_num[:2]:
        if cat and extra != metric:
            steps.append(_step("compare_groups", {"by": cat, "metric": extra}, f"{extra} across {cat}"))
    if date and metric:
        steps.append(_step("time_trend", {"date_col": date, "metric": metric, "agg": agg if agg != "count" else "sum",
                                          "grain": "month"}, f"{metric} per month"))
    for c in m_other[:1]:
        if c != cat and kinds[c] != "datetime":
            steps.append(_step("describe_column", {"column": c}, f"overview of {c}"))
    if not steps and metric:
        steps.append(_step("distribution", {"column": metric}, f"distribution of {metric}"))
    if len([c for c in kinds.values() if c == "numeric"]) >= 2 and len(steps) < 3:
        steps.append(_step("correlation", {}, "how the numeric columns move together"))
    return steps[:MAX_STEPS]


def _template_questions(profile: dict) -> list[str]:
    metric = _default_metric(profile)
    cat = _default_category(profile)
    date = _default_date(profile)
    other = _default_metric(profile, exclude={metric} if metric else None)
    qs = []
    if metric and cat:
        word = "total" if _agg_for(profile, metric, "sum") == "sum" else "average"
        qs.append(f"Which {cat} has the highest {word} {metric}?")
    if metric and date:
        qs.append(f"How does {metric} change over time by month?")
    if other and cat:
        qs.append(f"Compare {other} across {cat}")
    if metric:
        qs.append(f"Are there outliers in {metric}?")
    if len([c for c in profile.get("columns", []) if c["kind"] == "numeric"]) >= 2:
        qs.append("Which numeric columns are correlated?")
    if metric:
        qs.append(f"What is the distribution of {metric}?")
    return qs[:6]


# =============================================================================================
# answer
# =============================================================================================
ANSWER_SYSTEM = """You write the reply of a data-analysis assistant. You are given the user's question and the results of analysis steps that were actually computed on their data (each with a step number, title, summary of headline numbers, and data rows). Those results are the only facts you have.

Rules:
- Lead with the direct answer in the first sentence. No preamble, no restating the question, no "Based on the analysis".
- Every number you write must appear in the results. You may round (e.g. 12873.46 -> 12,873 or 12.9k) and may write a fraction as a percent (0.137 -> 13.7%). Do not compute new numbers yourself (no differences, ratios or totals that are not in the results); if a comparison matters, quote both numbers.
- Cite the step each claim comes from with its number in square brackets, e.g. "West has the highest mean discount (0.19) [2]".
- If the results cannot answer the question (missing column, failed step, too few rows), say so plainly in one sentence and say what would be needed. Do not guess or fill gaps with general knowledge. Correlation does not show cause; only say this if you discuss a relationship.
- Be brief: 2-5 sentences, or a short bullet list when listing several groups. Markdown is fine; no headings, no tables unless comparing 4+ items on 2+ measures.
- key_numbers: the 2-5 numbers that matter most, each {"label": short label, "value": the number or short string exactly as in the results, "step": step number}.
- follow_ups: 2-3 next questions the user could ask that these tools and columns can answer, phrased as the user would type them (e.g. "Same but by month", "Exclude West and compare again"), building on this answer.

Return only JSON: {"answer_md": "...", "key_numbers": [...], "follow_ups": ["...", "..."]}"""


def results_for_prompt(results: list[dict], max_rows: int = ANSWER_ROWS) -> list[dict]:
    out = []
    for i, r in enumerate(results, start=1):
        if r.get("ok") and r.get("result"):
            res = r["result"]
            data = res.get("data") or []
            item = {"step": i, "tool": res.get("tool"), "args": res.get("args"), "title": res.get("title"),
                    "summary": res.get("summary"), "data": data[:max_rows]}
            if len(data) > max_rows:
                item["data_note"] = f"first {max_rows} of {len(data)} rows shown"
            out.append(item)
        else:
            out.append({"step": i, "tool": r.get("tool"), "args": r.get("args"), "error": r.get("error")})
    return out


def _md_cell(v: Any) -> str:
    if isinstance(v, float):
        v = f"{v:,.2f}" if abs(v) >= 100 else f"{v:.4g}"
    elif isinstance(v, int) and not isinstance(v, bool):
        v = f"{v:,}" if abs(v) >= 10000 else str(v)
    return str(v).replace("|", "\\|").replace("\n", " ")


def offline_answer(question: str, results: list[dict], understanding: dict | None = None,
                   history: list[dict] | None = None, note: str | None = None) -> dict:
    lines = [f"_{note or OFFLINE_NOTE}: showing the computed results without commentary._", ""]
    lines += ["| Step | Result | Measure | Value |", "|---|---|---|---|"]
    key_numbers = []
    for i, r in enumerate(results, start=1):
        if r.get("ok") and r.get("result"):
            res = r["result"]
            for k, v in (res.get("summary") or {}).items():
                if v is None or isinstance(v, (list, dict)):
                    continue
                lines.append(f"| [{i}] | {_md_cell(res.get('title'))} | {_md_cell(k)} | {_md_cell(v)} |")
                if len(key_numbers) < 4 and isinstance(v, (int, float)) and not isinstance(v, bool):
                    key_numbers.append({"label": f"{res.get('title')}: {k}", "value": v, "step": i})
        else:
            lines.append(f"| [{i}] | {_md_cell(r.get('tool'))} | error | {_md_cell(r.get('error'))} |")
    asked = {t.get("question") for t in (history or [])} | {question}
    follow = [q for q in (understanding or {}).get("suggested_questions", []) if q not in asked][:3]
    return {"answer_md": "\n".join(lines), "key_numbers": key_numbers, "follow_ups": follow, "mode": "offline"}


def answer(question: str, understanding: dict | None, results: list[dict], history: list[dict] | None,
           llm: LLM | None = None) -> dict:
    if not _usable(llm):
        return offline_answer(question, results, understanding, history)
    payload = results_for_prompt(results)
    brief = (understanding or {}).get("summary") or ""
    prev = compact_history(history, turns=2) if history else "(none)"
    user = "\n\n".join([
        f"QUESTION: {question}",
        f"DATASET: {brief}",
        f"EARLIER IN THE CONVERSATION:\n{prev}",
        "RESULTS (JSON):\n" + _dumps(payload),
    ])
    try:
        out = llm.ask_json(ANSWER_SYSTEM, user)
    except _LLM_ERRORS as exc:
        return offline_answer(question, results, understanding, history,
                              note=f"LLM call failed ({exc.__class__.__name__})")
    answer_md = out.get("answer_md") or out.get("answer") or ""
    if not isinstance(answer_md, str) or not answer_md.strip():
        return offline_answer(question, results, understanding, history, note="LLM returned an empty answer")
    kn = []
    for k in out.get("key_numbers") or []:
        if isinstance(k, dict) and "value" in k:
            step = k.get("step")
            try:
                step = int(step) if step is not None else None
            except (TypeError, ValueError):
                step = None
            kn.append({"label": str(k.get("label") or ""), "value": k["value"], "step": step})
    fu = [str(f) for f in (out.get("follow_ups") or []) if isinstance(f, (str, int, float)) and str(f).strip()][:3]
    return {"answer_md": answer_md.strip(), "key_numbers": kn[:6], "follow_ups": fu, "mode": "llm"}
