import json

import pytest
from fastapi.testclient import TestClient

from server.main import app, sessions


@pytest.fixture
def client():
    sessions.clear()
    with TestClient(app) as c:
        yield c
    sessions.clear()


def parse_sse(text):
    events = []
    for block in text.strip().split("\n\n"):
        name, data = None, None
        for line in block.splitlines():
            if line.startswith("event: "):
                name = line[7:]
            elif line.startswith("data: "):
                data = json.loads(line[6:])
        if name:
            events.append((name, data))
    return events


def test_health(client):
    r = client.get("/api/health").json()
    assert r["ok"] is True
    assert r["llm"]["configured"] is False
    assert r["llm"]["model"] and r["llm"]["base_url_host"]


def test_samples(client):
    items = client.get("/api/samples").json()
    ids = {s["id"] for s in items}
    assert "retail_orders" in ids
    retail = next(s for s in items if s["id"] == "retail_orders")
    assert retail["rows"] == 3000 and retail["columns"] == 10


def _create(client):
    r = client.post("/api/sessions", data={"sample_id": "retail_orders"})
    assert r.status_code == 200, r.text
    return r.json()


def test_create_session_from_sample(client):
    body = _create(client)
    assert body["session_id"]
    assert body["dataset"] == {"name": "Retail orders", "rows": 3000, "columns": 10}
    assert body["profile"]["row_count"] == 3000
    got = client.get(f"/api/sessions/{body['session_id']}").json()
    assert got["session_id"] == body["session_id"] and got["turns"] == []


def test_understand_stream(client):
    sid = _create(client)["session_id"]
    with client.stream("GET", f"/api/sessions/{sid}/understand") as r:
        assert r.headers["content-type"].startswith("text/event-stream")
        events = parse_sse(r.read().decode())
    assert [n for n, _ in events] == ["profile", "understanding", "done"]
    assert events[1][1]["understanding"]["suggested_questions"]


def test_ask_stream(client):
    sid = _create(client)["session_id"]
    with client.stream("POST", f"/api/sessions/{sid}/ask", json={"question": "average discount by region"}) as r:
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        events = parse_sse(r.read().decode())
    names = [n for n, _ in events]
    assert names[0] == "plan" and names[-1] == "done"
    assert names[-3:] == ["answer", "grounding", "done"]
    assert "tool_start" in names and "tool_result" in names
    turn = events[-1][1]["turn"]
    assert turn["question"] == "average discount by region"
    west = next(d for d in turn["results"][0]["result"]["data"] if d["region"] == "West")
    assert west["mean_discount"] > 0.12
    s = client.get(f"/api/sessions/{sid}").json()
    assert len(s["turns"]) == 1
    md = client.get(f"/api/sessions/{sid}/report.md")
    assert md.status_code == 200 and "average discount by region" in md.text


def test_upload_csv(client):
    r = client.post("/api/sessions", files={"file": ("mini.csv", b"a,b\nx,1\ny,2\n", "text/csv")})
    assert r.status_code == 200, r.text
    assert r.json()["dataset"] == {"name": "mini", "rows": 2, "columns": 2}


def test_upload_too_large(client, monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_MB", "1")
    big = b"a,b\n" + b"1,2\n" * (300 * 1024)  # ~1.2 MB
    r = client.post("/api/sessions", files={"file": ("big.csv", big, "text/csv")})
    assert r.status_code == 413


def test_upload_bad_type(client):
    r = client.post("/api/sessions", files={"file": ("evil.exe", b"MZ", "application/octet-stream")})
    assert r.status_code == 415


def test_unknown_session_and_sample(client):
    assert client.get("/api/sessions/nope").status_code == 404
    assert client.post("/api/sessions", data={"sample_id": "nope"}).status_code == 404


def test_settings_roundtrip(client):
    r = client.put("/api/settings", json={"api_key": "sk-secret", "model": "some/model"}).json()
    assert r == {"model": "some/model", "base_url": r["base_url"], "has_key": True}
    assert "sk-secret" not in json.dumps(client.get("/api/settings").json())
    assert client.get("/api/health").json()["llm"]["configured"] is True
    client.put("/api/settings", json={"api_key": "", "model": ""})
    assert client.get("/api/settings").json()["has_key"] is False


def test_demo(client):
    r = client.get("/api/demo")
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] in ("offline", "llm") and body["turns"]
