"""
FastAPI Application Backend
Serves REST and SSE endpoints for the Multi-AI-Agent Data Analyst system.
"""

import os
import sys
import json
import shutil
import tempfile
import asyncio
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, PlainTextResponse, HTMLResponse
from pydantic import BaseModel

# Add workspace root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.orchestrator import AnalysisPipeline, AGENT_STAGES
from models.schemas import AnalysisState

app = FastAPI(
    title="Multi-AI-Agent Data Analyst API",
    description="Backend API supporting high-performance data profiling, multi-agent analytics, and SSE streaming.",
    version="2.0.0"
)

# Enable CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store
class SessionStore:
    def __init__(self):
        self.pipeline: Optional[AnalysisPipeline] = None
        self.current_state: Optional[AnalysisState] = None
        self.event_subscribers: List[asyncio.Queue] = []
        self.provider: str = "mock"
        self.model: Optional[str] = None
        self.api_key: Optional[str] = None
        self.temp_dir: str = tempfile.mkdtemp(prefix="ai_analyst_")

    def broadcast_event(self, event: Dict[str, Any]):
        for q in list(self.event_subscribers):
            try:
                q.put_nowait(event)
            except Exception:
                self.event_subscribers.remove(q)

session = SessionStore()


# ==========================================
# Pydantic Request Models
# ==========================================
class ConfigRequest(BaseModel):
    provider: str
    model: Optional[str] = None
    api_key: Optional[str] = None


class ChatRequest(BaseModel):
    message: str


# ==========================================
# Endpoints
# ==========================================
@app.get("/api/health")
def get_health():
    """Returns system status and active LLM configuration."""
    available_keys = {
        "groq": bool(os.getenv("GROQ_API_KEY") or (session.provider == "groq" and session.api_key)),
        "openai": bool(os.getenv("OPENAI_API_KEY") or (session.provider == "openai" and session.api_key)),
        "gemini": bool(os.getenv("GEMINI_API_KEY") or (session.provider == "gemini" and session.api_key)),
        "ollama": True
    }
    return {
        "status": "healthy",
        "active_provider": session.provider,
        "active_model": session.model or "default",
        "has_dataset": session.pipeline is not None,
        "available_keys": available_keys,
        "agent_stages": AGENT_STAGES
    }


@app.post("/api/config")
def set_config(req: ConfigRequest):
    """Updates provider and API key settings."""
    session.provider = req.provider.lower()
    session.model = req.model
    session.api_key = req.api_key
    if req.api_key:
        if session.provider == "groq":
            os.environ["GROQ_API_KEY"] = req.api_key
        elif session.provider == "openai":
            os.environ["OPENAI_API_KEY"] = req.api_key
        elif session.provider == "gemini":
            os.environ["GEMINI_API_KEY"] = req.api_key
            
    return {"message": f"Provider updated to {session.provider}", "model": session.model}


@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Uploads CSV, Parquet, or Excel file and returns quick preview."""
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".csv", ".parquet", ".pq", ".xlsx", ".xls", ".json"]:
        raise HTTPException(status_code=400, detail="Unsupported format. Upload CSV, Parquet, JSON, or Excel.")

    dest_path = os.path.join(session.temp_dir, file.filename)
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        session.pipeline = AnalysisPipeline(
            data_source=dest_path,
            provider=session.provider,
            model=session.model,
            api_key=session.api_key
        )
        session.current_state = session.pipeline.state
        
        return {
            "success": True,
            "filename": file.filename,
            "total_rows": session.current_state.total_rows,
            "total_columns": session.current_state.total_columns,
            "columns": session.current_state.column_names,
            "preview": session.current_state.quick_preview
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse dataset: {str(e)}")


@app.get("/api/sample")
def load_sample_dataset():
    """Loads the pre-packaged sample dataset for instant testing."""
    sample_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_data", "heart_disease.csv")
    if not os.path.exists(sample_path):
        raise HTTPException(status_code=404, detail="Sample dataset not found.")

    try:
        session.pipeline = AnalysisPipeline(
            data_source=sample_path,
            provider=session.provider,
            model=session.model,
            api_key=session.api_key
        )
        session.current_state = session.pipeline.state
        
        return {
            "success": True,
            "filename": "heart_disease.csv",
            "total_rows": session.current_state.total_rows,
            "total_columns": session.current_state.total_columns,
            "columns": session.current_state.column_names,
            "preview": session.current_state.quick_preview
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load sample dataset: {str(e)}")


@app.get("/api/pipeline/stream")
async def stream_pipeline_events():
    """SSE endpoint streaming live agent execution events."""
    q: asyncio.Queue = asyncio.Queue()
    session.event_subscribers.append(q)

    async def event_generator():
        try:
            while True:
                data = await q.get()
                yield f"data: {json.dumps(data)}\n\n"
        except asyncio.CancelledError:
            if q in session.event_subscribers:
                session.event_subscribers.remove(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/pipeline/run")
async def run_pipeline(background_tasks: BackgroundTasks):
    """Triggers the full DAG multi-agent pipeline."""
    if not session.pipeline:
        raise HTTPException(status_code=400, detail="No dataset uploaded yet.")

    def run_job():
        def progress_cb(event):
            session.broadcast_event(event)

        session.current_state = session.pipeline.run_full_pipeline(progress_callback=progress_cb)

    background_tasks.add_task(run_job)
    return {"message": "Pipeline execution started in background", "stages": AGENT_STAGES}


@app.get("/api/state")
def get_current_state():
    """Returns the full unified AnalysisState."""
    if not session.current_state:
        raise HTTPException(status_code=404, detail="No active analysis state.")
    return session.current_state.model_dump()


@app.post("/api/chat")
def chat_with_analyst(req: ChatRequest):
    """Contextual conversational response grounded in the dataset and agent findings."""
    if not session.pipeline:
        raise HTTPException(status_code=400, detail="Please upload a dataset first.")
    
    reply = session.pipeline.chat_with_data(req.message)
    return {"reply": reply}


@app.get("/api/export/{fmt}")
def export_report(fmt: str):
    """Exports comprehensive report in markdown, HTML, or raw JSON."""
    if not session.current_state or not session.current_state.comprehensive_report:
        raise HTTPException(status_code=400, detail="Analysis report has not been generated yet.")

    report = session.current_state.comprehensive_report
    if fmt.lower() == "markdown":
        return PlainTextResponse(
            report.full_markdown_report,
            headers={"Content-Disposition": f'attachment; filename="{session.current_state.dataset_name}_report.md"'}
        )
    elif fmt.lower() == "html":
        return HTMLResponse(
            report.styled_html_report or report.full_markdown_report,
            headers={"Content-Disposition": f'attachment; filename="{session.current_state.dataset_name}_report.html"'}
        )
    elif fmt.lower() == "json":
        return PlainTextResponse(
            session.current_state.model_dump_json(indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{session.current_state.dataset_name}_analysis.json"'}
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Choose 'markdown', 'html', or 'json'.")


# Mount production frontend build if present
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.exists(frontend_dist):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

