# RAMA AI OS v5.0

> Recursive Autonomous Multifunctional Assistant — a JARVIS-level AI OS

---

## Quick Start (3 commands)

```bash
# 1. Copy env and add your API key
cp .env.example .env
# edit .env and paste your GEMINI_API_KEY

# 2. Setup everything
./setup.sh          # Linux / Mac
setup.bat           # Windows

# 3. Start RAMA
./start.sh          # Linux / Mac
start.bat           # Windows
```

Open **http://localhost:8080** — RAMA is live.

---

## Prerequisites

| Tool | Required | Install |
|------|----------|---------|
| Python 3.11+ | ✅ Yes | https://python.org |
| Node.js 20+ | ✅ Yes | https://nodejs.org |
| Ollama | Recommended | https://ollama.com |
| Docker | Optional | https://docker.com |

---

## Ollama Models (Local LLMs)

```bash
ollama pull llama3          # Main orchestrator / persona
ollama pull phi3            # Fast intent routing (~100ms)
ollama pull qwen2.5-coder   # Code generation
ollama pull llava           # Vision / screen analysis
```

No Ollama? RAMA automatically falls back to **Gemini cloud**.

---

## Architecture

```
RAMA-AI/
├── backend/
│   ├── orchestrator/
│   │   ├── main.py          ← FastAPI entry point
│   │   └── swarm_router.py  ← Multi-LLM routing brain
│   ├── core/
│   │   └── prompts.py       ← System prompts per model
│   ├── memory/
│   │   └── learning_engine.py  ← FAISS vector memory
│   ├── security/
│   │   └── sentinel.py      ← Network port monitor
│   ├── intelligence/
│   │   └── emotion_engine.py   ← User mood detection
│   └── data/                ← Persistent storage (memory, skills)
├── frontend/
│   └── src/                 ← React + Three.js JARVIS HUD
├── docker-compose.yml
├── setup.sh / setup.bat
└── start.sh / start.bat
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Main chat — routes to best model |
| POST | `/api/reason` | Deep reasoning via Gemini Pro |
| POST | `/api/files` | Batch file read/write/list |
| GET  | `/api/security/status` | Sentinel threat status |
| GET  | `/api/memory` | FAISS memory contents |
| POST | `/api/skills/learn` | Learn from GitHub repo |
| POST | `/api/reflect` | RAMA self-analyses its own code |
| GET  | `/api/tools` | List all available tools |
| GET  | `/health` | Service health check |

Interactive docs: **http://localhost:3500/docs**

---

## Wake Words

Say or type **RAMA**, **Buddy**, or **Boss** to activate CEO mode.

**CEO Fast-Build syntax:**
```
RAMA, [Task] - High Efficiency Mode. Deploy Agents.
```

---

## Features

### Core Intelligence
- **SwarmRouter** — routes each task to the best model (phi3 → qwen → llava → llama3)
- **FAISS Memory** — vector-indexed memory of past interactions
- **EmotionEngine** — detects your mood, adjusts RAMA's tone
- **CEO Architect** — 3-tier agent hierarchy (CEO → Managers → Sub-agents)

### Security
- **NetworkSentinel** — scans ports every 10s, alerts on suspicious activity
- **Trivy integration** — container and IaC security scanning
- **Aegis defense** — DDoS protection and IP tracing

### Autonomous Capabilities
- **Ghost Coder** — watches your repo, fixes issues at night, opens PRs
- **Viral Empire** — trend scraping → video generation → auto-upload
- **API Bounty Hunter** — finds freelance gigs, writes scripts, auto-bids
- **Oracle SaaS Engine** — detects viral trends, builds and launches products

### Infrastructure
- **Phantom Infrastructure** — generates missing API endpoints on-the-fly
- **Chronos Debugger** — time-travel debugging with memory snapshots
- **Genesis Protocol** — self-optimising, rewrites slow code as Rust binaries
- **Coolify PaaS** — self-hosted deployment platform integration

---

## Environment Variables

See `.env.example` for all variables. Minimum required:

```env
GEMINI_API_KEY=your_key_here
```

---

## Docker (Full Stack)

```bash
docker compose up --build
```

Services started: orchestrator (3500), frontend (8080), neo4j (7474), redis (6379)

---

## Adding New Skills

Drop a new bridge file in `backend/intelligence/` or `backend/mcp_servers/`, then register it in the orchestrator's tool registry (`/api/tools`).

Or ask RAMA directly:
```
RAMA, learn from https://github.com/some/repo
```
