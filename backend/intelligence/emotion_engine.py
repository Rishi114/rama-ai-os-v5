"""
RAMA EmotionEngine — detects user sentiment and adjusts RAMA's tone
"""

import re


STRESSED_KEYWORDS = [
    "urgent", "asap", "fix now", "broken", "crash", "emergency", "help",
    "not working", "error", "bug", "failed", "issue", "problem", "stuck",
    "deadline", "immediately", "please please", "!!",
]

EXCITED_KEYWORDS = [
    "awesome", "amazing", "great", "love it", "yes!", "perfect", "let's go",
    "🔥", "🚀", "💪", "🎉", "wow", "incredible", "nice", "brilliant",
]


class EmotionEngine:
    def detect(self, text: str) -> str:
        lower = text.lower()
        exclamations = text.count("!")

        stressed_score = sum(1 for kw in STRESSED_KEYWORDS if kw in lower)
        excited_score = sum(1 for kw in EXCITED_KEYWORDS if kw in lower)
        excited_score += min(exclamations // 2, 3)

        if stressed_score >= 2:
            return "stressed"
        if excited_score >= 2:
            return "excited"
        if stressed_score == 1:
            return "focused"
        return "neutral"

    def tone_adjustment(self, emotion: str) -> str:
        map_ = {
            "stressed":  "Be calm, direct, and solution-focused. Skip the banter.",
            "excited":   "Match the energy! Be enthusiastic and fast-paced.",
            "focused":   "Be precise and efficient. Get straight to the point.",
            "neutral":   "Normal RAMA persona — loyal, capable, Mumbai-energy.",
        }
        return map_.get(emotion, map_["neutral"])
