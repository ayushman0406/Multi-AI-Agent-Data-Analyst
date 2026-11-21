"""The fixed registry of safe analysis tools. Every query is built from validated identifiers and
parameterised values; no user- or model-supplied SQL or code is ever executed."""

from __future__ import annotations

import difflib
import math
from typing import Any, Callable

from .data import Dataset, jsonable, quote_ident

AGGS = {"sum": "SUM", "mean": "AVG", "count": "COUNT", "min": "MIN", "max": "MAX", "median": "MEDIAN"}
GRAINS = ("day", "week", "month", "quarter", "year")
OPS = ("=", "!=", ">", ">=", "<", "<=", "in", "between", "contains")
_OP_ALIASES = {"==": "=", "eq": "=", "<>": "!=", "ne": "!=", "neq": "!=", "gt": ">", "gte": ">=", "ge": ">=",
               "lt": "<", "lte": "<=", "le": "<=", "not in": "not_in", "like": "contains", "ilike": "contains"}


class ToolError(Exception):
    """Bad tool arguments (unknown column, wrong type, bad aggregation...)."""


# ---------------------------------------------------------------------------------------------
# validation helpers
# ---------------------------------------------------------------------------------------------
def _valid_cols_msg(kinds: dict[str, str], want: tuple[str, ...] | None = None) -> str:
    cols = [c for c, k in kinds.items() if not want or k in want]
    return ", ".join(cols) if cols else "(none)"


def resolve_column(kinds: dict[str, str], name: Any, want: tuple[str, ...] | None = None,
                   arg: str = "column", fuzzy: bool = False) -> str:
    """Return the exact schema column for `name` (exact, case-insensitive, or fuzzy if allowed)."""
    if not isinstance(name, str) or not name.strip():
        raise ToolError(f"Argument '{arg}' must be a column name. Valid columns: {_valid_cols_msg(kinds, want)}")
    name = name.strip()
    col = name if name in kinds else None
    if col is None:
        lower = {c.lower(): c for c in kinds}
        col = lower.get(name.lower())
    if col is None and fuzzy:
        norm = {c.lower().replace(" ", "_"): c for c in kinds}
        match = difflib.get_close_matches(name.lower().replace(" ", "_"), list(norm), n=1, cutoff=0.8)
        col = norm[match[0]] if match else None
    if col is None:
        raise ToolError(f"Unknown column '{name}' for '{arg}'. Valid columns: {_valid_cols_msg(kinds)}")
    if want and kinds[col] not in want:
        raise ToolError(
            f"Column '{col}' is {kinds[col]}, but '{arg}' needs a {' or '.join(want)} column. "
            f"Valid columns: {_valid_cols_msg(kinds, want)}"
        )
    return col


def _int_arg(value: Any, arg: str, default: int, lo: int, hi: int) -> int:
    if value is None:
        return default
    try:
        v = int(float(value))
    except (TypeError, ValueError):
        raise ToolError(f"Argument '{arg}' must be an integer, got {value!r}")
    return max(lo, min(hi, v))


def _agg_arg(agg: Any) -> str:
    a = str(agg or "sum").strip().lower()
    a = {"avg": "mean", "average": "mean", "total": "sum", "n": "count"}.get(a, a)
    if a not in AGGS:
        raise ToolError(f"Unknown agg '{agg}'. Valid: {', '.join(AGGS)}")
    return a


def _grain_arg(grain: Any) -> str:
    g = str(grain or "month").strip().lower()
    g = {"daily": "day", "weekly": "week", "monthly": "month", "quarterly": "quarter", "yearly": "year",
         "annual": "year", "annually": "year", "days": "day", "weeks": "week", "months": "month",
         "quarters": "quarter", "years": "year"}.get(g, g)
    if g not in GRAINS:
        raise ToolError(f"Unknown grain '{grain}'. Valid: {', '.join(GRAINS)}")
    return g


def _metric_expr(kinds: dict[str, str], metric: Any, agg: str, fuzzy: bool = False) -> tuple[str | None, str, str]:
    """Return (metric column or None, SQL aggregate expression, output label)."""
    if agg == "count" and (metric in (None, "", "*", "rows", "count")):
        return None, "COUNT(*)", "count"
    want = ("numeric",) if agg in ("sum", "mean", "median") else ("numeric", "datetime", "categorical", "boolean")
    col = resolve_column(kinds, metric, want, "metric", fuzzy)
    q = quote_ident(col)
    if agg == "count":
        return col, f"COUNT({q})", f"count_{col}"
    if kinds[col] == "numeric":
        q = f"CAST({q} AS DOUBLE)"
    return col, f"{AGGS[agg]}({q})", f"{agg}_{col}"


