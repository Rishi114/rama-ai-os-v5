"""
RAMA OSINT Vision — scrapes Twitter, Reddit, GitHub
without paid API keys using public endpoints + HTML parsing.
"""

import asyncio, logging, re
from datetime import datetime
from typing import Optional
import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger("rama.osint")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class OSINTVision:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(headers=HEADERS)
        return self._session

    # ── Reddit (JSON API, no auth needed) ────────────────────────────────
    async def scrape_reddit(self, subreddit: str = "technology", limit: int = 10) -> list[dict]:
        session = await self._get_session()
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    data = await r.json()
                    posts = data.get("data", {}).get("children", [])
                    return [
                        {
                            "title": p["data"]["title"],
                            "score": p["data"]["score"],
                            "comments": p["data"]["num_comments"],
                            "url": f"https://reddit.com{p['data']['permalink']}",
                            "text": (p["data"].get("selftext") or "")[:200],
                        }
                        for p in posts
                    ]
        except Exception as e:
            logger.warning(f"Reddit scrape failed: {e}")
        return []

    # ── GitHub trending ───────────────────────────────────────────────────
    async def scrape_github_trending(self, language: str = "", period: str = "daily") -> list[dict]:
        session = await self._get_session()
        lang_path = f"/{language}" if language else ""
        url = f"https://github.com/trending{lang_path}?since={period}"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    soup = BeautifulSoup(await r.text(), "html.parser")
                    repos = []
                    for article in soup.select("article.Box-row")[:10]:
                        h2 = article.select_one("h2 a")
                        desc = article.select_one("p")
                        stars = article.select_one("a[href*='stargazers']")
                        repos.append({
                            "repo": h2.get_text(strip=True).replace("\n", "").replace(" ", "") if h2 else "",
                            "url": f"https://github.com{h2['href']}" if h2 else "",
                            "description": desc.get_text(strip=True) if desc else "",
                            "stars": stars.get_text(strip=True) if stars else "0",
                        })
                    return repos
        except Exception as e:
            logger.warning(f"GitHub trending scrape failed: {e}")
        return []

    # ── GitHub repo analysis ──────────────────────────────────────────────
    async def analyse_github_repo(self, repo_url: str) -> dict:
        """Fetch README and basic repo metadata."""
        session = await self._get_session()
        # Convert to API URL
        match = re.match(r"https://github\.com/([^/]+)/([^/]+)", repo_url)
        if not match:
            return {"error": "Invalid GitHub URL"}

        owner, repo = match.group(1), match.group(2)
        api_base = f"https://api.github.com/repos/{owner}/{repo}"

        try:
            async with session.get(api_base, timeout=aiohttp.ClientTimeout(total=8)) as r:
                meta = await r.json() if r.status == 200 else {}

            readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
            async with session.get(readme_url, timeout=aiohttp.ClientTimeout(total=8)) as r:
                readme = (await r.text())[:1500] if r.status == 200 else "No README found"

            return {
                "repo": f"{owner}/{repo}",
                "stars": meta.get("stargazers_count", 0),
                "language": meta.get("language", "Unknown"),
                "description": meta.get("description", ""),
                "topics": meta.get("topics", []),
                "readme_preview": readme,
                "url": repo_url,
            }
        except Exception as e:
            return {"error": str(e), "url": repo_url}

    # ── Hacker News ───────────────────────────────────────────────────────
    async def scrape_hackernews(self, limit: int = 10) -> list[dict]:
        session = await self._get_session()
        try:
            async with session.get(
                "https://hacker-news.firebaseio.com/v0/topstories.json",
                timeout=aiohttp.ClientTimeout(total=8),
            ) as r:
                story_ids = (await r.json())[:limit]

            stories = []
            for sid in story_ids:
                async with session.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as r:
                    if r.status == 200:
                        s = await r.json()
                        stories.append({
                            "title": s.get("title", ""),
                            "url": s.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                            "score": s.get("score", 0),
                            "comments": s.get("descendants", 0),
                        })
            return stories
        except Exception as e:
            logger.warning(f"HN scrape failed: {e}")
        return []

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
