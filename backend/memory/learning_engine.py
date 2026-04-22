"""
RAMA LearningEngine — FAISS-backed vector memory + GitHub skill acquisition
"""

import json, asyncio, hashlib, logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import aiohttp

logger = logging.getLogger("rama.memory")


class LearningEngine:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.memory_file = self.data_dir / "memory.json"
        self.skills_file = self.data_dir / "learned_skills.json"
        self._memory: list = self._load(self.memory_file)
        self._skills: list = self._load(self.skills_file)
        self._index = None   # FAISS index (lazy-loaded)
        self._embedder = None

    def _load(self, path: Path) -> list:
        try:
            return json.loads(path.read_text()) if path.exists() else []
        except Exception:
            return []

    def _save(self, path: Path, data: list):
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    # ── Lazy-load embedding model + FAISS ────────────────────────────────
    def _ensure_index(self):
        if self._index is not None:
            return
        try:
            import faiss
            from sentence_transformers import SentenceTransformer

            self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
            dim = 384
            self._index = faiss.IndexFlatL2(dim)
            self._faiss = faiss
            logger.info("FAISS index initialised")

            # Re-index existing memories
            if self._memory:
                texts = [m.get("input", "") for m in self._memory]
                vecs = self._embedder.encode(texts, convert_to_numpy=True)
                self._index.add(vecs)
        except ImportError:
            logger.warning("faiss/sentence-transformers not available — using keyword search")

    # ── Store interaction ─────────────────────────────────────────────────
    async def store_interaction(self, user_input: str, response: str, intent: str):
        entry = {
            "id": hashlib.md5(f"{user_input}{datetime.utcnow()}".encode()).hexdigest()[:8],
            "ts": datetime.utcnow().isoformat(),
            "input": user_input,
            "response": response[:500],
            "intent": intent,
        }
        self._memory.append(entry)
        if len(self._memory) > 1000:
            self._memory = self._memory[-800:]   # prune oldest
        self._save(self.memory_file, self._memory)

        # Add to FAISS
        try:
            self._ensure_index()
            if self._index and self._embedder:
                vec = self._embedder.encode([user_input], convert_to_numpy=True)
                self._index.add(vec)
        except Exception as e:
            logger.warning(f"FAISS add failed: {e}")

    # ── Query similar past context ────────────────────────────────────────
    async def query_similar(self, query: str, top_k: int = 3) -> str:
        if not self._memory:
            return ""
        try:
            self._ensure_index()
            if self._index and self._embedder and self._index.ntotal > 0:
                vec = self._embedder.encode([query], convert_to_numpy=True)
                _, ids = self._index.search(vec, min(top_k, self._index.ntotal))
                results = []
                for i in ids[0]:
                    if 0 <= i < len(self._memory):
                        m = self._memory[i]
                        results.append(f"[{m['intent']}] {m['input'][:100]} → {m['response'][:100]}")
                return "\n".join(results)
        except Exception:
            pass

        # Keyword fallback
        q_lower = query.lower()
        matches = [
            m for m in self._memory[-50:]
            if any(w in m.get("input", "").lower() for w in q_lower.split()[:5])
        ][:top_k]
        return "\n".join(
            f"[{m['intent']}] {m['input'][:80]} → {m['response'][:80]}" for m in matches
        )

    # ── Get all memory ────────────────────────────────────────────────────
    async def get_all(self) -> dict:
        return {
            "interactions": len(self._memory),
            "skills": self._skills,
            "recent": self._memory[-10:],
        }

    # ── Learn from GitHub repo ────────────────────────────────────────────
    async def learn_from_github(self, github_url: str) -> dict:
        try:
            # Convert github URL to raw README
            raw_url = (
                github_url
                .replace("github.com", "raw.githubusercontent.com")
                .rstrip("/") + "/main/README.md"
            )
            async with aiohttp.ClientSession() as session:
                async with session.get(raw_url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status == 200:
                        readme = (await r.text())[:2000]
                    else:
                        readme = f"Could not fetch README (HTTP {r.status})"

            skill_entry = {
                "url": github_url,
                "summary": readme[:300],
                "learned_at": datetime.utcnow().isoformat(),
            }
            self._skills.append(skill_entry)
            self._save(self.skills_file, self._skills)

            return {"status": "learned", "url": github_url, "preview": readme[:200]}
        except Exception as e:
            return {"status": "error", "error": str(e)}