def normalize_filters(kinds: dict[str, str], filters: Any, fuzzy: bool = False) -> list[dict]:
    if filters in (None, "", []):
        return []
    if isinstance(filters, dict):
        filters = [filters]
    if not isinstance(filters, list):
        raise ToolError("'filters' must be a list of {column, op, value} objects")
    out = []
    for f in filters:
        if not isinstance(f, dict):
            raise ToolError("Each filter must be an object {column, op, value}")
        col = resolve_column(kinds, f.get("column"), None, "filters.column", fuzzy)
        op = str(f.get("op", "=")).strip().lower()
        op = _OP_ALIASES.get(op, op)
        if op not in OPS and op != "not_in":
            raise ToolError(f"Unknown filter op '{f.get('op')}'. Valid: {', '.join(OPS)}")
        if "value" not in f:
            raise ToolError(f"Filter on '{col}' is missing 'value'")
        value = f["value"]
        if op in ("in", "not_in"):
            if not isinstance(value, list):
                value = [value]
            if not value or len(value) > 200:
                raise ToolError("'in' filter needs a list of 1-200 values")
        elif op == "between":
            if not isinstance(value, list) or len(value) != 2:
                raise ToolError("'between' filter needs a [low, high] list")
        elif isinstance(value, (list, dict)):
            raise ToolError(f"Filter op '{op}' needs a single value")
        for v in value if isinstance(value, list) else [value]:
            if isinstance(v, (list, dict)):
                raise ToolError("Filter values must be scalars")
        out.append({"column": col, "op": op, "value": value})
    return out


def _cast(kinds: dict[str, str], col: str) -> str:
    k = kinds[col]
    if k == "numeric":
        return "CAST(? AS DOUBLE)"
    if k == "datetime":
        return "CAST(? AS TIMESTAMP)"
    if k == "boolean":
        return "CAST(? AS BOOLEAN)"
    return "CAST(? AS VARCHAR)"


def compile_filters(kinds: dict[str, str], filters: list[dict]) -> tuple[str, list]:
    """Return (' WHERE ...' or '', params). Identifiers come from the schema; values are bound."""
    clauses, params = [], []
    for f in filters:
        col, op, value = f["column"], f["op"], f["value"]
        q = quote_ident(col)
        ph = _cast(kinds, col)
        if kinds[col] == "categorical" or op == "contains":
            q = f"CAST({q} AS VARCHAR)"
        if op == "contains":
            clauses.append(f"{q} ILIKE ?")
            params.append(f"%{value}%")
        elif op in ("in", "not_in"):
            neg = "NOT " if op == "not_in" else ""
            clauses.append(f"{q} {neg}IN ({', '.join([ph] * len(value))})")
            params.extend(str(v) if kinds[col] == "categorical" else v for v in value)
        elif op == "between":
            clauses.append(f"{q} BETWEEN {ph} AND {ph}")
            params.extend(value)
        else:
            clauses.append(f"{q} {op} {ph}")
            params.append(str(value) if kinds[col] == "categorical" else value)
    return (" WHERE " + " AND ".join(clauses), params) if clauses else ("", [])


def _and(where: str, extra: str) -> str:
    return f"{where} AND {extra}" if where else f" WHERE {extra}"


def _result(tool: str, args: dict, title: str, data: list[dict], chart: dict, summary: dict) -> dict:
    return jsonable({"tool": tool, "args": args, "title": title, "data": data, "chart": chart, "summary": summary})


def _q(ds: Dataset, sql: str, params: list | None = None) -> list[dict]:
    try:
        return ds.query(sql, params)
    except ToolError:
        raise
    except Exception as exc:  # conversion errors from bad filter values, etc.
        raise ToolError(f"Query failed: {str(exc).splitlines()[0]}") from exc


def _filters_label(filters: list[dict]) -> str:
    if not filters:
        return ""
    parts = []
    for f in filters:
        v = f["value"]
        v = ", ".join(map(str, v)) if isinstance(v, list) else v
        parts.append(f"{f['column']} {f['op']} {v}")
    return " (where " + "; ".join(parts) + ")"


