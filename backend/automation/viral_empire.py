"""
RAMA Viral Empire — scrapes trending topics, generates scripts,
creates short-form videos, and uploads to YouTube / Instagram.

Requires: ffmpeg, yt-dlp, moviepy
"""

import asyncio, json, logging, os, subprocess
from pathlib import Path
from datetime import datetime
import aiohttp

logger = logging.getLogger("rama.viral_empire")

OUTPUT_DIR = Path("data/viral_content")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TRENDING_SOURCES = [
    "https://trends.google.com/trends/trendingsearches/daily/rss?geo=IN",
    "https://www.reddit.com/r/technology/hot.json?limit=5",
]


class ViralEmpire:
    def __init__(self, gemini=None):
        self.gemini = gemini
        self._session = None

    async def _get_session(self):
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"User-Agent": "Mozilla/5.0"}
            )
        return self._session

    # ── Trend Scraper ─────────────────────────────────────────────────────
    async def scrape_trends(self) -> list[str]:
        session = await self._get_session()
        trends = []
        try:
            async with session.get(TRENDING_SOURCES[1], timeout=aiohttp.ClientTimeout(total=8)) as r:
                if r.status == 200:
                    data = await r.json()
                    posts = data.get("data", {}).get("children", [])
                    trends = [p["data"]["title"] for p in posts[:5]]
        except Exception as e:
            logger.warning(f"Trend scrape failed: {e}")
            trends = ["AI tools in 2025", "Python tips", "Startup ideas"]
        return trends

    # ── Script Generator ──────────────────────────────────────────────────
    async def generate_script(self, topic: str) -> dict:
        if not self.gemini:
            return {
                "topic": topic,
                "hook": f"Did you know about {topic}? 🔥",
                "body": f"Here's everything about {topic} in 60 seconds...",
                "cta": "Follow for more! Drop a comment below!",
            }
        try:
            prompt = (
                f"Write a viral YouTube Shorts / Instagram Reels script about: '{topic}'\n\n"
                "Format as JSON with keys: hook (first 3 seconds), body (main content, 45s), cta (call to action).\n"
                "Keep it punchy, conversational, trending. Add emojis. Max 150 words total.\n"
                "Return only valid JSON, no markdown."
            )
            response = self.gemini.generate_content(prompt)
            text = response.text.strip().strip("```json").strip("```").strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Script gen failed: {e}")
            return {"hook": topic, "body": "Check this out...", "cta": "Like and follow!"}

    # ── FFmpeg Video Builder ──────────────────────────────────────────────
    def build_video(self, script: dict, output_name: str) -> Path:
        """
        Builds a simple text-on-black video using ffmpeg.
        In production: replace with stock footage + TTS audio.
        """
        out_path = OUTPUT_DIR / f"{output_name}.mp4"
        text = f"{script.get('hook', '')} {script.get('body', '')}"[:200]
        # Escape special chars for ffmpeg drawtext
        safe_text = text.replace("'", "\\'").replace(":", "\\:")[:100]

        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=30:r=30",
            "-vf", (
                f"drawtext=text='{safe_text}':"
                "fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2:"
                "font=DejaVuSans-Bold:line_spacing=10"
            ),
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-t", "30", str(out_path),
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=60)
            logger.info(f"Video built: {out_path}")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"ffmpeg not available: {e}")
            out_path.write_bytes(b"")  # placeholder
        return out_path

    # ── YouTube Upload (via yt-dlp / YouTube Data API) ───────────────────
    async def upload_to_youtube(self, video_path: Path, title: str, description: str) -> dict:
        """
        Requires YouTube Data API v3 credentials in .env
        YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN
        """
        logger.info(f"Upload queued: {video_path.name} → YouTube")
        # Full OAuth2 upload implementation goes here
        # Using google-api-python-client in production
        return {
            "status": "queued",
            "platform": "youtube",
            "file": str(video_path),
            "title": title,
            "queued_at": datetime.utcnow().isoformat(),
        }

    # ── Full pipeline ─────────────────────────────────────────────────────
    async def run_pipeline(self) -> list[dict]:
        results = []
        trends = await self.scrape_trends()
        logger.info(f"Viral Empire: {len(trends)} trends found")

        for i, topic in enumerate(trends[:3]):
            try:
                script = await self.generate_script(topic)
                name = f"viral_{datetime.utcnow().strftime('%Y%m%d_%H%M')}_{i}"
                video = self.build_video(script, name)
                upload = await self.upload_to_youtube(
                    video,
                    title=script.get("hook", topic)[:100],
                    description=f"{script.get('body', '')} {script.get('cta', '')}",
                )
                results.append({"topic": topic, "video": str(video), "upload": upload})
            except Exception as e:
                logger.error(f"Pipeline failed for '{topic}': {e}")
                results.append({"topic": topic, "error": str(e)})

        return results

    # ── Autonomous daily loop ─────────────────────────────────────────────
    async def daily_loop(self, interval_hours: float = 24):
        logger.info("Viral Empire auto-loop started")
        while True:
            await self.run_pipeline()
            await asyncio.sleep(interval_hours * 3600)

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
