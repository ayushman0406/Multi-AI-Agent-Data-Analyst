"""Runtime settings. The only place model / provider defaults live."""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

try:  # optional: load a local .env if python-dotenv is installed
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
except Exception:  # pragma: no cover
    pass

DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "openai/gpt-oss-120b"

_overrides: dict[str, str] = {}
_lock = threading.Lock()


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str
    model: str
    max_rows: int = 200_000
    max_upload_mb: int = 25

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    @property
    def base_url_host(self) -> str:
        return urlparse(self.base_url).netloc or self.base_url

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "") or default)
    except ValueError:
        return default


def get_settings() -> Settings:
    """Read settings from the environment, then apply process-wide runtime overrides."""
    api_key = (
        os.environ.get("LLM_API_KEY")
        or os.environ.get("GROQ_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or ""
    )
    base_url = os.environ.get("LLM_BASE_URL") or DEFAULT_BASE_URL
    model = os.environ.get("LLM_MODEL") or DEFAULT_MODEL
    with _lock:
        ov = dict(_overrides)
    # The server's own key is only ever sent to the endpoint it was configured for.
    # If someone points the app at a different base URL without supplying a key,
    # run without a key rather than leak the server's key to that host.
    if "api_key" not in ov and ov.get("base_url"):
        if urlparse(ov["base_url"]).netloc != urlparse(base_url).netloc:
            api_key = ""
    return Settings(
        api_key=ov.get("api_key", api_key).strip(),
        base_url=(ov.get("base_url") or base_url).strip().rstrip("/"),
        model=(ov.get("model") or model).strip(),
        max_rows=_int_env("MAX_ROWS", 200_000),
        max_upload_mb=_int_env("MAX_UPLOAD_MB", 25),
    )


def set_overrides(api_key: str | None = None, base_url: str | None = None, model: str | None = None) -> None:
    """Runtime override for this process. None = leave unchanged, "" = clear the override."""
    with _lock:
        for key, value in (("api_key", api_key), ("base_url", base_url), ("model", model)):
            if value is None:
                continue
            if value == "":
                _overrides.pop(key, None)
            else:
                _overrides[key] = value


def clear_overrides() -> None:
    with _lock:
        _overrides.clear()