# ---------------------------------------------------------------------------------------------
# tools
# ---------------------------------------------------------------------------------------------
def group_aggregate(ds: Dataset, by: str, metric: str | None = None, agg: str = "sum", top: int = 10,
                    filters: list | None = None) -> dict:
    k = ds.kinds
    by = resolve_column(k, by, None, "by")
    agg = _agg_arg(agg)
    metric, expr, label = _metric_expr(k, metric, agg)
    top = _int_arg(top, "top", 10, 1, 50)
    flt = normalize_filters(k, filters)
    where, params = compile_filters(k, flt)
    qb = quote_ident(by)
    sql = (f"WITH g AS (SELECT {qb} AS grp, {expr} AS val, COUNT(*) AS n FROM data{where} GROUP BY 1) "
           f"SELECT grp, val, n, (SELECT COUNT(*) FROM g) AS groups, (SELECT SUM(val) FROM g) AS total "
           f"FROM g ORDER BY val DESC NULLS LAST, grp LIMIT {top}")
    rows = _q(ds, sql, params)
    data = [{by: r["grp"], label: r["val"], "rows": r["n"]} for r in rows]
    summary: dict[str, Any] = {"groups": rows[0]["groups"] if rows else 0}
    if rows:
        summary.update({"top_group": rows[0]["grp"], "top_value": rows[0]["val"],
                        "bottom_shown_group": rows[-1]["grp"], "bottom_shown_value": rows[-1]["val"]})
        if agg in ("sum", "count") and rows[0]["total"]:
            summary["total"] = rows[0]["total"]
            summary["top_share_pct"] = round(100.0 * (rows[0]["val"] or 0) / rows[0]["total"], 2)
    args = {"by": by, "metric": metric, "agg": agg, "top": top, "filters": flt}
    title = f"{agg.capitalize()} of {metric or 'rows'} by {by}{_filters_label(flt)}"
    return _result("group_aggregate", args, title, data, {"type": "bar", "x": by, "y": label}, summary)


def time_trend(ds: Dataset, date_col: str, metric: str | None = None, agg: str = "sum", grain: str = "month",
               filters: list | None = None) -> dict:
    k = ds.kinds
    date_col = resolve_column(k, date_col, ("datetime",), "date_col")
    agg = _agg_arg(agg)
    metric, expr, label = _metric_expr(k, metric, agg)
    grain = _grain_arg(grain)
    flt = normalize_filters(k, filters)
    where, params = compile_filters(k, flt)
    qd = quote_ident(date_col)
    where = _and(where, f"{qd} IS NOT NULL")
    sql = (f"SELECT CAST(date_trunc('{grain}', {qd}) AS DATE) AS period, {expr} AS val, COUNT(*) AS n "
           f"FROM data{where} GROUP BY 1 ORDER BY 1 LIMIT 1000")
    rows = _q(ds, sql, params)
    data = [{"period": r["period"], label: r["val"], "rows": r["n"]} for r in rows]
    summary: dict[str, Any] = {"periods": len(rows)}
    vals = [r["val"] for r in rows if r["val"] is not None]
    if rows and vals:
        nonnull = [r for r in rows if r["val"] is not None]
        first, last = nonnull[0], nonnull[-1]
        peak = max(nonnull, key=lambda r: r["val"])
        low = min(nonnull, key=lambda r: r["val"])
        summary.update({"first_period": first["period"], "first_value": first["val"],
                        "last_period": last["period"], "last_value": last["val"],
                        "peak_period": peak["period"], "peak_value": peak["val"],
                        "lowest_period": low["period"], "lowest_value": low["val"],
                        "mean_per_period": sum(vals) / len(vals)})
        if first["val"] not in (None, 0) and last["val"] is not None:
            summary["change_pct_first_to_last"] = round(100.0 * (last["val"] - first["val"]) / abs(first["val"]), 2)
    args = {"date_col": date_col, "metric": metric, "agg": agg, "grain": grain, "filters": flt}
    title = f"{agg.capitalize()} of {metric or 'rows'} per {grain}{_filters_label(flt)}"
    return _result("time_trend", args, title, data, {"type": "line", "x": "period", "y": label}, summary)


