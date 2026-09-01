import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "agent_stages" in data


def test_sample_and_chat_flow():
    # 1. Load sample dataset
    res = client.get("/api/sample")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["total_rows"] > 0
    assert len(data["columns"]) == 14

    # 2. Test chat
    chat_res = client.post("/api/chat", json={"message": "Summarize the primary metrics."})
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert "reply" in chat_data
    assert len(chat_data["reply"]) > 10
