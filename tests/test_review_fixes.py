"""Regression tests for issues found in the final branch review."""
import httpx
import openai
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from analyst.config import clear_overrides, get_settings, set_overrides
from analyst.data import Dataset
from analyst.llm import LLM, LLMUnavailable
from analyst.session import AnalysisSession
from analyst.tools import ToolError, run_tool
from conftest import FakeLLM


def _err(cls, status, msg):
    req = httpx.Request("POST", "http://x.invalid/v1/chat/completions")
    return cls(msg, response=httpx.Response(status, request=req), body=None)


class _Stub:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.chat = self
        self.completions = self

    def create(self, **kw):
        out = self.outcomes.pop(0)
        if isinstance(out, Exception):
            raise out
        return out


def test_retry_without_response_format_errors_become_unavailable():
    llm = LLM(api_key="k", base_url="http://x.invalid/v1", model="m")
    llm._client = _Stub([_err(openai.BadRequestError, 400, "response_format not supported"),
                         _err(openai.RateLimitError, 429, "slow down")])
    with pytest.raises(LLMUnavailable):
        llm.ask_json("sys", "user")


def test_empty_choices_become_unavailable():
    class R:
        choices = []
    llm = LLM(api_key="k", base_url="http://x.invalid/v1", model="m")
    llm._client = _Stub([R()])
    with pytest.raises(LLMUnavailable):
        llm.ask("sys", "user")


def test_unexpected_llm_exception_falls_back_instead_of_killing_turn(tiny_ds):
    def boom(system, user, messages):
        raise RuntimeError("provider exploded")
    s = AnalysisSession(tiny_ds, llm=FakeLLM(boom))
    turn = s.ask("units by region", lambda n, d: None)
    assert turn["results"] and turn["answer_md"]


def test_infinite_int_arg_is_tool_error(tiny_ds):
    with pytest.raises(ToolError):
        run_tool(tiny_ds, "top_categories", {"column": "region", "top": float("inf")})


def _ds(df):
    return Dataset.from_frame(df, name="t")


def test_time_trend_summary_covers_all_periods():
    days = pd.date_range("2020-01-01", periods=1500, freq="D")
    ds = _ds(pd.DataFrame({"d": days, "v": range(1500)}))
    res = run_tool(ds, "time_trend", {"date_col": "d", "metric": "v", "agg": "sum", "grain": "day"})
    assert str(res["summary"]["last_period"]).startswith(str(days[-1].date()))
    assert res["summary"]["periods"] == 1500


def test_compare_groups_summary_covers_all_groups():
    df = pd.DataFrame({"g": [f"g{i:02d}" for i in range(40)], "v": [float(i) for i in range(40)]})
    res = run_tool(_ds(df), "compare_groups", {"by": "g", "metric": "v"})
    assert res["summary"]["groups"] == 40
    assert res["summary"]["lowest_group"] == "g00"


def test_distribution_counts_every_row_despite_rounding():
    ds = _ds(pd.DataFrame({"x": [1.23456, 2, 3, 4, 5]}))
    res = run_tool(ds, "distribution", {"column": "x", "bins": 4})
    assert sum(b["count"] for b in res["data"]) == 5


def test_report_download_with_non_latin_name():
    from server.main import app, sessions
    with TestClient(app) as c:
        r = c.post("/api/sessions", files={"file": ("данные.csv", b"a,b\nx,1\ny,2\n", "text/csv")})
        sid = r.json()["session_id"]
        assert c.get(f"/api/sessions/{sid}/report.md").status_code == 200
    sessions.clear()


def test_ui_entered_key_is_not_sent_to_a_different_host(monkeypatch):
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    clear_overrides()
    try:
        set_overrides(api_key="ui-key")
        assert get_settings().api_key == "ui-key"
        set_overrides(base_url="https://attacker.example/v1")
        assert get_settings().api_key == ""
    finally:
        clear_overrides()


def test_key_never_sent_over_plain_http_to_same_host(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "server-env-key")
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    clear_overrides()
    try:
        set_overrides(base_url="http://api.groq.com/openai/v1")
        assert get_settings().api_key == ""
    finally:
        clear_overrides()


def test_operator_configured_http_endpoint_keeps_its_key(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "ollama")
    monkeypatch.setenv("LLM_BASE_URL", "http://gpu-box:11434/v1")
    clear_overrides()
    assert get_settings().api_key == "ollama"



def test_chunked_upload_over_limit_stops_reading_early(monkeypatch):
    """The body must be cut off once it passes the limit, not spooled to disk first."""
    import asyncio
    from server.main import app
    monkeypatch.setenv("MAX_UPLOAD_MB", "1")
    chunk, total_chunks = 65536, 160  # 10 MB offered
    state = {"sent": 0, "status": None}

    async def receive():
        if state["sent"] == 0:
            state["sent"] += 1
            return {"type": "http.request", "body": b"--XyZ\r\nContent-Disposition: form-data; name=\"file\"; "
                    b"filename=\"big.csv\"\r\n\r\n", "more_body": True}
        if state["sent"] <= total_chunks:
            state["sent"] += 1
            return {"type": "http.request", "body": b"a" * chunk, "more_body": True}
        return {"type": "http.request", "body": b"\r\n--XyZ--\r\n", "more_body": False}

    async def send(msg):
        if msg["type"] == "http.response.start":
            state["status"] = msg["status"]

    scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": "POST",
             "scheme": "http", "path": "/api/sessions", "raw_path": b"/api/sessions", "query_string": b"",
             "root_path": "", "server": ("test", 80), "client": ("test", 1),
             "headers": [(b"content-type", b"multipart/form-data; boundary=XyZ"),
                         (b"transfer-encoding", b"chunked")]}
    asyncio.run(app(scope, receive, send))
    assert state["status"] == 413
    assert state["sent"] * chunk < 2 * 1024 * 1024  # stopped soon after 1 MB
