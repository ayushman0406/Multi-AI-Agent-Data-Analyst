"""Dataset loading (DuckDB in-memory table `data`) and a batched-SQL profile."""

from __future__ import annotations

import datetime as _dt
import decimal
import math
import threading
from pathlib import Path
from typing import Any

import duckdb

from .config import get_settings

SUPPORTED_EXTENSIONS = {".csv", ".tsv", ".txt", ".parquet", ".json", ".jsonl", ".ndjson", ".xlsx"}

_NUMERIC_PREFIXES = ("TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT", "UTINYINT", "USMALLINT", "UINTEGER",
                     "UBIGINT", "UHUGEINT", "FLOAT", "DOUBLE", "REAL", "DECIMAL", "NUMERIC")
_DATETIME_PREFIXES = ("DATE", "TIMESTAMP", "TIME")


def quote_ident(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def kind_of(dtype: str) -> str:
    t = dtype.upper()
    if t.startswith("BOOL"):
        return "boolean"
    if t.startswith(_NUMERIC_PREFIXES):
        return "numeric"
    if t.startswith(_DATETIME_PREFIXES):
        return "datetime"
    if t.startswith(("VARCHAR", "ENUM", "UUID", "CHAR", "STRING", "TEXT")):
        return "categorical"
    return "other"


def jsonable(value: Any, ndigits: int = 4) -> Any:
    """Convert DuckDB / numpy values to JSON-safe Python, rounding floats."""
    if value is None or isinstance(value, (bool, str, int)):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return round(value, ndigits)
    if isinstance(value, decimal.Decimal):
        return jsonable(float(value), ndigits)
    if isinstance(value, _dt.datetime):
        if value.hour == value.minute == value.second == value.microsecond == 0:
            return value.date().isoformat()
        return value.isoformat(sep=" ")
    if isinstance(value, (_dt.date, _dt.time)):
        return value.isoformat()
    if isinstance(value, _dt.timedelta):
        return str(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v, ndigits) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v, ndigits) for v in value]
    if hasattr(value, "item"):  # numpy scalar
        try:
            return jsonable(value.item(), ndigits)
        except Exception:
            pass
    return str(value)


