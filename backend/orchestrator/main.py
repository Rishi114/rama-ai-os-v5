"""
RAMA Orchestrator — FastAPI main entry point
Handles: chat, voice, tools, memory, security, file ops
"""

import os, json, asyncio, logging
from pathlib import Path
from typing import Optional
from datetime import datetime

import google.generativeai as genai
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from orchestrator.swarm_router import SwarmRouter
from memory.learning_engine import LearningEngine
from security.sentinel import NetworkSentinel
from intelligence.emotion_engine import EmotionEngine

# ── Setup ─────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rama.main")

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    gemini = genai.GenerativeModel("gemini-1.5-flash")
else:
    gemini = None
    logger.warning("No Gemini API key — cloud fallback disabled")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
MEMORY_FILE = DATA_DIR / "memory.json"
SKILLS_FILE = DATA_DIR / "learned_skills.json"

# ── Component init ────────────────────────────────────────────────────────
router = SwarmRouter(gemini_fallback=gemini)
learner = LearningEngine(str(DATA_DIR))
sentinel = NetworkSentinel()
emotion_engine = EmotionEngine()

# ── App ───────────────────────────────────────────────────────────────────
app = FastAPI(title="RAMA Orchestrator", version="5.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ───────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    history: list = []
    ceo_mode: bool = False
    session_id: str = "default"


class FileOpsRequest(BaseModel):
    operations: list   # [{action, path, content?}]


class SkillRequest(BaseModel):
    github_url: str


# ── Startup ───────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    await router.check_available_models()
    if os.getenv("NETWORK_SENTINEL_ENABLED", "true").lower() == "true":
        asyncio.create_task(sentinel.monitor_loop())
    logger.info("RAMA Orchestrator online")


@app.on_event("shutdown")
async def shutdown():
    await router.close()


# ── Health ────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "online",
        "models": list(router.available_models),
        "timestamp": datetime.utcnow().isoformat(),
    }


# ── Chat ──────────────────────────────────────────────────────────────────
@app.post("/api/chat")
async def chat(req: ChatRequest):
    # Detect emotion
    emotion = emotion_engine.detect(req.message)

    # Retrieve similar past context
    context = await learner.query_similar(req.message)

    # Route through swarm
    result = await router.route_task(
        req.message,
        emotion=emotion,
        context=context,
        ceo_mode=req.ceo_mode,
    )

    # Learn from this interaction
    asyncio.create_task(
        learner.store_interaction(req.message, result["response"], result["intent"])
    )

    return result


# ── Gemini reasoning (cloud, for complex tasks) ───────────────────────────
@app.post("/api/reason")
async def reason(req: ChatRequest):
    if not gemini:
        raise HTTPException(503, "Gemini not configured")
    try:
        history = [
            {"role": m["role"], "parts": [m["content"]]}
            for m in req.history[-10:]
        ]
        chat_session = gemini.start_chat(history=history)
        response = chat_session.send_message(req.message)
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(500, str(e))


# ── File system (batch) ───────────────────────────────────────────────────
@app.post("/api/files")
async def file_ops(req: FileOpsRequest):
    results = []
    for op in req.operations:
        action = op.get("action")
        rel_path = op.get("path", "")
        safe_path = DATA_DIR / Path(rel_path).name  # sandbox

        try:
            if action == "write":
                safe_path.write_text(op.get("content", ""), encoding="utf-8")
                results.append({"path": rel_path, "status": "written"})
            elif action == "read":
                results.append({
                    "path": rel_path,
                    "content": safe_path.read_text(encoding="utf-8"),
                })
            elif action == "list":
                items = [p.name for p in DATA_DIR.iterdir()]
                results.append({"path": rel_path, "items": items})
            else:
                results.append({"path": rel_path, "error": f"Unknown action: {action}"})
        except Exception as e:
            results.append({"path": rel_path, "error": str(e)})

    return {"results": results}


# ── Security ──────────────────────────────────────────────────────────────
@app.get("/api/security/status")
async def security_status():
    return sentinel.get_status()


# ── Memory / skills ───────────────────────────────────────────────────────
@app.get("/api/memory")
async def get_memory():
    return await learner.get_all()


@app.post("/api/skills/learn")
async def learn_skill(req: SkillRequest):
    result = await learner.learn_from_github(req.github_url)
    return result


# ── Autonomous action (reflection) ───────────────────────────────────────
@app.post("/api/reflect")
async def reflect():
    """RAMA analyses its own code and proposes optimisations"""
    if not gemini:
        return {"status": "Gemini required for reflection"}
    try:
        src = Path("orchestrator/swarm_router.py").read_text()
        prompt = (
            f"Analyse this Python code for performance improvements, bugs, "
            f"and architectural issues. Be concise.\n\n```python\n{src[:3000]}\n```"
        )
        response = gemini.generate_content(prompt)
        return {"reflection": response.text}
    except Exception as e:
        return {"error": str(e)}


# ── Tools registry ────────────────────────────────────────────────────────
@app.get("/api/tools")
async def list_tools():
    return {
        "tools": [
            {"name": "chat", "description": "Multi-LLM swarm chat with emotion detection"},
            {"name": "reason", "description": "Deep reasoning via Gemini Pro"},
            {"name": "files", "description": "Batch file read/write/list"},
            {"name": "security", "description": "Network sentinel status"},
            {"name": "memory", "description": "FAISS vector memory retrieval"},
            {"name": "skills/learn", "description": "Learn from GitHub repo"},
            {"name": "reflect", "description": "RAMA self-analysis"},
        ],
        "models": list(router.available_models),
        "batch_support": True,
    }