def distribution(ds: Dataset, column: str, bins: int = 20, filters: list | None = None) -> dict:
    k = ds.kinds
    column = resolve_column(k, column, None, "column")
    flt = normalize_filters(k, filters)
    if k[column] != "numeric":
        res = top_categories(ds, column, top=20, filters=flt)
        res["tool"] = "distribution"
        res["args"] = {"column": column, "bins": bins, "filters": flt}
        return res
    bins = _int_arg(bins, "bins", 20, 2, 60)
    where, params = compile_filters(k, flt)
    d = f"CAST({quote_ident(column)} AS DOUBLE)"
    where = _and(where, f"{d} IS NOT NULL AND isfinite({d})")
    st = _q(ds, f"SELECT COUNT(*) AS n, MIN({d}) AS mn, MAX({d}) AS mx, AVG({d}) AS mean, MEDIAN({d}) AS median, "
                f"STDDEV_SAMP({d}) AS std, QUANTILE_CONT({d}, 0.25) AS p25, QUANTILE_CONT({d}, 0.75) AS p75, "
                f"SKEWNESS({d}) AS skew FROM data{where}", params)[0]
    data = []
    if st["n"]:
        lo, hi = float(st["mn"]), float(st["mx"])
        nb = bins if hi > lo else 1
        width = (hi - lo) / nb if hi > lo else 1.0
        counts = {r["b"]: r["n"] for r in _q(
            ds, f"SELECT LEAST(CAST(FLOOR(({d} - ?) / ?) AS BIGINT), {nb - 1}) AS b, COUNT(*) AS n "
                f"FROM data{where} GROUP BY 1", [lo, width] + list(params))}
        data = [{"bin_start": lo + i * width, "bin_end": lo + (i + 1) * width, "count": counts.get(i, 0)}
                for i in range(nb)]
    summary = {"count": st["n"], "min": st["mn"], "p25": st["p25"], "median": st["median"], "mean": st["mean"],
               "p75": st["p75"], "max": st["mx"], "std": st["std"], "skewness": st["skew"]}
    args = {"column": column, "bins": bins, "filters": flt}
    return _result("distribution", args, f"Distribution of {column}{_filters_label(flt)}", data,
                   {"type": "hist", "x": "bin_start", "y": "count"}, summary)


def top_categories(ds: Dataset, column: str, top: int = 10, filters: list | None = None) -> dict:
    k = ds.kinds
    column = resolve_column(k, column, None, "column")
    top = _int_arg(top, "top", 10, 1, 50)
    flt = normalize_filters(k, filters)
    where, params = compile_filters(k, flt)
    q = quote_ident(column)
    sql = (f"WITH g AS (SELECT {q} AS v, COUNT(*) AS n FROM data{where} GROUP BY 1) "
           f"SELECT v, n, (SELECT SUM(n) FROM g) AS total, (SELECT COUNT(*) FROM g) AS distinct_values "
           f"FROM g ORDER BY n DESC, v NULLS LAST LIMIT {top}")
    rows = _q(ds, sql, params)
    total = rows[0]["total"] if rows else 0
    data = [{column: r["v"], "count": r["n"], "pct": round(100.0 * r["n"] / total, 2) if total else None}
            for r in rows]
    summary: dict[str, Any] = {"rows": total, "distinct_values": rows[0]["distinct_values"] if rows else 0}
    if rows:
        summary.update({"top_value": rows[0]["v"], "top_count": rows[0]["n"], "top_pct": data[0]["pct"],
                        "shown_pct": round(sum(d["count"] for d in data) * 100.0 / total, 2) if total else None})
    args = {"column": column, "top": top, "filters": flt}
    return _result("top_categories", args, f"Most common {column}{_filters_label(flt)}", data,
                   {"type": "bar", "x": column, "y": "count"}, summary)


def correlation(ds: Dataset, columns: list | None = None) -> dict:
    k = ds.kinds
    if columns:
        if isinstance(columns, str):
            columns = [columns]
        cols = []
        for c in columns:
            col = resolve_column(k, c, ("numeric",), "columns")
            if col not in cols:
                cols.append(col)
    else:
        cols = [c for c, kind in k.items() if kind == "numeric"][:12]
    if len(cols) < 2:
        raise ToolError(f"correlation needs at least 2 numeric columns. Valid columns: {_valid_cols_msg(k, ('numeric',))}")
    cols = cols[:12]
    pairs = [(a, b) for i, a in enumerate(cols) for b in cols[i + 1:]]
    exprs = []
    for i, (a, b) in enumerate(pairs):
        qa, qb = f"CAST({quote_ident(a)} AS DOUBLE)", f"CAST({quote_ident(b)} AS DOUBLE)"
        exprs.append(f"CORR({qa}, {qb}) AS r{i}, COUNT(*) FILTER (WHERE {qa} IS NOT NULL AND {qb} IS NOT NULL) AS n{i}")
    row = _q(ds, f"SELECT {', '.join(exprs)} FROM data")[0]
    data = []
    for i, (a, b) in enumerate(pairs):
        r = row[f"r{i}"]
        if r is not None and isinstance(r, float) and math.isnan(r):
            r = None
        data.append({"x": a, "y": b, "r": r, "n": row[f"n{i}"]})
    ranked = sorted([d for d in data if d["r"] is not None], key=lambda d: -abs(d["r"]))
    summary: dict[str, Any] = {"columns": len(cols), "pairs": len(pairs)}
    if ranked:
        s = ranked[0]
        summary.update({"strongest_pair": f"{s['x']} ~ {s['y']}", "strongest_r": s["r"]})
        if len(ranked) > 1:
            w = ranked[-1]
            summary.update({"weakest_pair": f"{w['x']} ~ {w['y']}", "weakest_r": w["r"]})
    data = ranked + [d for d in data if d["r"] is None]
    return _result("correlation", {"columns": cols}, "Correlation between " + ", ".join(cols), data,
                   {"type": "heatmap", "x": "x", "y": "y", "value": "r"}, summary)


