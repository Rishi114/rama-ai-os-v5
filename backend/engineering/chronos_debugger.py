"""
RAMA Chronos Debugger — memory snapshots + time-travel crash analysis
"""

import asyncio, copy, json, logging, traceback
from collections import deque
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("rama.chronos")

SNAPSHOT_DIR = Path("data/chronos_snapshots")
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


class ChronosDebugger:
    def __init__(self, max_snapshots: int = 30):
        self._snapshots: deque = deque(maxlen=max_snapshots)
        self._running = False

    # ── Take a snapshot ───────────────────────────────────────────────────
    def snapshot(self, state: dict):
        entry = {
            "ts": datetime.utcnow().isoformat(),
            "state": copy.deepcopy(state),
        }
        self._snapshots.append(entry)

        # Persist latest 5 to disk
        snapshots_list = list(self._snapshots)[-5:]
        (SNAPSHOT_DIR / "latest.json").write_text(
            json.dumps(snapshots_list, default=str, indent=2)
        )

    # ── Background snapshot loop ──────────────────────────────────────────
    async def snapshot_loop(self, state_provider, interval: int = 10):
        """Call snapshot_provider() every `interval` seconds."""
        self._running = True
        logger.info("Chronos snapshot loop started")
        while self._running:
            try:
                state = state_provider()
                self.snapshot(state)
            except Exception as e:
                logger.warning(f"Snapshot failed: {e}")
            await asyncio.sleep(interval)

    # ── Rewind to stable state ────────────────────────────────────────────
    def rewind(self, steps_back: int = 1) -> dict | None:
        if not self._snapshots:
            return None
        idx = max(0, len(self._snapshots) - 1 - steps_back)
        snap = list(self._snapshots)[idx]
        logger.info(f"Chronos rewind → snapshot @ {snap['ts']}")
        return snap

    # ── Analyse crash and propose patch ──────────────────────────────────
    async def analyse_crash(self, error: Exception, context: dict, gemini=None) -> dict:
        tb = traceback.format_exc()
        stable_snap = self.rewind(steps_back=2)

        report = {
            "crash_ts": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_msg": str(error),
            "traceback_summary": tb[:500],
            "stable_state_ts": stable_snap["ts"] if stable_snap else None,
        }

        if gemini:
            try:
                prompt = (
                    f"A Python application crashed with:\n"
                    f"Error: {type(error).__name__}: {str(error)}\n\n"
                    f"Traceback:\n{tb[:800]}\n\n"
                    f"Context: {json.dumps(context, default=str)[:300]}\n\n"
                    "Provide: 1) Root cause (1 sentence), "
                    "2) Defensive code patch (Python), "
                    "3) Prevention strategy (1 sentence)."
                )
                response = gemini.generate_content(prompt)
                report["ai_patch"] = response.text
            except Exception as e:
                report["ai_patch_error"] = str(e)

        # Save crash report
        crash_file = SNAPSHOT_DIR / f"crash_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        crash_file.write_text(json.dumps(report, default=str, indent=2))
        logger.info(f"Crash report saved: {crash_file}")

        return report

    def stop(self):
        self._running = False

    def list_snapshots(self) -> list:
        return [{"ts": s["ts"], "keys": list(s["state"].keys())} for s in self._snapshots]
