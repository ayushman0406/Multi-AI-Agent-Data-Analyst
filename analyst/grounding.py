"""Grounding check: which numbers in a reply do not trace back to a computed tool result?"""

from __future__ import annotations

import math
import re
from typing import Any, Iterable

_CITATION = re.compile(r"\[\s*\d+(?:\s*[,–-]\s*\d+)*\s*\]")          # [1], [1, 2], [1-3]
_DATES = re.compile(r"\b\d{4}-\d{1,2}(?:-\d{1,2})?(?:[ T]\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?)?\b")
_NUMBER = re.compile(
    r"(?<![\w.])(?P<sign>[-−])?\$?(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+)"
    r"(?P<pct>\s?%)?(?:\s?(?P<suf>k|K|M|B|bn|million|billion|thousand)\b)?"
)
_SUFFIX = {"k": 1e3, "K": 1e3, "thousand": 1e3, "M": 1e6, "million": 1e6, "B": 1e9, "bn": 1e9, "billion": 1e9}


def numbers_in(text: str) -> list[float]:
    """Every number written in `text` (citations like [1] and ISO dates removed). '37%' -> 37.0."""
    if not text:
        return []
    text = _CITATION.sub(" ", str(text))
    text = _DATES.sub(" ", text)
    out = []
    for m in _NUMBER.finditer(text):
        try:
            v = float(m.group("num").replace(",", ""))
        except ValueError:
            continue
        if m.group("suf"):
            v *= _SUFFIX[m.group("suf")]
        if m.group("sign"):
            v = -v
        out.append(v)
    return out


def _sig2(x: float) -> float:
    if x == 0 or not math.isfinite(x):
        return 0.0
    return float(f"{x:.2g}")


def _walk(obj: Any) -> Iterable[float]:
    if isinstance(obj, bool) or obj is None:
        return
    if isinstance(obj, (int, float)):
        if isinstance(obj, float) and not math.isfinite(obj):
            return
        yield float(obj)
    elif isinstance(obj, str):
        yield from numbers_in(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk(v)
    elif isinstance(obj, (list, tuple, set)):
        for v in obj:
            yield from _walk(v)


def _ignorable(v: float) -> bool:
    if float(v).is_integer():
        a = abs(v)
        if a <= 10:
            return True
        if 1900 <= v <= 2100:
            return True
    return False


def _source_keys(sources: tuple) -> set[float]:
    keys: set[float] = set()
    for s in sources:
        for v in _walk(s):
            for cand in (v, v * 100, v / 100, abs(v), abs(v) * 100, abs(v) / 100):
                keys.add(_sig2(cand))
    return keys


def check(text: str, *sources: Any, question: str = "") -> dict:
    """Return {"ungrounded": [floats], "grounded_count": int, "total_numbers": int}."""
    keys = _source_keys(sources)
    asked = {_sig2(v) for v in numbers_in(question)}
    ungrounded: list[float] = []
    grounded = total = 0
    for v in numbers_in(text):
        if _ignorable(v) or _sig2(v) in asked:
            continue
        total += 1
        if _sig2(v) in keys or _sig2(abs(v)) in keys:
            grounded += 1
        elif v not in ungrounded:
            ungrounded.append(v)
    return {"ungrounded": ungrounded, "grounded_count": grounded, "total_numbers": total}


def ungrounded_numbers(text: str, *sources: Any, question: str = "") -> list[float]:
    """Numbers in `text` that match nothing in `sources` (2 significant figures, % <-> fraction)."""
    return check(text, *sources, question=question)["ungrounded"]