def outliers(ds: Dataset, column: str) -> dict:
    k = ds.kinds
    column = resolve_column(k, column, ("numeric",), "column")
    d = f"CAST({quote_ident(column)} AS DOUBLE)"
    st = _q(ds, f"SELECT COUNT({d}) AS n, QUANTILE_CONT({d}, 0.25) AS q1, QUANTILE_CONT({d}, 0.75) AS q3, "
                f"MEDIAN({d}) AS median FROM data")[0]
    if not st["n"]:
        raise ToolError(f"Column '{column}' has no numeric values")
    q1, q3 = float(st["q1"]), float(st["q3"])
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    cnt = _q(ds, f"SELECT COUNT(*) FILTER (WHERE {d} < ?) AS below, COUNT(*) FILTER (WHERE {d} > ?) AS above "
                 f"FROM data", [lo, hi])[0]
    rows = _q(ds, f"SELECT * FROM data WHERE {d} < ? OR {d} > ? "
                  f"ORDER BY ABS({d} - ?) DESC LIMIT 20", [lo, hi, float(st["median"])])
    n_out = cnt["below"] + cnt["above"]
    summary = {"count": st["n"], "q1": q1, "q3": q3, "iqr": iqr, "lower_fence": lo, "upper_fence": hi,
               "outliers": n_out, "below_lower": cnt["below"], "above_upper": cnt["above"],
               "outlier_pct": round(100.0 * n_out / st["n"], 2)}
    return _result("outliers", {"column": column}, f"Outliers in {column} (1.5 x IQR)", rows,
                   {"type": "table", "x": column, "y": None}, summary)


def compare_groups(ds: Dataset, by: str, metric: str, filters: list | None = None) -> dict:
    k = ds.kinds
    by = resolve_column(k, by, None, "by")
    metric = resolve_column(k, metric, ("numeric",), "metric")
    flt = normalize_filters(k, filters)
    where, params = compile_filters(k, flt)
    qb, d = quote_ident(by), f"CAST({quote_ident(metric)} AS DOUBLE)"
    sql = (f"SELECT {qb} AS grp, COUNT(*) AS n, AVG({d}) AS mean, MEDIAN({d}) AS median, STDDEV_SAMP({d}) AS std, "
           f"MIN({d}) AS min, MAX({d}) AS max FROM data{where} GROUP BY 1 ORDER BY mean DESC NULLS LAST, grp LIMIT 25")
    rows = _q(ds, sql, params)
    overall = _q(ds, f"SELECT AVG({d}) AS mean, COUNT(*) AS n FROM data{where}", params)[0]
    data = [{by: r["grp"], "count": r["n"], "mean": r["mean"], "median": r["median"], "std": r["std"],
             "min": r["min"], "max": r["max"]} for r in rows]
    summary: dict[str, Any] = {"groups": len(rows), "overall_mean": overall["mean"], "rows": overall["n"]}
    valid = [r for r in rows if r["mean"] is not None]
    if valid:
        hi, lo = valid[0], valid[-1]
        summary.update({"highest_group": hi["grp"], "highest_mean": hi["mean"],
                        "lowest_group": lo["grp"], "lowest_mean": lo["mean"],
                        "gap": (hi["mean"] or 0) - (lo["mean"] or 0)})
        if lo["mean"]:
            summary["ratio_highest_to_lowest"] = round(hi["mean"] / lo["mean"], 4)
    args = {"by": by, "metric": metric, "filters": flt}
    return _result("compare_groups", args, f"{metric} compared across {by}{_filters_label(flt)}", data,
                   {"type": "bar", "x": by, "y": "mean"}, summary)


