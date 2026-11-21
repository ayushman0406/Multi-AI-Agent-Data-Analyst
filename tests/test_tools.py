import pytest

from analyst.tools import TOOL_SPECS, TOOLS, ToolError, run_tool, validate_args


def test_registry_matches_specs():
    assert {s["name"] for s in TOOL_SPECS} == set(TOOLS)
    assert set(TOOLS) == {"group_aggregate", "time_trend", "distribution", "top_categories", "correlation",
                          "outliers", "compare_groups", "crosstab", "scatter", "describe_column", "filter_rows"}


def test_result_shape(tiny_ds):
    r = run_tool(tiny_ds, "group_aggregate", {"by": "region", "metric": "units"})
    assert set(r) == {"tool", "args", "title", "data", "chart", "summary"}
    assert r["chart"]["type"] == "bar"


def test_group_aggregate_sum_ordered(tiny_ds):
    r = run_tool(tiny_ds, "group_aggregate", {"by": "region", "metric": "units", "agg": "sum"})
    assert [(d["region"], d["sum_units"]) for d in r["data"]] == [("S", 12), ("N", 6)]
    assert r["summary"]["top_group"] == "S" and r["summary"]["total"] == 18


def test_group_aggregate_count_and_mean(tiny_ds):
    r = run_tool(tiny_ds, "group_aggregate", {"by": "region", "agg": "count"})
    assert {d["region"]: d["count"] for d in r["data"]} == {"S": 3, "N": 2}
    r = run_tool(tiny_ds, "group_aggregate", {"by": "region", "metric": "units", "agg": "mean"})
    assert {d["region"]: d["mean_units"] for d in r["data"]} == {"S": 6, "N": 3}


def test_correlation_skips_nulls(tiny_ds):
    r = run_tool(tiny_ds, "correlation", {"columns": ["units", "price"]})
    pair = r["data"][0]
    assert pair["r"] == pytest.approx(0.9045, abs=1e-4)
    assert pair["n"] == 4


def test_unknown_column_names_valid_columns(tiny_ds):
    with pytest.raises(ToolError) as e:
        run_tool(tiny_ds, "group_aggregate", {"by": "regoin", "metric": "units"})
    msg = str(e.value)
    assert "regoin" in msg and "region" in msg and "units" in msg and "price" in msg


def test_bad_agg(tiny_ds):
    with pytest.raises(ToolError, match="agg"):
        run_tool(tiny_ds, "group_aggregate", {"by": "region", "metric": "units", "agg": "explode"})


def test_sum_of_text_column_rejected(tiny_ds):
    with pytest.raises(ToolError, match="numeric"):
        run_tool(tiny_ds, "group_aggregate", {"by": "units", "metric": "region", "agg": "sum"})


def test_filters(tiny_ds):
    r = run_tool(tiny_ds, "group_aggregate", {"by": "region", "metric": "units",
                                              "filters": [{"column": "region", "op": "!=", "value": "S"}]})
    assert [d["region"] for d in r["data"]] == ["N"]
    r = run_tool(tiny_ds, "filter_rows", {"filters": [{"column": "units", "op": ">=", "value": 4},
                                                      {"column": "date", "op": "between",
                                                       "value": ["2026-01-02", "2026-01-02"]}]})
    assert r["summary"]["matched_rows"] == 3
    r = run_tool(tiny_ds, "filter_rows", {"filters": [{"column": "region", "op": "in", "value": ["N"]}]})
    assert r["summary"]["matched_rows"] == 2
    r = run_tool(tiny_ds, "filter_rows", {"filters": [{"column": "region", "op": "contains", "value": "s"}]})
    assert r["summary"]["matched_rows"] == 3


def test_filters_reject_sql_injection(tiny_ds):
    with pytest.raises(ToolError, match="Valid columns"):
        run_tool(tiny_ds, "filter_rows", {"filters": [{"column": 'region" = region; DROP TABLE data; --',
                                                       "op": "=", "value": "S"}]})
    with pytest.raises(ToolError):
        run_tool(tiny_ds, "filter_rows", {"filters": [{"column": "region", "op": "= 1 OR 1=1 --", "value": "S"}]})
    # a malicious value is just a value: bound as a parameter, matches nothing, table intact
    r = run_tool(tiny_ds, "filter_rows", {"filters": [{"column": "region", "op": "=",
                                                       "value": "S' OR '1'='1"}]})
    assert r["summary"]["matched_rows"] == 0
    assert tiny_ds.scalar("SELECT COUNT(*) FROM data") == 5


def test_time_trend_ordered(tiny_ds):
    r = run_tool(tiny_ds, "time_trend", {"date_col": "date", "metric": "units", "agg": "sum", "grain": "day"})
    periods = [d["period"] for d in r["data"]]
    assert periods == sorted(periods) == ["2026-01-01", "2026-01-02", "2026-01-03"]
    assert [d["sum_units"] for d in r["data"]][:2] == [2, 16]
    assert r["chart"]["type"] == "line"


def test_time_trend_needs_datetime(tiny_ds):
    with pytest.raises(ToolError, match="datetime"):
        run_tool(tiny_ds, "time_trend", {"date_col": "region", "metric": "units"})


def test_other_tools_run(tiny_ds):
    calls = [("distribution", {"column": "units", "bins": 4}), ("top_categories", {"column": "region"}),
             ("outliers", {"column": "units"}), ("compare_groups", {"by": "region", "metric": "price"}),
             ("crosstab", {"row": "region", "col": "date"}), ("scatter", {"x": "units", "y": "price"}),
             ("describe_column", {"column": "units"}), ("describe_column", {"column": "region"}),
             ("correlation", {})]
    for tool, args in calls:
        r = run_tool(tiny_ds, tool, args)
        assert r["tool"] == tool and isinstance(r["summary"], dict)
    cg = run_tool(tiny_ds, "compare_groups", {"by": "region", "metric": "price"})
    assert cg["summary"]["highest_group"] == "S" and cg["summary"]["highest_mean"] == 20


def test_unknown_tool(tiny_ds):
    with pytest.raises(ToolError):
        run_tool(tiny_ds, "rm_rf", {})


def test_validate_args_repairs_and_rejects(tiny_ds):
    out = validate_args(tiny_ds.kinds, "group_aggregate", {"by": "Region", "metric": "unit", "bogus": 1})
    assert out["by"] == "region" and out["metric"] == "units" and "bogus" not in out
    with pytest.raises(ToolError):
        validate_args(tiny_ds.kinds, "group_aggregate", {"metric": "units"})
