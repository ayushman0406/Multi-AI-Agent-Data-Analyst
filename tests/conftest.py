import json
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analyst import config  # noqa: E402
from analyst.data import Dataset  # noqa: E402
from analyst.llm import LLM  # noqa: E402

ROWS = [
    ("N", 2, 10.0, "2026-01-01"),
    ("N", 4, 10.0, "2026-01-02"),
    ("S", 6, 20.0, "2026-01-02"),
    ("S", None, 20.0, "2026-01-03"),
    ("S", 6, 20.0, "2026-01-02"),
]


@pytest.fixture(autouse=True)
def no_llm_env(monkeypatch):
    """Tests never touch the network: no key from the environment, no runtime overrides."""
    for k in ("LLM_API_KEY", "GROQ_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    config.clear_overrides()
    yield
    config.clear_overrides()


@pytest.fixture
def tiny_ds():
    df = pd.DataFrame(ROWS, columns=["region", "units", "price", "date"])
    return Dataset.from_frame(df, "tiny")


class FakeLLM(LLM):
    """An LLM whose transport is a function of (system, messages). Records every call."""

    def __init__(self, responder):
        super().__init__(api_key="fake-key", base_url="http://fake.invalid/v1", model="fake-model")
        self.responder = responder
        self.calls: list[dict] = []

    def _complete(self, messages, json_mode):
        system = messages[0]["content"]
        user = "\n".join(m["content"] for m in messages[1:] if m["role"] == "user")
        self.calls.append({"system": system, "user": user, "messages": messages, "json_mode": json_mode})
        out = self.responder(system, user, messages)
        return out if isinstance(out, str) else json.dumps(out)

    def prompts_for(self, role: str) -> list[str]:
        key = {"plan": "planner of a data-analysis", "answer": "reply of a data-analysis",
               "understand": "first brief"}[role]
        return [c["user"] for c in self.calls if key in c["system"]]


def role_of(system: str) -> str:
    if "planner of a data-analysis" in system:
        return "plan"
    if "reply of a data-analysis" in system:
        return "answer"
    return "understand"


@pytest.fixture
def fake_llm_factory():
    return FakeLLM