class Dataset:
    """A single table `data` in an in-memory DuckDB connection."""

    def __init__(self, con: duckdb.DuckDBPyConnection, name: str = "data"):
        self.con = con
        self.name = name
        self.lock = threading.RLock()
        self._coerce_text_numbers()
        self._coerce_text_dates()
        self._refresh_schema()

    # -- constructors --------------------------------------------------------------------------
    @classmethod
    def from_path(cls, path: str | Path, name: str | None = None, max_rows: int | None = None) -> "Dataset":
        path = Path(path)
        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
        max_rows = max_rows or get_settings().max_rows
        con = duckdb.connect(":memory:")
        p = str(path)
        nulls = "nullstr=['', 'NA', 'N/A', 'NaN', 'nan', 'null', 'NULL', 'None', '#N/A']"
        if ext in (".csv", ".txt"):
            src = f"read_csv_auto(?, sample_size=-1, {nulls})"
        elif ext == ".tsv":
            src = f"read_csv_auto(?, delim='\t', sample_size=-1, {nulls})"
        elif ext == ".parquet":
            src = "read_parquet(?)"
        elif ext in (".json", ".jsonl", ".ndjson"):
            src = "read_json_auto(?)"
        else:  # .xlsx via pandas/openpyxl
            import pandas as pd

            df = pd.read_excel(p, engine="openpyxl", nrows=max_rows)
            df.columns = [str(c) for c in df.columns]
            con.register("_frame", df)
            con.execute("CREATE TABLE data AS SELECT * FROM _frame")
            con.unregister("_frame")
            return cls(con, name or path.stem)
        con.execute(f"CREATE TABLE data AS SELECT * FROM {src} LIMIT {int(max_rows)}", [p])
        return cls(con, name or path.stem)

    @classmethod
    def from_frame(cls, df, name: str = "data") -> "Dataset":
        con = duckdb.connect(":memory:")
        df = df.copy()
        df.columns = [str(c) for c in df.columns]
        con.register("_frame", df)
        con.execute("CREATE TABLE data AS SELECT * FROM _frame")
        con.unregister("_frame")
        return cls(con, name)

    # -- schema --------------------------------------------------------------------------------
    def _refresh_schema(self) -> None:
        rows = self.con.execute("DESCRIBE data").fetchall()
        self.columns: list[str] = [r[0] for r in rows]
        self.dtypes: dict[str, str] = {r[0]: str(r[1]) for r in rows}
        self.kinds: dict[str, str] = {c: kind_of(t) for c, t in self.dtypes.items()}
        self.row_count: int = self.con.execute("SELECT COUNT(*) FROM data").fetchone()[0]

    def _coerce_text_numbers(self) -> None:
        """Text columns whose every non-null value is a number (e.g. 'NA'-padded CSVs) become DOUBLE."""
        rows = self.con.execute("DESCRIBE data").fetchall()
        text_cols = [r[0] for r in rows if kind_of(str(r[1])) == "categorical"]
        if not text_cols:
            return
        exprs = [f"COUNT({quote_ident(c)}) AS n{i}, COUNT(TRY_CAST({quote_ident(c)} AS DOUBLE)) AS d{i}"
                 for i, c in enumerate(text_cols)]
        res = self.con.execute(f"SELECT {', '.join(exprs)} FROM data").fetchone()
        convert = [c for i, c in enumerate(text_cols) if res[2 * i] > 0 and res[2 * i] == res[2 * i + 1]]
        if convert:
            repl = ", ".join(f"TRY_CAST({quote_ident(c)} AS DOUBLE) AS {quote_ident(c)}" for c in convert)
            self.con.execute(f"CREATE OR REPLACE TABLE data AS SELECT * REPLACE ({repl}) FROM data")

    def _coerce_text_dates(self) -> None:
        """Turn text columns whose every non-null value parses as a date/timestamp into TIMESTAMP."""
        rows = self.con.execute("DESCRIBE data").fetchall()
        text_cols = [r[0] for r in rows if kind_of(str(r[1])) == "categorical"]
        if not text_cols:
            return
        exprs = []
        for c in text_cols:
            q = quote_ident(c)
            exprs.append(
                f"COUNT({q}) AS n{len(exprs)}, COUNT(TRY_CAST({q} AS TIMESTAMP)) AS d{len(exprs)}, "
                f"COUNT(*) FILTER (WHERE regexp_matches(CAST({q} AS VARCHAR), '^\\d{{4}}-\\d{{1,2}}-\\d{{1,2}}')) AS r{len(exprs)}"
            )
        res = self.con.execute(f"SELECT {', '.join(exprs)} FROM data").fetchone()
        convert = [c for i, c in enumerate(text_cols)
                   if res[3 * i] > 0 and res[3 * i] == res[3 * i + 1] == res[3 * i + 2]]
        if convert:
            repl = ", ".join(f"TRY_CAST({quote_ident(c)} AS TIMESTAMP) AS {quote_ident(c)}" for c in convert)
            self.con.execute(f"CREATE OR REPLACE TABLE data AS SELECT * REPLACE ({repl}) FROM data")

    # -- queries -------------------------------------------------------------------------------
    def query(self, sql: str, params: list | None = None) -> list[dict]:
        with self.lock:
            cur = self.con.execute(sql, params or [])
            names = [d[0] for d in cur.description]
            return [dict(zip(names, (jsonable(v) for v in row))) for row in cur.fetchall()]

    def scalar(self, sql: str, params: list | None = None) -> Any:
        with self.lock:
            row = self.con.execute(sql, params or []).fetchone()
        return jsonable(row[0]) if row else None

    def close(self) -> None:
        try:
            self.con.close()
        except Exception:
            pass

    # -- profile -------------------------------------------------------------------------------
    def profile(self) -> dict:
        with self.lock:
            return self._profile()

    def _profile(self) -> dict:
        cols = self.columns
        n = self.row_count
        exprs: list[str] = []
        for i, c in enumerate(cols):
            q = quote_ident(c)
            k = self.kinds[c]
            exprs.append(f"COUNT({q}) AS c{i}")
            exprs.append(f"COUNT(DISTINCT {q}) AS u{i}")
            if k == "numeric":
                d = f"CAST({q} AS DOUBLE)"
                exprs += [f"MIN({d}) AS mn{i}", f"MAX({d}) AS mx{i}", f"AVG({d}) AS av{i}",
                          f"MEDIAN({d}) AS md{i}", f"STDDEV_SAMP({d}) AS sd{i}"]
            elif k == "datetime":
                exprs += [f"MIN({q}) AS mn{i}", f"MAX({q}) AS mx{i}"]
        agg = dict(zip([e.rsplit(" AS ", 1)[1] for e in exprs],
                       self.con.execute(f"SELECT {', '.join(exprs)} FROM data").fetchone())) if exprs else {}

        duplicate_rows = 0
        if cols:
            duplicate_rows = self.con.execute(
                "SELECT (SELECT COUNT(*) FROM data) - (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM data))"
            ).fetchone()[0]

        # top values for categorical/boolean columns, one UNION ALL query
        cat_idx = [i for i, c in enumerate(cols) if self.kinds[c] in ("categorical", "boolean")]
        tops: dict[int, list[dict]] = {i: [] for i in cat_idx}
        if cat_idx:
            parts = [
                f"SELECT * FROM (SELECT {i} AS ci, CAST({quote_ident(cols[i])} AS VARCHAR) AS v, COUNT(*) AS n "
                f"FROM data WHERE {quote_ident(cols[i])} IS NOT NULL GROUP BY 2 ORDER BY 3 DESC, 2 LIMIT 5)"
                for i in cat_idx
            ]
            for ci, v, cnt in self.con.execute(" UNION ALL ".join(parts)).fetchall():
                tops[ci].append({"value": v, "count": cnt})
            for i in cat_idx:
                tops[i].sort(key=lambda t: (-t["count"], t["value"]))

        # 12-bin histograms for numeric columns, one UNION ALL query
        bins = 12
        hist: dict[int, list[dict]] = {}
        parts = []
        for i, c in enumerate(cols):
            if self.kinds[c] != "numeric":
                continue
            lo, hi = agg.get(f"mn{i}"), agg.get(f"mx{i}")
            if lo is None or hi is None:
                continue
            lo, hi = float(lo), float(hi)
            if not (math.isfinite(lo) and math.isfinite(hi)):
                continue
            width = (hi - lo) / bins if hi > lo else 1.0
            hist[i] = [{"start": jsonable(lo + b * width), "end": jsonable(lo + (b + 1) * width), "count": 0}
                       for b in range(bins if hi > lo else 1)]
            d = f"CAST({quote_ident(c)} AS DOUBLE)"
            parts.append(
                f"SELECT {i} AS ci, LEAST(CAST(FLOOR(({d} - {lo!r}) / {width!r}) AS BIGINT), {len(hist[i]) - 1}) AS b, "
                f"COUNT(*) AS n FROM data WHERE {d} IS NOT NULL AND isfinite({d}) GROUP BY 2"
            )
        if parts:
            for ci, b, cnt in self.con.execute(" UNION ALL ".join(parts)).fetchall():
                if b is not None and 0 <= b < len(hist[ci]):
                    hist[ci][b]["count"] = cnt

        columns = []
        for i, c in enumerate(cols):
            k = self.kinds[c]
            nonnull = agg.get(f"c{i}", 0) or 0
            col: dict[str, Any] = {
                "name": c,
                "dtype": self.dtypes[c],
                "kind": k,
                "null_count": n - nonnull,
                "null_pct": round(100.0 * (n - nonnull) / n, 2) if n else 0.0,
                "distinct_count": agg.get(f"u{i}", 0),
            }
            if k == "numeric":
                for key, alias in (("min", "mn"), ("max", "mx"), ("mean", "av"), ("median", "md"), ("stddev", "sd")):
                    col[key] = jsonable(agg.get(f"{alias}{i}"))
                col["histogram"] = hist.get(i, [])
            elif k == "datetime":
                col["min"] = jsonable(agg.get(f"mn{i}"))
                col["max"] = jsonable(agg.get(f"mx{i}"))
            if k in ("categorical", "boolean"):
                col["top_values"] = tops.get(i, [])
            columns.append(col)

        sample = self.con.execute("SELECT * FROM data LIMIT 5")
        names = [d[0] for d in sample.description]
        sample_rows = [dict(zip(names, (jsonable(v) for v in r))) for r in sample.fetchall()]
        return jsonable({
            "name": self.name,
            "row_count": n,
            "column_count": len(cols),
            "duplicate_rows": duplicate_rows,
            "columns": columns,
            "sample_rows": sample_rows,
        })
