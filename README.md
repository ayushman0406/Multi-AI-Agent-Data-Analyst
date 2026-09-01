# 🌟 Multi-AI-Agent Data Analyst
### Autonomous Enterprise Data Intelligence Website & Multi-Agent Platform

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react&logoColor=black)](https://reactjs.org)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.1+-FFF000?logo=duckdb&logoColor=black)](https://duckdb.org)
[![Plotly](https://img.shields.io/badge/Plotly-Interactive-3F4F75?logo=plotly&logoColor=white)](https://plotly.com)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic&logoColor=white)](https://pydantic.dev)

A luxury **Enterprise SaaS Product Website & Live Interactive Analytics Studio** powered by **6 specialized AI agents**, a zero-JVM **DuckDB + Pandas** columnar analytical engine, and a multi-provider LLM gateway (**Groq**, **OpenAI**, **Google Gemini**, **Ollama**, and **Offline Demo Mode**).

---

## ⚡ Key Highlights & Architecture Upgrades

1. **Enterprise SaaS Website ("Midnight Luxe" Aesthetic)**:
   - Complete product website with high-converting **Hero Section**, **6-Agent Deep Dive**, **DuckDB Engine Benchmarks**, **Interactive Live Studio**, **FAQ Accordion**, and **Luxury Footer**.
   - Styled with frosted glassmorphism (`backdrop-filter: blur`), obsidian surfaces (`#080C14`), electric cyan and emerald glow accents, and Google Fonts (*Outfit* and *Inter*).

2. **Zero-JVM High-Performance Engine (DuckDB + Pandas)**:
   - **50x Faster Profiling**: Sub-second startup latency (< 0.08s) replacing heavy PySpark JVM overhead.
   - **Zero Java Dependencies**: No JDK 8/11/17 installation or `JAVA_HOME` configuration needed.
   - Handles CSV, Parquet, JSON, and Excel directly in-memory with vectorized SQL querying.

3. **100% Type-Safe Pydantic Structured Outputs**:
   - Resolved legacy placeholder string bug where LLM text was discarded.
   - All 6 agents output strictly validated, typed Pydantic models containing real mathematical insights, semantic roles, and strategic recommendations.

4. **Multi-Provider LLM Gateway**:
   - Native support for **Groq** (Llama 3.3 70B), **OpenAI** (GPT-4o, GPT-4o-mini), **Google Gemini** (Gemini 2.0 Flash/Pro), and **Ollama** (offline local models).
   - Built-in **Intelligent Demo Mode** for testing all features without requiring an API key.

5. **Real-time DAG Execution Stepper (SSE Streaming)**:
   - Live visual workflow showing active agent execution, animated glowing telemetry nodes, execution timing, and error handling via Server-Sent Events (SSE).

6. **Interactive Plotly Visual Analytics**:
   - Dynamic bivariate scatter plots, correlation heatmaps, feature distribution histograms, and category breakdown charts with hover tooltips, zoom, and PNG downloads.

7. **In-App "Chat with Your Analyst Team" Assistant**:
   - Conversational AI drawer grounded directly in the ingested dataset's schema, statistics, and strategic recommendations.

8. **Multi-Format Boardroom Deliverables**:
   - 1-Click exports for **GitHub-Flavored Markdown** (.md), standalone **Styled HTML Executive Report** (.html), and raw **JSON State Bundle** (.json).

---

## 🤖 The 6-Agent Collective

| Agent | Purpose | Core Deliverables |
| :--- | :--- | :--- |
| **1. 📋 Dataset Description Agent** | Semantic data profiling & lineage | Domain classification, entity relationships, data dictionary, quality diagnostics |
| **2. 🔍 Domain Patterns Agent** | Correlation & anomaly discovery | Pairwise Pearson matrix, multivariate patterns with confidence scoring, anomaly alerts |
| **3. 📈 Interactive Visuals Agent** | Dynamic chart synthesis | Plotly heatmaps, distributions, scatter plots, and category breakdowns with business insights |
| **4. ⚙️ Custom Analysis Agent** | Rigorous statistical hypothesis testing | D'Agostino normality test, Welch's t-test, and target key driver ranking |
| **5. 🎯 Business Goals Agent** | Commercial KPI alignment | Strategic initiatives, monetization avenues, operational risk factors, priority action matrix |
| **6. 📊 Comprehensive Report Agent** | Executive boardroom synthesis | C-suite summary, strategic recommendations with ROI estimates, Markdown & HTML reports |

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9 or higher
- Node.js v18+ and npm

### 2. Launch the Platform (Single Command)

```bash
# Clone the repository
git clone <repo-url>
cd Multi-AI-Agent-Data-Analyst

# Run the unified launcher
./run.sh
```

The application will build the production frontend and start the platform at **`http://localhost:8000`** with interactive API docs at **`http://localhost:8000/docs`**.

### 3. Development Mode (Live Reloading)

To run the Vite dev server with Hot Module Replacement (HMR) and the FastAPI backend concurrently:

```bash
./run.sh --dev
```
- **Website (Vite Dev Server)**: `http://localhost:5173`
- **Backend API**: `http://localhost:8000`

---

## 🔧 Environment & Model Configuration

Create a `.env` file or use the in-app **Settings Modal** (gear icon in the top right navbar):

```bash
# Optional: Provide API keys for live LLM reasoning (or use Demo Mode / Ollama)
GROQ_API_KEY="gsk_..."
OPENAI_API_KEY="sk-..."
GEMINI_API_KEY="AIzaSy..."
```

---

## 🧪 Testing

Run the automated test suite covering the data engine, pipeline DAG, and backend endpoints:

```bash
.venv/bin/pytest tests/
```

---

## 📁 Repository Structure

```
Multi-AI-Agent-Data-Analyst/
├── backend/
│   ├── __init__.py
│   └── main.py                     # FastAPI backend (REST, SSE streaming, file upload, export)
├── engine/
│   ├── __init__.py
│   └── data_engine.py              # DuckDB + Pandas vectorized profiling & SQL engine
├── models/
│   ├── __init__.py
│   └── schemas.py                  # Pydantic models for structured agent outputs & AnalysisState
├── llm/
│   ├── __init__.py
│   └── llm_gateway.py              # Multi-provider gateway (Groq, OpenAI, Gemini, Ollama, Mock)
├── pipeline/
│   ├── __init__.py
│   └── orchestrator.py             # DAG pipeline coordinator with telemetry callbacks
│
# Specialized AI Agents
├── generate_dataset_description_agent.py
├── analyze_domain_specific_patterns_agent.py
├── generate_visualizations_agent.py
├── execute_custom_analysis_agent.py
├── define_business_goals_agent.py
├── generate_comprehensive_report_agent.py
│
# Enterprise SaaS Frontend (React + Vite)
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── website/            # HeroSection, AgentSuite, Benchmarks, Faq, Footer
│   │   │   ├── tabs/               # 6 Agent Studio inspection tabs
│   │   │   ├── Navbar.jsx
│   │   │   ├── DatasetUploader.jsx
│   │   │   ├── PipelineStepper.jsx
│   │   │   ├── AgentStudio.jsx
│   │   │   ├── DataChatDrawer.jsx
│   │   │   └── SettingsModal.jsx
│   │   ├── App.jsx
│   │   ├── index.css               # Midnight Luxe Design System tokens
│   │   └── main.jsx
│   ├── index.html
│   └── vite.config.js
│
├── sample_data/
│   └── heart_disease.csv           # Benchmark sample dataset
├── tests/
│   ├── conftest.py
│   ├── test_data_engine.py
│   ├── test_pipeline.py
│   └── test_backend_api.py
├── requirements.txt                # Python backend dependencies
└── run.sh                          # Unified execution launcher
```

---

## 📄 License
Apache-2.0. Built for modern enterprise data science and analytics teams.
