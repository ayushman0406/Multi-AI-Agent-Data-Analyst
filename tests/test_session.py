import json

from analyst import agents
from analyst.session import AnalysisSession
from conftest import FakeLLM, role_of

UNDERSTANDING = {"title": "Tiny sales", "domain": "sales", "summary": "Five rows of unit sales.",
                 "column_notes": {"region": "Sales region."}, "quality_notes": [],
                 "suggested_questions": ["Units by region?"]}

GOOD_STEP = {"tool": "group_aggregate", "args": {"by": "region", "metric": "units", "agg": "sum"},
             "why": "units per region"}


def make_llm(plan_steps, answer=None):
    def respond(system, user, messages):
        role = role_of(system)
        if role == "plan":
            return {"steps": plan_steps}
        if role == "answer":
            return answer or {"answer_md": "South sold the most units: 12 [1].",
                              "key_numbers": [{"label": "South units", "value": 12, "step": 1}],
                              "follow_ups": ["Same but by date", "Exclude N"]}
        return UNDERSTANDING
    return FakeLLM(respond)


def test_event_order_and_turn_shape(tiny_ds):
    llm = make_llm([GOOD_STEP])
    s = AnalysisSession(tiny_ds, llm=llm)
    events = []
    turn = s.ask("Which region sells the most units?", lambda n, d: events.append(n))
    assert events == ["plan", "tool_start", "tool_result", "answer", "grounding", "done"]
    for key in ("id", "question", "plan", "results", "answer_md", "key_numbers", "follow_ups", "ungrounded",
                "grounded_count", "total_numbers", "created_at", "events"):
        assert key in turn
    assert turn["ungrounded"] == [] and turn["grounded_count"] == 1
    json.dumps(turn)


def test_tool_results_reach_answer_prompt(tiny_ds):
    llm = make_llm([GOOD_STEP])
    AnalysisSession(tiny_ds, llm=llm).ask("Which region sells the most units?")
    answer_prompts = llm.prompts_for("answer")
    assert len(answer_prompts) == 1
    assert "12" in answer_prompts[0] and '"top_group":"S"' in answer_prompts[0]


def test_invalid_plan_steps_dropped(tiny_ds):
    steps = [{"tool": "rm_rf", "args": {"path": "/"}}, {"tool": "group_aggregate", "args": {"by": "nope"}},
             "garbage", GOOD_STEP]
    events = {}
    turn = AnalysisSession(tiny_ds, llm=make_llm(steps)).ask("units by region",
                                                            lambda n, d: events.setdefault(n, d))
    assert [p["tool"] for p in turn["plan"]] == ["group_aggregate"]
    assert len(events["plan"]["dropped"]) == 3


def test_zero_valid_steps_falls_back_to_heuristic(tiny_ds):
    turn = AnalysisSession(tiny_ds, llm=make_llm([{"tool": "rm_rf"}])).ask("units by region")
    assert turn["plan"] and turn["plan"][0]["tool"] == "group_aggregate"


def test_tool_error_recorded_and_run_continues(tiny_ds):
    bad = {"tool": "filter_rows", "args": {"filters": [{"column": "units", "op": ">", "value": "lots"}]}}
    turn = AnalysisSession(tiny_ds, llm=make_llm([bad, GOOD_STEP])).ask("units by region")
    assert [r["ok"] for r in turn["results"]] == [False, True]
    assert turn["results"][0]["error"]
    assert turn["answer_md"]


def test_offline_plan_and_table_answer(tiny_ds):
    s = AnalysisSession(tiny_ds)  # no key in env -> offline
    u = s.understand()
    assert u["mode"] == "offline" and "LLM not configured" in u["summary"]
    turn = s.ask("total units by region")
    assert turn["plan"][0]["tool"] == "group_aggregate"
    assert turn["plan"][0]["args"]["by"] == "region"
    lines = [l for l in turn["answer_md"].splitlines() if l.strip()]
    assert "LLM not configured" in lines[0]
    assert all(l.startswith("|") for l in lines[1:])  # only a table, no invented prose
    assert turn["ungrounded"] == []


def test_followup_planner_sees_previous_turn(tiny_ds):
    llm = make_llm([GOOD_STEP])
    s = AnalysisSession(tiny_ds, llm=llm)
    s.ask("Which region sells the most units?")
    s.ask("Same but only for N")
    prompts = llm.prompts_for("plan")
    assert len(prompts) == 2
    assert "Which region sells the most units?" in prompts[1]
    assert "group_aggregate" in prompts[1]


def test_llm_failure_falls_back(tiny_ds):
    from analyst.llm import LLMUnavailable

    def boom(system, user, messages):
        raise LLMUnavailable("down")
    turn = AnalysisSession(tiny_ds, llm=FakeLLM(boom)).ask("units by region")
    assert turn["plan"] and "LLM call failed" in turn["answer_md"]


def test_heuristic_planner_keywords(tiny_ds):
    p = tiny_ds.profile()
    tools = lambda q: [s["tool"] for s in agents.heuristic_plan(p, q)]  # noqa: E731
    assert "time_trend" in tools("units trend over time")
    assert "correlation" in tools("are units and price correlated?")
    assert "outliers" in tools("any outliers in units?")
    assert "distribution" in tools("distribution of price")
    assert "compare_groups" in tools("compare price across region")
    plan = agents.heuristic_plan(p, "units by regoin")
    assert plan[0]["args"]["by"] == "region"


def test_heuristic_followup_modifies_previous_plan(tiny_ds):
    s = AnalysisSession(tiny_ds)
    s.ask("total units by region")
    turn = s.ask("exclude N")
    step = turn["plan"][0]
    assert step["tool"] == "group_aggregate"
    assert {"column": "region", "op": "!=", "value": "N"} in step["args"]["filters"]
    turn = s.ask("same but by day")
    assert any(st["tool"] == "time_trend" and st["args"]["grain"] == "day" for st in turn["plan"])


def test_report_md(tiny_ds):
    s = AnalysisSession(tiny_ds, llm=make_llm([GOOD_STEP]))
    s.understand()
    s.ask("Which region sells the most units?")
    md = s.report_md()
    assert "Tiny sales" in md and "Which region sells the most units?" in md and "Grounding:" in md