def crosstab(ds: Dataset, row: str, col: str, metric: str | None = None, agg: str | None = None) -> dict:
    k = ds.kinds
    row = resolve_column(k, row, None, "row")
    col = resolve_column(k, col, None, "col")
    if row == col:
        raise ToolError("crosstab needs two different columns")
    agg = _agg_arg(agg or ("sum" if metric else "count"))
    metric, expr, label = _metric_expr(k, metric, agg)
    qr, qc = quote_ident(row), quote_ident(col)
    sql = (f"WITH tr AS (SELECT {qr} AS v FROM data GROUP BY 1 ORDER BY COUNT(*) DESC LIMIT 15), "
           f"tc AS (SELECT {qc} AS v FROM data GROUP BY 1 ORDER BY COUNT(*) DESC LIMIT 10) "
           f"SELECT {qr} AS r, {qc} AS c, {expr} AS val FROM data "
           f"WHERE {qr} IN (SELECT v FROM tr) AND {qc} IN (SELECT v FROM tc) GROUP BY 1, 2 ORDER BY 1, 2")
    rows = _q(ds, sql)
    data = [{row: r["r"], col: r["c"], label: r["val"]} for r in rows]
    summary: dict[str, Any] = {"cells": len(rows), "row_values": len({r["r"] for r in rows}),
                               "col_values": len({r["c"] for r in rows})}
    vals = [r for r in rows if r["val"] is not None]
    if vals:
        mx = max(vals, key=lambda r: r["val"])
        mn = min(vals, key=lambda r: r["val"])
        summary.update({"max_cell": f"{mx['r']} / {mx['c']}", "max_value": mx["val"],
                        "min_cell": f"{mn['r']} / {mn['c']}", "min_value": mn["val"]})
    args = {"row": row, "col": col, "metric": metric, "agg": agg}
    return _result("crosstab", args, f"{agg.capitalize()} of {metric or 'rows'} by {row} x {col}", data,
                   {"type": "heatmap", "x": col, "y": row, "value": label}, summary)


def scatter(ds: Dataset, x: str, y: str, color: str | None = None, limit: int = 500) -> dict:
    k = ds.kinds
    x = resolve_column(k, x, ("numeric", "datetime"), "x")
    y = resolve_column(k, y, ("numeric",), "y")
    color = resolve_column(k, color, None, "color") if color else None
    limit = _int_arg(limit, "limit", 500, 10, 2000)
    qx, qy = quote_ident(x), quote_ident(y)
    sel = f"{qx}, {qy}" + (f", {quote_ident(color)}" if color and color not in (x, y) else "")
    rows = _q(ds, f"SELECT {sel} FROM (SELECT * FROM data WHERE {qx} IS NOT NULL AND {qy} IS NOT NULL) "
                  f"USING SAMPLE reservoir({limit} ROWS) REPEATABLE (7)")
    summary: dict[str, Any] = {"points": len(rows)}
    if k[x] == "numeric":
        st = _q(ds, f"SELECT CORR(CAST({qx} AS DOUBLE), CAST({qy} AS DOUBLE)) AS r, "
                    f"COUNT(*) FILTER (WHERE {qx} IS NOT NULL AND {qy} IS NOT NULL) AS n FROM data")[0]
        summary.update({"r": st["r"], "rows_with_both": st["n"]})
    chart = {"type": "scatter", "x": x, "y": y}
    if color:
        chart["series"] = color
    args = {"x": x, "y": y, "color": color, "limit": limit}
    return _result("scatter", args, f"{y} vs {x}" + (f" by {color}" if color else ""), rows, chart, summary)


def describe_column(ds: Dataset, column: str) -> dict:
    k = ds.kinds
    column = resolve_column(k, column, None, "column")
    q = quote_ident(column)
    kind = k[column]
    base = _q(ds, f"SELECT COUNT(*) AS rows, COUNT({q}) AS non_null, COUNT(DISTINCT {q}) AS distinct_values FROM data")[0]
    summary: dict[str, Any] = {"kind": kind, "rows": base["rows"], "non_null": base["non_null"],
                               "nulls": base["rows"] - base["non_null"],
                               "null_pct": round(100.0 * (base["rows"] - base["non_null"]) / base["rows"], 2)
                               if base["rows"] else 0.0,
                               "distinct_values": base["distinct_values"]}
    if kind == "numeric":
        dist = distribution(ds, column, bins=12)
        summary.update({kk: v for kk, v in dist["summary"].items() if kk != "count"})
        data, chart = dist["data"], dist["chart"]
    elif kind == "datetime":
        st = _q(ds, f"SELECT MIN({q}) AS min, MAX({q}) AS max FROM data")[0]
        summary.update(st)
        tr = time_trend(ds, column, None, "count", "month")
        data, chart = tr["data"], tr["chart"]
    else:
        tc = top_categories(ds, column, top=10)
        summary.update({kk: v for kk, v in tc["summary"].items() if kk not in ("rows", "distinct_values")})
        data, chart = tc["data"], tc["chart"]
    return _result("describe_column", {"column": column}, f"About {column}", data, chart, summary)


