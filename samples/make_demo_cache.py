"""Build samples/retail_orders.cached.json: a full session (brief + one turn) served by GET /api/demo.

Uses the configured LLM if a key is set, otherwise the offline fallbacks (marked "mode": "offline").
Run: python samples/make_demo_cache.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analyst import AnalysisSession, Dataset  # noqa: E402
from analyst.config import get_settings  # noqa: E402

QUESTION = "Where are we losing margin?"
OUT = ROOT / "samples" / "retail_orders.cached.json"


def main() -> None:
    settings = get_settings()
    ds = Dataset.from_path(ROOT / "samples" / "retail_orders.csv", "Retail orders")
    session = AnalysisSession(ds, session_id="demo", name="Retail orders")
    events: list[dict] = []
    session.understand(lambda n, d: events.append({"event": n}))
    session.ask(QUESTION)
    payload = session.to_dict()
    payload["mode"] = "llm" if settings.configured and session.turns[-1].get("mode") == "llm" else "offline"
    payload["model"] = settings.model if payload["mode"] == "llm" else None
    payload["sample_id"] = "retail_orders"
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n")
    print(f"wrote {OUT} (mode={payload['mode']}, {OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
