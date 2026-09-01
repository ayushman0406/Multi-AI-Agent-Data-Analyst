#!/usr/bin/env bash
# ==============================================================================
# Multi-AI-Agent Data Analyst Platform Launcher
# Boots the FastAPI backend and Midnight Luxe Enterprise Website
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

export PYTHONPATH="$SCRIPT_DIR"

if [ "$1" == "--dev" ]; then
    echo "🚀 Launching in Development Mode (Vite Dev Server + FastAPI)..."
    # Start backend
    .venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!

    # Start frontend
    cd frontend && npm run dev &
    FRONTEND_PID=$!

    trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
    echo "✅ Platform running:"
    echo "   - Website: http://localhost:5173"
    echo "   - API Documentation: http://localhost:8000/docs"
    wait
else
    # Build frontend if not built
    if [ ! -d "frontend/dist" ]; then
        echo "📦 Building production frontend assets..."
        cd frontend && npm run build && cd ..
    fi

    echo "🌟 Launching Multi-Agent Data Analyst Enterprise Website..."
    echo "   - Website & API: http://localhost:8000"
    echo "   - Interactive API Docs: http://localhost:8000/docs"
    .venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
fi