def filter_rows(ds: Dataset, filters: list | None = None, columns: list | None = None, limit: int = 50) -> dict:
    k = ds.kinds
    flt = normalize_filters(k, filters)
    if columns:
        if isinstance(columns, str):
            columns = [columns]
        cols = []
        for c in columns:
            cc = resolve_column(k, c, None, "columns")
            if cc not in cols:
                cols.append(cc)
    else:
        cols = list(ds.columns)
    limit = _int_arg(limit, "limit", 50, 1, 200)
    where, params = compile_filters(k, flt)
    sel = ", ".join(quote_ident(c) for c in cols)
    rows = _q(ds, f"SELECT {sel} FROM data{where} LIMIT {limit}", params)
    matched = _q(ds, f"SELECT COUNT(*) AS n FROM data{where}", params)[0]["n"]
    summary = {"matched_rows": matched, "total_rows": ds.row_count, "shown": len(rows),
               "matched_pct": round(100.0 * matched / ds.row_count, 2) if ds.row_count else 0.0}
    args = {"filters": flt, "columns": cols if columns else None, "limit": limit}
    return _result("filter_rows", args, f"Rows{_filters_label(flt) or ' (no filter)'}", rows,
                   {"type": "table", "x": None, "y": None}, summary)


# ---------------------------------------------------------------------------------------------
# registry + specs
# ---------------------------------------------------------------------------------------------
TOOLS: dict[str, Callable[..., dict]] = {
    "group_aggregate": group_aggregate,
    "time_trend": time_trend,
    "distribution": distribution,
    "top_categories": top_categories,
    "correlation": correlation,
    "outliers": outliers,
    "compare_groups": compare_groups,
    "crosstab": crosstab,
    "scatter": scatter,
    "describe_column": describe_column,
    "filter_rows": filter_rows,
}

_FILTERS_SPEC = {
    "type": "array", "required": False,
    "description": 'Optional row filters, ANDed: [{"column": str, "op": one of '
                   + ", ".join(f'"{o}"' for o in OPS)
                   + ', "value": scalar | [values] for in | [low, high] for between}]. Dates as "YYYY-MM-DD".',
}
_AGG_SPEC = {"type": "string", "enum": list(AGGS), "required": False, "default": "sum"}

TOOL_SPECS: list[dict] = [
    {"name": "group_aggregate", "description": "Aggregate a metric per group, sorted high to low. Use for 'which X has the most Y', totals or averages by a category.",
     "args": {"by": {"type": "column", "required": True, "description": "grouping column (usually categorical)"},
              "metric": {"type": "column", "kind": "numeric", "required": False, "description": "column to aggregate; omit with agg=count"},
              "agg": _AGG_SPEC, "top": {"type": "integer", "required": False, "default": 10},
              "filters": _FILTERS_SPEC}},
    {"name": "time_trend", "description": "A metric per time period, in time order. Use for trends, growth, seasonality, 'over time', 'by month'.",
     "args": {"date_col": {"type": "column", "kind": "datetime", "required": True},
              "metric": {"type": "column", "kind": "numeric", "required": False, "description": "omit with agg=count"},
              "agg": _AGG_SPEC,
              "grain": {"type": "string", "enum": list(GRAINS), "required": False, "default": "month"},
              "filters": _FILTERS_SPEC}},
    {"name": "distribution", "description": "Histogram and percentiles (min, p25, median, mean, p75, max, std, skewness) of one numeric column; counts per value for categorical.",
     "args": {"column": {"type": "column", "required": True},
              "bins": {"type": "integer", "required": False, "default": 20}, "filters": _FILTERS_SPEC}},
    {"name": "top_categories", "description": "Most frequent values of a column with counts and percent share.",
     "args": {"column": {"type": "column", "required": True},
              "top": {"type": "integer", "required": False, "default": 10}, "filters": _FILTERS_SPEC}},
    {"name": "correlation", "description": "Pearson correlation for every pair of numeric columns (nulls skipped pairwise), strongest first.",
     "args": {"columns": {"type": "array of column", "kind": "numeric", "required": False, "description": "2-12 numeric columns; omit for all numeric columns"}}},
    {"name": "outliers", "description": "IQR outlier check (1.5 x IQR fences) on a numeric column; returns fences, counts and the most extreme rows.",
     "args": {"column": {"type": "column", "kind": "numeric", "required": True}}},
    {"name": "compare_groups", "description": "Count, mean, median, std, min, max of a numeric metric per group, plus the overall mean and the gap between highest and lowest group.",
     "args": {"by": {"type": "column", "required": True},
              "metric": {"type": "column", "kind": "numeric", "required": True}, "filters": _FILTERS_SPEC}},
    {"name": "crosstab", "description": "Two-way table: count (or agg of metric) for each combination of two columns (top 15 x top 10 values).",
     "args": {"row": {"type": "column", "required": True}, "col": {"type": "column", "required": True},
              "metric": {"type": "column", "kind": "numeric", "required": False},
              "agg": {"type": "string", "enum": list(AGGS), "required": False, "default": "count, or sum when metric is given"}}},
    {"name": "scatter", "description": "Sample of (x, y) points, optional colour column, plus correlation r. Use to show a relationship.",
     "args": {"x": {"type": "column", "kind": "numeric", "required": True}, "y": {"type": "column", "kind": "numeric", "required": True},
              "color": {"type": "column", "required": False}, "limit": {"type": "integer", "required": False, "default": 500}}},
    {"name": "describe_column", "description": "Everything about one column: nulls, distinct values, stats or top values, and its histogram/trend.",
     "args": {"column": {"type": "column", "required": True}}},
    {"name": "filter_rows", "description": "Return matching rows (up to limit) and the number of rows that match. Use for 'show me', 'how many rows where', or looking at examples.",
     "args": {"filters": _FILTERS_SPEC | {"required": True}, "columns": {"type": "array of column", "required": False},
              "limit": {"type": "integer", "required": False, "default": 50}}},
]

