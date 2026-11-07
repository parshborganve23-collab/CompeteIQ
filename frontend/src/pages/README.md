# CompeteIQ — NEXORA AI

**AI-Powered Competitive Intelligence Platform**

CompeteIQ helps businesses monitor competitors, analyze market developments, remember historical events, and generate strategic recommendations using AI agents.

## Core Integrations

### 1. BAND AI — Multi-Agent Collaboration

BAND AI coordinates seven specialized agents:

- Research Agent
- Product Intelligence Agent
- Market Intelligence Agent
- Financial Intelligence Agent
- Historical Intelligence Agent
- Risk Analysis Agent
- Strategy Agent

### 2. Hindsight — Long-Term AI Memory

Hindsight supports:

- **Retain:** Store historical competitor intelligence.
- **Recall:** Retrieve relevant past information.
- **Reflect:** Generate insights using stored memories.

## Technology Stack

- Frontend: React and Vite
- Backend: Python and FastAPI
- AI Model: Ollama
- Multi-Agent Platform: BAND AI
- Memory Platform: Hindsight
- Database: SQLAlchemy

## Company and Product

- Company: NEXORA AI
- Platform: CompeteIQ
- Demo competitor: MINTY-GPT (simulated only)

## Run Locally

Backend:

```powershell
cd backend
.\venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm.cmd run dev
```

BAND worker:

```powershell
cd backend
.\venv\Scripts\python.exe band_worker.py
```

See the `docs` folder for setup and integration documentation.

**Security:** Never publish `.env` files, API keys, database files, or credentials.