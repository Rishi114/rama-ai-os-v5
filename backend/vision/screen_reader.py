"""
RAMA ScreenReader — takes screenshots, extracts text via OCR,
analyses visual layout, and suggests actions.
"""

import asyncio, base64, logging
from pathlib import Path
from typing import Optional
import os

logger = logging.getLogger("rama.screenreader")


class ScreenReader:
    def __init__(self, gemini=None):
        self.gemini = gemini
        self._last_screenshot = None

    # ── Take screenshot ────────────────────────────────────────────────
    def screenshot(self, output_path: str = "data/screen_capture.png") -> Optional[str]:
        """Take a screenshot and save it."""
        try:
            import pyautogui
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            img = pyautogui.screenshot()
            img.save(output_path)
            self._last_screenshot = output_path
            logger.info(f"Screenshot saved: {output_path}")
            return output_path
        except ImportError:
            logger.error("pyautogui required: pip install pyautogui")
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
        return None

    # ── OCR (text extraction) ──────────────────────────────────────────
    def extract_text(self, image_path: str) -> str:
        """Extract text from image using OCR."""
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            logger.info(f"OCR extracted {len(text)} chars from {image_path}")
            return text
        except ImportError:
            logger.error("pytesseract required: pip install pytesseract (also needs tesseract-ocr installed)")
        except Exception as e:
            logger.error(f"OCR failed: {e}")
        return ""

    # ── Vision analysis via Gemini ─────────────────────────────────────
    async def analyse_screen(self, image_path: Optional[str] = None, gemini=None) -> dict:
        """Analyse screen content: layout, text, UI elements, actions."""
        if not image_path:
            image_path = self.screenshot()
        if not image_path or not Path(image_path).exists():
            return {"error": "No screenshot available"}

        try:
            # Read as base64
            img_data = Path(image_path).read_bytes()
            img_b64 = base64.b64encode(img_data).decode()

            gemini = gemini or self.gemini
            if not gemini:
                return {"error": "Gemini not configured"}

            # Use Gemini's vision capability
            response = gemini.generate_content([
                "Analyse this screenshot. Provide:",
                "1. What's visible on screen (description)",
                "2. Main UI elements and their positions",
                "3. Text content (key information)",
                "4. Suggested actions RAMA could take",
                "5. Confidence level (high/medium/low)",
                "\nFormat as JSON.",
                {
                    "mime_type": "image/png",
                    "data": img_b64,
                }
            ])

            result = {"analysis": response.text, "image": image_path}
            logger.info("Screen analysis complete")
            return result
        except Exception as e:
            logger.error(f"Screen analysis failed: {e}")
            return {"error": str(e)}

    # ── Find UI elements (buttons, inputs, links) ──────────────────────
    async def find_clickables(self, image_path: Optional[str] = None) -> list[dict]:
        """Detect clickable elements on screen."""
        if not image_path:
            image_path = self.screenshot()

        try:
            # Use Gemini to identify clickable elements
            analysis = await self.analyse_screen(image_path)
            if "error" in analysis:
                return []

            prompt = (
                f"From this screenshot analysis:\n{analysis.get('analysis', '')}\n\n"
                f"List all clickable elements (buttons, links, inputs) with approximate coordinates.\n"
                f"Format as JSON array: [{{'element': 'name', 'type': 'button|link|input', 'x': int, 'y': int}}, ...]"
            )
            response = self.gemini.generate_content(prompt)
            import json, re
            match = re.search(r'\[[\s\S]*\]', response.text)
            if match:
                return json.loads(match.group())
        except Exception as e:
            logger.error(f"Find clickables failed: {e}")
        return []

    # ── Monitor screen for changes ─────────────────────────────────────
    async def screen_diff_monitor(self, callback, interval: int = 5):
        """Monitor screen for changes and trigger callback."""
        prev_hash = None
        while True:
            try:
                path = self.screenshot()
                if path:
                    import hashlib
                    current_hash = hashlib.md5(Path(path).read_bytes()).hexdigest()
                    if prev_hash and current_hash != prev_hash:
                        logger.info("Screen changed detected")
                        asyncio.create_task(callback(path))
                    prev_hash = current_hash
            except Exception as e:
                logger.debug(f"Screen diff error: {e}")
            await asyncio.sleep(interval)
