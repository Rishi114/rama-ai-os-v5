"""
RAMA FileWatcher — monitors local directories,
detects new/modified/deleted files, triggers autonomous workflows.
"""

import asyncio, logging, hashlib
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional
from collections import defaultdict

logger = logging.getLogger("rama.filewatcher")


class FileWatcher:
    def __init__(self):
        self._watch_dirs: dict[str, Callable] = {}  # path → callback
        self._file_hashes: dict[str, str] = defaultdict(lambda: "")
        self._running = False

    def watch(self, directory: str, callback: Callable, recursive: bool = True):
        """Register a directory to watch."""
        path = Path(directory)
        if not path.exists():
            logger.warning(f"Watch directory doesn't exist: {directory}")
            return False

        key = str(path.resolve())
        self._watch_dirs[key] = (callback, recursive)
        logger.info(f"Watching: {directory} (recursive={recursive})")
        return True

    def _get_file_hash(self, filepath: Path) -> str:
        """Compute MD5 hash of file content."""
        try:
            return hashlib.md5(filepath.read_bytes()).hexdigest()
        except Exception:
            return ""

    async def monitor_loop(self, interval: int = 2):
        """Background loop to detect file changes."""
        self._running = True
        logger.info("FileWatcher monitor loop started")

        while self._running:
            try:
                for watch_path, (callback, recursive) in self._watch_dirs.items():
                    path_obj = Path(watch_path)
                    pattern = "**/*" if recursive else "*"
                    files = list(path_obj.glob(pattern))

                    for filepath in files:
                        if not filepath.is_file():
                            continue

                        current_hash = self._get_file_hash(filepath)
                        prev_hash = self._file_hashes.get(str(filepath), "")

                        if current_hash != prev_hash:
                            if prev_hash == "":
                                # New file
                                event = {
                                    "type": "created",
                                    "path": str(filepath),
                                    "ts": datetime.utcnow().isoformat(),
                                }
                                logger.info(f"📄 File created: {filepath.name}")
                            else:
                                # Modified file
                                event = {
                                    "type": "modified",
                                    "path": str(filepath),
                                    "ts": datetime.utcnow().isoformat(),
                                }
                                logger.info(f"✏️  File modified: {filepath.name}")

                            self._file_hashes[str(filepath)] = current_hash
                            asyncio.create_task(callback(event))

                    # Check for deleted files
                    for tracked_path in list(self._file_hashes.keys()):
                        if tracked_path.startswith(watch_path) and not Path(tracked_path).exists():
                            event = {
                                "type": "deleted",
                                "path": tracked_path,
                                "ts": datetime.utcnow().isoformat(),
                            }
                            logger.info(f"🗑️  File deleted: {Path(tracked_path).name}")
                            del self._file_hashes[tracked_path]
                            asyncio.create_task(callback(event))
            except Exception as e:
                logger.error(f"FileWatcher error: {e}")

            await asyncio.sleep(interval)

    def stop(self):
        self._running = False
        logger.info("FileWatcher stopped")


# ── Common use case: Git commit on file change ────────────────────────────
async def auto_git_commit(file_event: dict, repo_path: str = "."):
    """Auto-commit changes when files are modified."""
    import subprocess
    try:
        if file_event["type"] != "modified":
            return

        filepath = file_event["path"]
        msg = f"RAMA auto-commit: {Path(filepath).name}"

        result = subprocess.run(
            ["git", "-C", repo_path, "add", filepath],
            capture_output=True, timeout=10,
        )
        if result.returncode == 0:
            subprocess.run(
                ["git", "-C", repo_path, "commit", "-m", msg],
                capture_output=True, timeout=10,
            )
            logger.info(f"Auto-committed: {msg}")
    except Exception as e:
        logger.error(f"Auto-commit failed: {e}")
