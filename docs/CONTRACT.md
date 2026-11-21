# Build contract — backend ⇄ frontend

Single source of truth for the rebuild. Backend lives in `analyst/` (library) and `server/` (FastAPI).
Frontend lives in `web/` (React + Vite). Nothing else.

## Idea

You give it a dataset. It first **understands** it (profile → an LLM writes what the dataset is,
what each column means, quality issues, and 4–6 questions worth asking). Then it **answers questions**:
for every question (the initial goal, or any follow-up chat message) a planner LLM picks calls from a
fixed registry of safe analysis tools, DuckDB runs them, and an answer LLM writes a reply that only
uses the numbers the tools returned. A grounding check lists every number in the reply that does not
appear in the tool results. Follow-ups see the conversation history and previous results, so
"now split that by category" or "drop 2025 and redo it" works — that is how the analysis is modified.

No user-supplied code is ever executed. Model and provider are configurable (any OpenAI-compatible
endpoint); nothing hardcodes a model outside `analyst/config.py` defaults.

## Library (`analyst/`)

- `config.py` — `Settings` from env: `LLM_API_KEY` (falls back to `GROQ_API_KEY`, then `OPENAI_API_KEY`),
  `LLM_BASE_URL` (default `https://api.groq.com/openai/v1`), `LLM_MODEL` (default `openai/gpt-oss-120b`),
  `MAX_ROWS` (200000), `MAX_UPLOAD_MB` (25).
- `llm.py` — the only file importing an LLM SDK (`openai` package, OpenAI-compatible).
  `class LLMUnavailable(Exception)`, `class LLMBadJSON(Exception)`,
  `class LLM: ask(system, user|messages) -> str; ask_json(system, user|messages) -> dict`
  (json_object response format, strips code fences, one retry with "Return only valid JSON.", then LLMBadJSON).
  Temperature 0.2, timeout 60 s. Runtime overrides (api_key, base_url, model) per request/session.
- `data.py` — `Dataset` wrapping a DuckDB in-memory connection with table `data`; loads csv/tsv/parquet/json/xlsx.
  `profile() -> dict` (row_count, column_count, duplicate_rows, columns[{name,dtype,kind numeric|categorical|datetime|boolean|other,
  null_count, null_pct, distinct_count, min,max,mean,median,stddev (numeric), top_values[{value,count}] (categorical/boolean, top 5),
  histogram (numeric, 12 bins small)}], sample_rows (5)). JSON-safe. Aggregates in batched SQL, not per-column loops of queries.
- `tools.py` — `ToolError`; tools take `(ds, **args)` and return
  `{"tool","args","title","data":[row dicts],"chart":{"type":"bar"|"line"|"hist"|"scatter"|"heatmap"|"table","x","y","series"?},"summary":{small dict of headline numbers}}`.
  Registry (exact names): `group_aggregate(by, metric, agg=sum|mean|count|min|max|median, top=10, filters?)`,
  `time_trend(date_col, metric, agg, grain=day|week|month|quarter|year, filters?)`, `distribution(column, bins=20, filters?)`,
  `top_categories(column, top=10, filters?)`, `correlation(columns?)`, `outliers(column)` (IQR),
  `compare_groups(by, metric, filters?)` (count/mean/median/std per group), `crosstab(row, col, metric?, agg?)`,
  `scatter(x, y, color?, limit=500)`, `describe_column(column)`, `filter_rows(filters, columns?, limit=50)`.
  `filters` = list of `{"column","op": "=","!=",">",">=","<","<=","in","between","contains","value"}` — compiled to
  parameterised SQL, identifiers validated against the schema and quoted. Bad args → ToolError naming valid columns.
  Floats rounded to 4 dp. `TOOL_SPECS` (JSON-schema-ish list) is what the planner sees.
- `grounding.py` — `numbers_in(text)`, `ungrounded_numbers(text, *sources) -> list[float]`. Grounded if equal after rounding to
  2 significant figures (also accept percent ↔ fraction ×100) to any number anywhere in sources. Ignore 0–10 integers, years 1900–2100,
  and numbers inside the user's own question.
- `agents.py` — `understand(profile) -> {"title","domain","summary","column_notes":{col:str},"quality_notes":[str],"suggested_questions":[str]}`;
  `plan(profile, understanding, question, history) -> list[{"tool","args","why"}]` (≤5 steps, invalid tools/args dropped);
  `answer(question, understanding, results, history) -> {"answer_md", "key_numbers":[{"label","value","step"}], "follow_ups":[str]}`.
  Each has an offline fallback (no key): deterministic `understand` (no invented prose — say what was measured),
  keyword/heuristic `plan`, and `answer` that renders the tool summaries as a plain markdown table with a note "LLM not configured".
- `session.py` — `AnalysisSession` holding Dataset, profile, understanding, `turns: list[Turn]`; `Turn = {id, question, plan, results, answer_md,
  key_numbers, follow_ups, ungrounded, grounded_count, total_numbers, created_at, events}`. `ask(question, on_event)`.
  Events emitted in order: `plan` → `tool_start`/`tool_result` (per step, `{index, tool, args, ok, result|error, ms}`) → `answer` → `grounding` → `done`.

## HTTP API (`server/main.py`, FastAPI, all under `/api`)

- `GET  /api/health` → `{"ok":true,"llm":{"configured":bool,"model":str,"base_url_host":str}}`
- `GET  /api/samples` → `[{"id","name","description","rows","columns"}]` (from `samples/`)
- `POST /api/sessions` multipart `file` **or** form `sample_id` → `{"session_id","dataset":{"name","rows","columns"},"profile",...}`
  Rejects > MAX_UPLOAD_MB (413) and unknown types (415).
- `GET  /api/sessions/{id}/understand` → **SSE** stream: `event: profile` `{profile}`, `event: understanding` `{understanding}`, `event: done`.
- `POST /api/sessions/{id}/ask` JSON `{"question": str}` → **SSE** stream of the turn events above, each `event: <name>` + `data: <json>`.
  Final `done` carries the whole Turn.
- `GET  /api/sessions/{id}` → `{session_id, dataset, profile, understanding, turns}`
- `GET  /api/sessions/{id}/report.md` → markdown export of understanding + every turn (with grounding line).
- `PUT  /api/settings` JSON `{"api_key"?, "base_url"?, "model"?}` → session-less runtime override for this server process
  (key never echoed back). `GET /api/settings` → `{model, base_url, has_key}`.
- In production `server/main.py` serves `web/dist` as static files at `/` (SPA fallback to index.html).
- Sessions in memory, LRU of 20, temp files cleaned.

## Frontend (`web/`)

React 19 + Vite, plain CSS with tokens (no Tailwind needed), GSAP + Lenis for the landing page only.
Light theme, white/off-white background, one accent colour. Two surfaces:
1. `/` landing page — explains the idea with a real, live-looking trace (not generic feature cards).
2. `/app` workspace — choose sample / drop a file → watch "understanding" stream in → dataset brief
   (summary, column cards with mini histograms, quality notes, suggested questions as chips) → chat thread where each turn shows
   the plan as steps, each tool call expandable (args + result JSON + chart), the answer markdown, key numbers, grounding badge
   ("14 of 14 numbers trace to a computed result"; ungrounded ones highlighted), follow-up chips. Composer at the bottom.
   Export report (.md). Settings drawer for API key / base URL / model.
Charts rendered from the `chart` spec with hand-built SVG components (bar, line, hist, scatter, heatmap, table).
