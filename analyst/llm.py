"""Thin wrapper over any OpenAI-compatible chat endpoint. The only module that imports an LLM SDK."""

from __future__ import annotations

import json
import re
from typing import Any

from .config import get_settings

TEMPERATURE = 0.2
TIMEOUT_S = 60.0
RETRY_HINT = "Return only valid JSON."


class LLMUnavailable(Exception):
    """No API key configured, or the endpoint could not be reached."""


class LLMBadJSON(Exception):
    """The model did not return parseable JSON, even after one retry."""


_FENCE = re.compile(r"^\s*```[a-zA-Z0-9_-]*\s*\n?(.*?)\n?\s*```\s*$", re.DOTALL)


def strip_fences(text: str) -> str:
    """Remove a surrounding ``` / ```json fence, if any."""
    text = (text or "").strip()
    m = _FENCE.match(text)
    return m.group(1).strip() if m else text


def parse_json(text: str) -> dict:
    """Parse a JSON object out of a model reply (fences stripped; falls back to the outermost {...})."""
    cleaned = strip_fences(text)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise
        value = json.loads(cleaned[start : end + 1])
    if not isinstance(value, dict):
        raise json.JSONDecodeError("expected a JSON object", cleaned, 0)
    return value


class LLM:
    """`LLM()` uses current settings; pass api_key/base_url/model to override for one session/request."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None):
        s = get_settings()
        self.api_key = s.api_key if api_key is None else api_key
        self.base_url = base_url or s.base_url
        self.model = model or s.model
        self._client: Any = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    # -- transport -----------------------------------------------------------------------------
    def _get_client(self):
        if self._client is None:
            from openai import OpenAI  # imported lazily so the library works without a key

            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=TIMEOUT_S, max_retries=1)
        return self._client

    def _complete(self, messages: list[dict], json_mode: bool) -> str:
        """One chat completion. Overridden by fakes in tests."""
        import openai

        client = self._get_client()
        kwargs: dict[str, Any] = {"model": self.model, "messages": messages, "temperature": TEMPERATURE}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        try:
            resp = client.chat.completions.create(**kwargs)
        except openai.BadRequestError as exc:
            # Some OpenAI-compatible servers reject response_format; retry once without it.
            if json_mode and "response_format" in str(exc):
                kwargs.pop("response_format", None)
                resp = client.chat.completions.create(**kwargs)
            else:
                raise LLMUnavailable(f"LLM request rejected: {exc}") from exc
        except (openai.APIConnectionError, openai.AuthenticationError, openai.PermissionDeniedError,
                openai.NotFoundError, openai.RateLimitError, openai.APITimeoutError, openai.InternalServerError) as exc:
            raise LLMUnavailable(f"LLM endpoint error: {exc.__class__.__name__}: {exc}") from exc
        except openai.APIError as exc:
            raise LLMUnavailable(f"LLM endpoint error: {exc}") from exc
        if not getattr(resp, "choices", None):
            raise LLMUnavailable("LLM returned no choices")
        return resp.choices[0].message.content or ""

    # -- public API ----------------------------------------------------------------------------
    @staticmethod
    def _messages(system: str, user: str | None, messages: list[dict] | None) -> list[dict]:
        out = [{"role": "system", "content": system}]
        if messages:
            out.extend(messages)
        if user is not None:
            out.append({"role": "user", "content": user})
        if len(out) == 1:
            raise ValueError("ask() needs `user` or `messages`")
        return out

    def _safe_complete(self, messages: list[dict], json_mode: bool) -> str:
        """Run one completion; any provider/transport failure becomes LLMUnavailable so callers can fall back."""
        try:
            return self._complete(messages, json_mode)
        except LLMUnavailable:
            raise
        except Exception as exc:  # retry errors, malformed responses, SDK bugs
            raise LLMUnavailable(f"LLM call failed: {exc.__class__.__name__}: {exc}") from exc

    def ask(self, system: str, user: str | None = None, messages: list[dict] | None = None) -> str:
        if not self.available:
            raise LLMUnavailable("No LLM API key configured (set LLM_API_KEY).")
        return self._safe_complete(self._messages(system, user, messages), json_mode=False).strip()

    def ask_json(self, system: str, user: str | None = None, messages: list[dict] | None = None) -> dict:
        if not self.available:
            raise LLMUnavailable("No LLM API key configured (set LLM_API_KEY).")
        msgs = self._messages(system, user, messages)
        raw = self._safe_complete(msgs, json_mode=True)
        try:
            return parse_json(raw)
        except (json.JSONDecodeError, ValueError):
            pass
        retry = msgs + [{"role": "assistant", "content": raw}, {"role": "user", "content": RETRY_HINT}]
        raw2 = self._safe_complete(retry, json_mode=True)
        try:
            return parse_json(raw2)
        except (json.JSONDecodeError, ValueError) as exc:
            raise LLMBadJSON(f"Model returned invalid JSON twice: {raw2[:200]!r}") from exc