_SPEC_BY_NAME = {s["name"]: s for s in TOOL_SPECS}


def validate_args(kinds: dict[str, str], tool: str, args: Any, fuzzy: bool = True) -> dict:
    """Check and repair planner-supplied args against the schema without running anything.
    Unknown args are dropped, column names are repaired (case / near-miss). Raises ToolError."""
    if tool not in TOOLS:
        raise ToolError(f"Unknown tool '{tool}'. Valid tools: {', '.join(TOOLS)}")
    if not isinstance(args, dict):
        raise ToolError("args must be an object")
    spec = _SPEC_BY_NAME[tool]["args"]
    out: dict[str, Any] = {}
    for name, s in spec.items():
        v = args.get(name)
        if v in (None, "", []):
            if s.get("required"):
                raise ToolError(f"{tool}: missing required argument '{name}'")
            continue
        t = s["type"]
        want = (s["kind"],) if s.get("kind") else None
        if t == "column":
            v = resolve_column(kinds, v, want, name, fuzzy)
        elif t == "array of column":
            v = [v] if isinstance(v, str) else v
            if not isinstance(v, list):
                raise ToolError(f"{tool}: '{name}' must be a list of columns")
            v = [resolve_column(kinds, c, want, name, fuzzy) for c in v]
        elif t == "integer":
            v = _int_arg(v, name, int(s.get("default", 10)) if str(s.get("default", "")).isdigit() else 10, 1, 2000)
        elif name == "agg":
            v = _agg_arg(v)
        elif name == "grain":
            v = _grain_arg(v)
        elif name == "filters":
            v = normalize_filters(kinds, v, fuzzy)
        out[name] = v
    # cross-arg checks that the tool would otherwise fail on
    agg = out.get("agg", "sum")
    if tool in ("group_aggregate", "time_trend"):
        if "metric" not in out and agg != "count":
            raise ToolError(f"{tool}: 'metric' is required unless agg is 'count'")
    if tool == "crosstab" and out.get("row") == out.get("col"):
        raise ToolError("crosstab needs two different columns")
    if tool == "correlation" and "columns" in out and len(set(out["columns"])) < 2:
        raise ToolError("correlation needs at least 2 numeric columns")
    return out


def run_tool(ds: Dataset, tool: str, args: dict | None = None) -> dict:
    fn = TOOLS.get(tool)
    if fn is None:
        raise ToolError(f"Unknown tool '{tool}'. Valid tools: {', '.join(TOOLS)}")
    args = dict(args or {})
    spec = _SPEC_BY_NAME[tool]["args"]
    unknown = [a for a in args if a not in spec]
    for a in unknown:
        args.pop(a)
    try:
        return fn(ds, **args)
    except TypeError as exc:
        raise ToolError(f"{tool}: bad arguments ({exc}). Expected: {', '.join(spec)}") from exc
