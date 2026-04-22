"""
RAMA Oracle SaaS Engine — finds viral trends, generates startup ideas,
and suggests products RAMA could build and launch.
"""

import asyncio, json, logging
from datetime import datetime
from typing import Optional
import aiohttp

logger = logging.getLogger("rama.oracle")


class OracleSaaS:
    def __init__(self, gemini=None):
        self.gemini = gemini
        self._session: Optional[aiohttp.ClientSession] = None
        self._ideas: list = []

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    # ── Fetch trending topics from HN, Reddit, Twitter ────────────────
    async def get_trending_topics(self) -> list[dict]:
        """Pull trending topics from Hacker News and Reddit."""
        trends = []
        session = await self._get_session()

        # HN top stories
        try:
            async with session.get(
                "https://hacker-news.firebaseio.com/v0/topstories.json",
                timeout=aiohttp.ClientTimeout(total=8),
            ) as r:
                story_ids = (await r.json())[:5]
                for sid in story_ids:
                    async with session.get(
                        f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as sr:
                        if sr.status == 200:
                            s = await sr.json()
                            trends.append({
                                "title": s.get("title", ""),
                                "source": "hackernews",
                                "score": s.get("score", 0),
                                "url": s.get("url", ""),
                            })
        except Exception as e:
            logger.debug(f"HN fetch failed: {e}")

        # Reddit hot posts
        try:
            async with session.get(
                "https://www.reddit.com/r/technology/hot.json?limit=5",
                timeout=aiohttp.ClientTimeout(total=8),
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    for post in data.get("data", {}).get("children", [])[:5]:
                        trends.append({
                            "title": post["data"]["title"],
                            "source": "reddit",
                            "score": post["data"]["score"],
                            "url": f"https://reddit.com{post['data']['permalink']}",
                        })
        except Exception as e:
            logger.debug(f"Reddit fetch failed: {e}")

        return trends[:10]

    # ── Generate startup ideas from trends ──────────────────────────────
    async def brainstorm_ideas(self, trends: list[dict]) -> list[dict]:
        """Use Gemini to brainstorm SaaS products based on trends."""
        if not self.gemini:
            return []

        trend_text = "\n".join([f"- {t['title']} ({t['source']})" for t in trends[:5]])
        prompt = (
            f"Based on these trending topics:\n{trend_text}\n\n"
            f"Generate 3 SaaS product ideas that RAMA could build and launch:\n"
            f"For each idea, provide:\n"
            f"1. Product name (cool, memorable)\n"
            f"2. Problem it solves (1 sentence)\n"
            f"3. Target market (1 sentence)\n"
            f"4. MVP features (3-4 bullet points)\n"
            f"5. Revenue model (subscription/one-time/freemium)\n"
            f"6. Build time estimate (days)\n\n"
            f"Format as JSON array."
        )

        try:
            response = self.gemini.generate_content(prompt)
            text = response.text.strip()
            # Extract JSON
            import re
            json_match = re.search(r'\[[\s\S]*\]', text)
            if json_match:
                ideas = json.loads(json_match.group())
                return ideas
        except Exception as e:
            logger.error(f"Brainstorm failed: {e}")
        return []

    # ── Full oracle pipeline ───────────────────────────────────────────
    async def run_oracle(self) -> dict:
        """Full pipeline: trends → ideas → action plan."""
        try:
            logger.info("Oracle SaaS: analyzing market trends...")
            trends = await self.get_trending_topics()

            if not trends:
                return {"status": "no_trends_found"}

            logger.info(f"Oracle SaaS: brainstorming ideas from {len(trends)} trends...")
            ideas = await self.brainstorm_ideas(trends)

            self._ideas = ideas
            result = {
                "status": "success",
                "trends_analyzed": len(trends),
                "ideas_generated": len(ideas),
                "ideas": ideas,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Log top idea
            if ideas:
                top = ideas[0]
                logger.info(f"🚀 TOP IDEA: {top.get('Product name', 'Unnamed')} — {top.get('Problem', '')}")

            return result
        except Exception as e:
            logger.error(f"Oracle pipeline failed: {e}")
            return {"status": "error", "error": str(e)}

    # ── Autonomous oracle loop ─────────────────────────────────────────
    async def oracle_loop(self, interval_hours: float = 6):
        """Run oracle analysis every N hours."""
        logger.info("Oracle SaaS autonomous loop started")
        while True:
            await self.run_oracle()
            await asyncio.sleep(interval_hours * 3600)

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
