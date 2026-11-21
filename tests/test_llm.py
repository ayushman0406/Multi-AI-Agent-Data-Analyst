import pytest

from analyst.llm import LLM, LLMBadJSON, LLMUnavailable, RETRY_HINT, strip_fences
from conftest import FakeLLM


def test_strip_fences():
    assert strip_fences('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert strip_fences("```\n{}\n```") == "{}"
    assert strip_fences('  {"a": 2} ') == '{"a": 2}'


def test_ask_json_strips_fences():
    llm = FakeLLM(lambda s, u, m: '```json\n{"steps": [1, 2]}\n```')
    assert llm.ask_json("sys", "hi") == {"steps": [1, 2]}
    assert llm.calls[0]["json_mode"] is True


def test_ask_json_retries_once_then_succeeds():
    replies = iter(["not json at all", '{"ok": true}'])
    llm = FakeLLM(lambda s, u, m: next(replies))
    assert llm.ask_json("sys", "hi") == {"ok": True}
    assert len(llm.calls) == 2
    assert llm.calls[1]["messages"][-1]["content"] == RETRY_HINT


def test_ask_json_raises_bad_json_after_retry():
    llm = FakeLLM(lambda s, u, m: "still not json")
    with pytest.raises(LLMBadJSON):
        llm.ask_json("sys", "hi")
    assert len(llm.calls) == 2


def test_missing_key_is_unavailable():
    llm = LLM()
    assert not llm.available
    with pytest.raises(LLMUnavailable):
        llm.ask("sys", "hi")
    with pytest.raises(LLMUnavailable):
        llm.ask_json("sys", "hi")


def test_key_fallback_and_overrides(monkeypatch):
    from analyst import config

    monkeypatch.setenv("GROQ_API_KEY", "g")
    assert config.get_settings().api_key == "g"
    monkeypatch.setenv("LLM_API_KEY", "l")
    assert config.get_settings().api_key == "l"
    config.set_overrides(api_key="o", model="m1")
    s = config.get_settings()
    assert (s.api_key, s.model) == ("o", "m1")
    assert LLM().model == "m1"
    assert LLM(model="m2").model == "m2"
