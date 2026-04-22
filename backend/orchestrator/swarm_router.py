"""
RAMA SwarmRouter — dynamically routes tasks to the right local Ollama model
or falls back to Gemini cloud when needed.
"""

import asyncio
import json
import logging
from typing import Optional
import aiohttp
from core.prompts import SYSTEM_PROMPTS, CEO_PROMPT

logger = logging.getLogger("rama.swarm")

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"

# Map intent → model name
INTENT_MODEL_MAP = {
    "CODER":        "qwen2.5-coder",
    "VISION":       "llava",
    "ANALYST":      "llama3",
    "SECURITY":     "llama3",
    "CREATIVE":     "llama3",
    "ORCHESTRATOR": "llama3",
}

# Models that should be available locally
REQUIRED_MODELS = ["phi3", "qwen2.5-coder", "llava", "llama3"]


class SwarmRouter:
    def __init__(self, gemini_fallback=None):
        self._session: Optional[aiohttp.ClientSession] = None
        self.gemini_fallback = gemini_fallback          # GoogleGenAI instance
        self.available_models: set[str] = set()

    async def _session_get(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=120)
            )
        return self._session

    # ── Model health check ────────────────────────────────────────────────
    async def check_available_models(self) -> set[str]:
        try:
            session = await self._session_get()
            async with session.get("http://localhost:11434/api/tags") as r:
                if r.status == 200:
                    data = await r.json()
                    self.available_models = {
                        m["name"].split(":")[0]
                        for m in data.get("models", [])
                    }
                    logger.info(f"Ollama models available: {self.available_models}")
        except Exception as e:
            logger.warning(f"Ollama unreachable: {e}")
        return self.available_models

    # ── Raw Ollama call ───────────────────────────────────────────────────
    async def _call_ollama(self, model: str, prompt: str, system: str = "") -> str:
        if model not in self.available_models:
            logger.warning(f"Model {model} not available, falling back to Gemini")
            return await self._call_gemini(prompt, system)

        payload = {
            "model": model,
            "prompt": f"{system}\n\n{prompt}" if system else prompt,
            "stream": False,
            "options": {"temperature": 0.7, "num_ctx": 4096},
        }
        try:
            session = await self._session_get()
            async with session.post(OLLAMA_URL, json=payload) as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get("response", "")
                return f"[Ollama error: HTTP {r.status}]"
        except asyncio.TimeoutError:
            return await self._call_gemini(prompt, system)
        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            return await self._call_gemini(prompt, system)

    # ── Gemini cloud fallback ─────────────────────────────────────────────
    async def _call_gemini(self, prompt: str, system: str = "") -> str:
        if not self.gemini_fallback:
            return "Error: Gemini fallback not configured."
        try:
            full = f"{system}\n\n{prompt}" if system else prompt
            response = self.gemini_fallback.generate_content(full)
            return response.text
        except Exception as e:
            return f"Error: {e}"

    # ── Classify intent using phi3 ────────────────────────────────────────
    async def _classify_intent(self, user_input: str, emotion: str = "neutral") -> str:
        if "phi3" not in self.available_models:
            # Fallback: simple keyword routing
            lower = user_input.lower()
            if any(k in lower for k in ["code", "write", "fix", "build", "function", "script"]):
                return "CODER"
            if any(k in lower for k in ["look", "see", "image", "screen", "photo"]):
                return "VISION"
            if any(k in lower for k in ["analyse", "analyze", "data", "chart", "revenue"]):
                return "ANALYST"
            if any(k in lower for k in ["hack", "secure", "port", "vulnerability", "scan"]):
                return "SECURITY"
            if any(k in lower for k in ["video", "content", "youtube", "instagram", "write a post"]):
                return "CREATIVE"
            return "ORCHESTRATOR"

        intent_raw = await self._call_ollama(
            "phi3",
            f"User input: '{user_input}'\nEmotion: {emotion}\nClassify:",
            SYSTEM_PROMPTS["ROUTER"],
        )
        intent = intent_raw.strip().upper()
        return intent if intent in INTENT_MODEL_MAP else "ORCHESTRATOR"

    # ── Main public routing method ────────────────────────────────────────
    async def route_task(
        self,
        user_input: str,
        emotion: str = "neutral",
        context: str = "",
        ceo_mode: bool = False,
    ) -> dict:
        await self.check_available_models()

        # CEO mode — complex multi-agent task
        if ceo_mode or any(
            kw in user_input.lower()
            for kw in ["deploy agents", "high efficiency mode", "run the company"]
        ):
            result = await self._call_ollama(
                "llama3",
                f"Context: {context}\n\nCommand: {user_input}",
                CEO_PROMPT,
            )
            return {"intent": "CEO_MODE", "model": "llama3", "response": result}

        # Standard routing
        intent = await self._classify_intent(user_input, emotion)
        model = INTENT_MODEL_MAP.get(intent, "llama3")

        system = SYSTEM_PROMPTS.get(intent, SYSTEM_PROMPTS["ORCHESTRATOR"])
        if context:
            system += f"\n\nContext from memory:\n{context}"

        response = await self._call_ollama(model, user_input, system)

        return {
            "intent": intent,
            "model": model,
            "response": response,
            "emotion": emotion,
        }

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
