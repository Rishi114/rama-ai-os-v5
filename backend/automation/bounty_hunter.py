"""
RAMA Bounty Hunter — scrapes Upwork, Fiverr, Toptal, etc.
Finds relevant gigs, generates proposals, and auto-bids.
"""

import asyncio, json, logging, re
from datetime import datetime
from typing import Optional
import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger("rama.bounty_hunter")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


class BountyHunter:
    def __init__(self, gemini=None):
        self.gemini = gemini
        self._session: Optional[aiohttp.ClientSession] = None
        self._found_gigs: list = []

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(headers=HEADERS)
        return self._session

    # ── Scrape Upwork job listings ──────────────────────────────────────
    async def scrape_upwork(self, keywords: str = "python api") -> list[dict]:
        """
        Scrape Upwork job feed (public RSS or web page).
        Returns list of job opportunities.
        """
        session = await self._get_session()
        jobs = []
        try:
            # Upwork API requires OAuth, so we scrape the search page
            search_url = f"https://www.upwork.com/ab/find-work/search?q={keywords.replace(' ', '+')}&sort=recency"
            async with session.get(search_url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    html = await r.text()
                    # Simple extraction (Upwork heavily JS-renders, so limited results)
                    jobs = [
                        {"title": "Upwork job", "platform": "upwork", "url": search_url, "status": "requires_auth"}
                    ]
        except Exception as e:
            logger.warning(f"Upwork scrape failed: {e}")
        return jobs

    # ── Scrape Freelancer.com ──────────────────────────────────────────
    async def scrape_freelancer(self, keywords: str = "python") -> list[dict]:
        """Scrape Freelancer.com project listings."""
        session = await self._get_session()
        jobs = []
        try:
            url = f"https://www.freelancer.com/jobs/{keywords}/"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    soup = BeautifulSoup(await r.text(), "html.parser")
                    for item in soup.select(".project-card")[:10]:
                        title_elem = item.select_one("h4 a")
                        budget_elem = item.select_one(".budget")
                        jobs.append({
                            "title": title_elem.get_text(strip=True) if title_elem else "Unknown",
                            "platform": "freelancer",
                            "budget": budget_elem.get_text(strip=True) if budget_elem else "Unlisted",
                            "url": f"https://www.freelancer.com{title_elem['href']}" if title_elem and 'href' in title_elem.attrs else "",
                        })
        except Exception as e:
            logger.warning(f"Freelancer scrape failed: {e}")
        return jobs

    # ── Generate AI proposal ───────────────────────────────────────────
    async def generate_proposal(self, job: dict) -> str:
        """Use Gemini to generate a compelling proposal."""
        if not self.gemini:
            return f"I'm interested in your {job.get('title', 'project')}. Please consider my bid."
        try:
            prompt = (
                f"Write a winning Upwork/Freelancer proposal for this job:\n"
                f"Title: {job.get('title', 'Unknown')}\n"
                f"Platform: {job.get('platform', 'Unknown')}\n\n"
                f"Make it professional, concise (max 150 words), and compelling.\n"
                f"Mention relevant skills: Python, API design, web scraping, automation.\n"
                f"Emphasize speed, quality, and 24/7 availability."
            )
            response = self.gemini.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Proposal generation failed: {e}")
            return "Interested in your project!"

    # ── Job radar (continuous monitoring) ──────────────────────────────
    async def job_radar(self, keywords: list[str], check_interval: int = 600):
        """Continuously monitor for new gigs matching keywords."""
        logger.info(f"Job Radar started — watching: {', '.join(keywords)}")
        while True:
            try:
                all_jobs = []
                for kw in keywords:
                    upwork = await self.scrape_upwork(kw)
                    freelancer = await self.scrape_freelancer(kw)
                    all_jobs.extend(upwork + freelancer)

                # Filter new ones
                new_jobs = [
                    j for j in all_jobs
                    if j not in self._found_gigs
                ]
                self._found_gigs.extend(new_jobs)
                if len(self._found_gigs) > 100:
                    self._found_gigs = self._found_gigs[-80:]

                if new_jobs:
                    logger.info(f"Bounty Hunter found {len(new_jobs)} new gigs!")
                    for job in new_jobs[:3]:
                        proposal = await self.generate_proposal(job)
                        logger.info(f"  → {job.get('title', 'Unnamed')}\n    Proposal: {proposal[:100]}")
            except Exception as e:
                logger.error(f"Job radar error: {e}")

            await asyncio.sleep(check_interval)

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
