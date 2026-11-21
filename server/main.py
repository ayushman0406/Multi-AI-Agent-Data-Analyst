"""HTTP API. Run: uvicorn server.main:app --port 8000"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, StreamingResponse
from pydantic import BaseModel

from analyst.config import get_settings, set_overrides
from analyst.data import SUPPORTED_EXTENSIONS, Dataset, jsonable
from analyst.session import AnalysisSession

ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = ROOT / "samples"
WEB_DIST = ROOT / "web" / "dist"
MAX_SESSIONS = 20

app = FastAPI(title="Grounded data analyst", version="2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------------------------
# in-memory session store (LRU)
# ---------------------------------------------------------------------------------------------
class SessionStore:
    def __init__(self, limit: int = MAX_SESSIONS):
        self.limit = limit
        self._items: OrderedDict[str, AnalysisSession] = OrderedDict()
        self._lock = threading.Lock()

    def add(self, s: AnalysisSession) -> None:
        with self._lock:
            self._items[s.id] = s
            self._items.move_to_end(s.id)
            while len(self._items) > self.limit:
                _, old = self._items.popitem(last=False)
                old.close()

    def get(self, sid: str) -> AnalysisSession:
        with self._lock:
            s = self._items.get(sid)
            if s is None:
                raise HTTPException(404, f"Unknown session '{sid}'")
            self._items.move_to_end(sid)
            return s

    def clear(self) -> None:
        with self._lock:
            for s in self._items.values():
                s.close()
            self._items.clear()


sessions = SessionStore()


# ---------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------
def _load_samples() -> list[dict]:
    path = SAMPLES_DIR / "samples.json"
    if not path.exists():
        return []
    items = json.loads(path.read_text())
    return [s for s in items if (SAMPLES_DIR / s["file"]).exists()]


_sample_shapes: dict[str, tuple[int, int]] = {}


def _sample_shape(sample: dict) -> tuple[int, int]:
    key = sample["id"]
    if key not in _sample_shapes:
        import duckdb

        con = duckdb.connect()
        try:
            src = str(SAMPLES_DIR / sample["file"])
            rows = con.execute("SELECT COUNT(*) FROM read_csv_auto(?)", [src]).fetchone()[0]
            cols = len(con.execute("DESCRIBE SELECT * FROM read_csv_auto(?)", [src]).fetchall())
        finally:
            con.close()
        _sample_shapes[key] = (rows, cols)
    return _sample_shapes[key]


def _sse(name: str, data: Any) -> bytes:
    return f"event: {name}\ndata: {json.dumps(jsonable(data), ensure_ascii=False)}\n\n".encode()


def sse_response(work: Callable[[Callable[[str, dict], None]], Any]) -> StreamingResponse:
    """Run blocking `work(emit)` in a thread; stream each emitted event to the client as it happens."""

    async def gen():
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()
        done = object()

        def emit(name: str, data: dict) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, (name, data))

        def run() -> None:
            try:
                work(emit)
            except Exception as exc:  # surfaced to the client as an SSE error event
                emit("error", {"message": f"{exc.__class__.__name__}: {exc}"})
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, done)

        task = loop.run_in_executor(None, run)
        try:
            while True:
                item = await queue.get()
                if item is done:
                    break
                yield _sse(*item)
        finally:
            await task

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"})


def _session_payload(s: AnalysisSession) -> dict:
    return jsonable(s.to_dict())


# ---------------------------------------------------------------------------------------------
# routes
# ---------------------------------------------------------------------------------------------
@app.get("/api/health")
def health() -> dict:
    s = get_settings()
    return {"ok": True, "llm": {"configured": s.configured, "model": s.model, "base_url_host": s.base_url_host}}


@app.get("/api/samples")
def samples() -> list[dict]:
    out = []
    for smp in _load_samples():
        rows, cols = _sample_shape(smp)
        out.append({"id": smp["id"], "name": smp["name"], "description": smp["description"],
                    "source": smp.get("source", ""), "rows": rows, "columns": cols})
    return out


@app.get("/api/demo")
def demo() -> JSONResponse:
    path = SAMPLES_DIR / "retail_orders.cached.json"
    if not path.exists():
        raise HTTPException(404, "No cached demo session")
    return JSONResponse(json.loads(path.read_text()))


@app.post("/api/sessions")
async def create_session(request: Request, file: UploadFile | None = File(None),
                         sample_id: str | None = Form(None)) -> dict:
    settings = get_settings()
    limit = settings.max_upload_bytes
    if file is not None and file.filename:
        clen = request.headers.get("content-length")
        if clen and clen.isdigit() and int(clen) > limit + 1024 * 1024:
            raise HTTPException(413, f"File too large (max {settings.max_upload_mb} MB)")
        ext = Path(file.filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(415, f"Unsupported file type '{ext or file.filename}'. "
                                     f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
        fd, tmp = tempfile.mkstemp(suffix=ext, prefix="analyst_upload_")
        try:
            size = 0
            with os.fdopen(fd, "wb") as out:
                while chunk := await file.read(1024 * 1024):
                    size += len(chunk)
                    if size > limit:
                        raise HTTPException(413, f"File too large (max {settings.max_upload_mb} MB)")
                    out.write(chunk)
            if size == 0:
                raise HTTPException(400, "Uploaded file is empty")
            name = Path(file.filename).stem
            try:
                ds = await asyncio.to_thread(Dataset.from_path, tmp, name)
            except Exception as exc:
                raise HTTPException(400, f"Could not read file: {str(exc).splitlines()[0]}")
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass
    elif sample_id:
        smp = next((s for s in _load_samples() if s["id"] == sample_id), None)
        if smp is None:
            raise HTTPException(404, f"Unknown sample '{sample_id}'")
        ds = await asyncio.to_thread(Dataset.from_path, SAMPLES_DIR / smp["file"], smp["name"])
        name = smp["name"]
    else:
        raise HTTPException(400, "Send a multipart 'file' or a form field 'sample_id'")
    if ds.row_count == 0 or not ds.columns:
        ds.close()
        raise HTTPException(400, "The file has no rows")
    session = await asyncio.to_thread(AnalysisSession, ds, None, None, name)
    sessions.add(session)
    return _session_payload(session)


@app.get("/api/sessions/{sid}")
def get_session(sid: str) -> dict:
    return _session_payload(sessions.get(sid))


@app.get("/api/sessions/{sid}/understand")
def understand(sid: str, refresh: bool = False) -> StreamingResponse:
    s = sessions.get(sid)

    def work(emit):
        u = s.understand(emit, refresh=refresh)
        emit("done", {"understanding": u})

    return sse_response(work)


class AskBody(BaseModel):
    question: str


@app.post("/api/sessions/{sid}/ask")
def ask(sid: str, body: AskBody) -> StreamingResponse:
    s = sessions.get(sid)
    q = (body.question or "").strip()
    if not q:
        raise HTTPException(400, "question is empty")
    if len(q) > 2000:
        raise HTTPException(400, "question is too long (max 2000 characters)")
    return sse_response(lambda emit: s.ask(q, emit))


@app.get("/api/sessions/{sid}/report.md")
def report(sid: str) -> PlainTextResponse:
    s = sessions.get(sid)
    fname = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in s.name)[:60] or "report"
    return PlainTextResponse(s.report_md(), media_type="text/markdown; charset=utf-8",
                             headers={"Content-Disposition": f'attachment; filename="{fname}-report.md"'})


class SettingsBody(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None


def _settings_view() -> dict:
    s = get_settings()
    return {"model": s.model, "base_url": s.base_url, "has_key": s.configured}


@app.get("/api/settings")
def read_settings() -> dict:
    return _settings_view()


@app.put("/api/settings")
def write_settings(body: SettingsBody) -> dict:
    if body.base_url and not body.base_url.startswith(("http://", "https://")):
        raise HTTPException(400, "base_url must start with http:// or https://")
    set_overrides(api_key=body.api_key, base_url=body.base_url, model=body.model)
    return _settings_view()


@app.api_route("/api/{rest:path}", methods=["GET", "POST", "PUT", "DELETE"])
def api_not_found(rest: str):
    raise HTTPException(404, f"Unknown API route /api/{rest}")


# ---------------------------------------------------------------------------------------------
# static frontend (web/dist) with SPA fallback
# ---------------------------------------------------------------------------------------------
@app.get("/{full_path:path}", include_in_schema=False)
def spa(full_path: str):
    index = WEB_DIST / "index.html"
    if not index.exists():
        return JSONResponse({"detail": "Frontend not built. Run `npm run build` in web/, or use the Vite dev server."},
                            status_code=404)
    if full_path:
        candidate = (WEB_DIST / full_path).resolve()
        if candidate.is_file() and WEB_DIST.resolve() in candidate.parents:
            return FileResponse(candidate)
    return FileResponse(index)
