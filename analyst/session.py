"""AnalysisSession: one dataset, its profile and brief, and a list of question/answer turns."""

from __future__ import annotations

import datetime as _dt
import time
import uuid
from typing import Any, Callable, TypedDict

from . import agents, grounding
from .data import Dataset, jsonable
from .llm import LLM
from .tools import ToolError, run_tool

EventFn = Callable[[str, dict], None]


class Turn(TypedDict):
    id: str
    question: str
    plan: list[dict]
    results: list[dict]
    answer_md: str
    key_numbers: list[dict]
    follow_ups: list[str]
    ungrounded: list[float]
    grounded_count: int
    total_numbers: int
    created_at: str
    events: list[dict]


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


class AnalysisSession:
    def __init__(self, dataset: Dataset, llm: LLM | None = None, session_id: str | None = None,
                 name: str | None = None):
        self.id = session_id or uuid.uuid4().hex[:12]
        self.dataset = dataset
        self.name = name or dataset.name
        self._llm = llm  # None -> a fresh LLM() from current settings on every call
        self.profile: dict = dataset.profile()
        self.profile["name"] = self.name
        self.understanding: dict | None = None
        self.turns: list[Turn] = []
        self.created_at = _now()

    # ------------------------------------------------------------------------------------------
    def llm(self) -> LLM:
        return self._llm if self._llm is not None else LLM()

    @property
    def dataset_info(self) -> dict:
        return {"name": self.name, "rows": self.profile["row_count"], "columns": self.profile["column_count"]}

    def understand(self, on_event: EventFn | None = None, refresh: bool = False) -> dict:
        emit = on_event or (lambda *_: None)
        emit("profile", {"profile": self.profile})
        if self.understanding is None or refresh:
            self.understanding = agents.understand(self.profile, self.llm())
        emit("understanding", {"understanding": self.understanding})
        return self.understanding

    # ------------------------------------------------------------------------------------------
    def ask(self, question: str, on_event: EventFn | None = None) -> Turn:
        question = (question or "").strip()
        if not question:
            raise ValueError("question is empty")
        t0 = time.perf_counter()
        log: list[dict] = []

        def emit(name: str, data: dict) -> None:
            data = jsonable(data)
            light = {"event": name, "ms": int((time.perf_counter() - t0) * 1000)}
            for k in ("index", "tool", "ok", "mode"):
                if k in data:
                    light[k] = data[k]
            log.append(light)
            if on_event:
                on_event(name, data)

        llm = self.llm()
        if self.understanding is None:
            self.understanding = agents.understand(self.profile, llm)
        history = list(self.turns)

        planned = agents.plan_detailed(self.profile, self.understanding, question, history, llm)
        steps = planned["steps"]
        emit("plan", {"steps": steps, "mode": planned["mode"], "dropped": planned.get("dropped", []),
                      "note": planned.get("note")})

        results: list[dict] = []
        for i, step in enumerate(steps):
            emit("tool_start", {"index": i, "tool": step["tool"], "args": step["args"]})
            s0 = time.perf_counter()
            entry: dict[str, Any] = {"index": i, "tool": step["tool"], "args": step["args"]}
            try:
                res = run_tool(self.dataset, step["tool"], step["args"])
                entry.update(ok=True, result=res)
            except ToolError as exc:
                entry.update(ok=False, error=str(exc))
            except Exception as exc:  # a tool bug must not kill the turn
                entry.update(ok=False, error=f"{exc.__class__.__name__}: {exc}")
            entry["ms"] = int((time.perf_counter() - s0) * 1000)
            results.append(entry)
            emit("tool_result", entry)

        ans = agents.answer(question, self.understanding, results, history, llm)
        emit("answer", ans)

        sources = [r.get("result") for r in results if r.get("ok")]
        g = grounding.check(ans["answer_md"], *sources, question=question)
        emit("grounding", g)

        turn: Turn = {
            "id": uuid.uuid4().hex[:10],
            "question": question,
            "plan": steps,
            "results": results,
            "answer_md": ans["answer_md"],
            "key_numbers": ans.get("key_numbers", []),
            "follow_ups": ans.get("follow_ups", []),
            "ungrounded": g["ungrounded"],
            "grounded_count": g["grounded_count"],
            "total_numbers": g["total_numbers"],
            "created_at": _now(),
            "events": log,
        }
        turn["mode"] = ans.get("mode", "offline")  # type: ignore[typeddict-unknown-key]
        log.append({"event": "done", "ms": int((time.perf_counter() - t0) * 1000)})
        turn = jsonable(turn)
        self.turns.append(turn)
        if on_event:
            on_event("done", {"turn": turn})
        return turn

    # ------------------------------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {"session_id": self.id, "dataset": self.dataset_info, "profile": self.profile,
                "understanding": self.understanding, "turns": self.turns, "created_at": self.created_at}

    def report_md(self) -> str:
        u = self.understanding or {}
        p = self.profile
        out = [f"# {u.get('title') or self.name}", "",
               f"_Dataset: {self.name} - {p['row_count']} rows x {p['column_count']} columns. Generated {_now()}._", ""]
        if u:
            out += ["## Dataset brief", "", u.get("summary", ""), ""]
            if u.get("column_notes"):
                out += ["### Columns", ""] + [f"- **{c}**: {n}" for c, n in u["column_notes"].items()] + [""]
            if u.get("quality_notes"):
                out += ["### Data quality", ""] + [f"- {n}" for n in u["quality_notes"]] + [""]
        for i, t in enumerate(self.turns, start=1):
            out += [f"## {i}. {t['question']}", "", t["answer_md"], ""]
            if t.get("key_numbers"):
                out += ["**Key numbers**", ""]
                out += [f"- {k.get('label')}: {k.get('value')}" + (f" [{k['step']}]" if k.get("step") else "")
                        for k in t["key_numbers"]] + [""]
            out += ["**Steps**", ""]
            for j, r in enumerate(t["results"], start=1):
                status = r["result"]["title"] if r.get("ok") else f"failed: {r.get('error')}"
                out.append(f"{j}. `{r['tool']}` - {status}")
            out.append("")
            line = f"_Grounding: {t['grounded_count']} of {t['total_numbers']} numbers trace to a computed result"
            if t["ungrounded"]:
                line += "; not found in results: " + ", ".join(f"{v:g}" for v in t["ungrounded"])
            out += [line + "._", ""]
        return "\n".join(out).rstrip() + "\n"

    def close(self) -> None:
        self.dataset.close()
