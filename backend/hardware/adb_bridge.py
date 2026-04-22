"""
RAMA ADB Bridge — Ghost-in-the-Phone
Control your Android device: read notifications, send WhatsApp, take screenshots.

Requirements:
  - ADB installed: https://developer.android.com/tools/releases/platform-tools
  - USB debugging enabled on your phone
  - Phone connected via USB or WiFi ADB
"""

import asyncio, logging, subprocess, base64
from pathlib import Path
from typing import Optional

logger = logging.getLogger("rama.adb")

ADB = "adb"  # or full path e.g. "C:/platform-tools/adb.exe"


def _adb(*args, timeout: int = 10) -> tuple[str, str]:
    """Run an adb command and return (stdout, stderr)."""
    try:
        result = subprocess.run(
            [ADB, *args], capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return "", "ADB not found — install platform-tools"
    except subprocess.TimeoutExpired:
        return "", "ADB command timed out"


class ADBBridge:
    def __init__(self):
        self._connected = False

    # ── Connection ─────────────────────────────────────────────────────────
    def check_connection(self) -> dict:
        stdout, _ = _adb("devices")
        lines = [l for l in stdout.splitlines() if "device" in l and "List" not in l]
        self._connected = len(lines) > 0
        return {
            "connected": self._connected,
            "devices": lines,
        }

    def connect_wifi(self, ip: str, port: int = 5555) -> str:
        stdout, stderr = _adb("connect", f"{ip}:{port}")
        self._connected = "connected" in stdout
        return stdout or stderr

    # ── Screenshots ────────────────────────────────────────────────────────
    def screenshot(self, local_path: str = "data/screen.png") -> Optional[str]:
        _adb("shell", "screencap", "-p", "/sdcard/screen.png")
        stdout, err = _adb("pull", "/sdcard/screen.png", local_path)
        if err and "error" in err.lower():
            return None
        try:
            data = Path(local_path).read_bytes()
            return base64.b64encode(data).decode()
        except Exception:
            return None

    # ── Notifications ──────────────────────────────────────────────────────
    def get_notifications(self) -> list[str]:
        """Dump recent notification text via dumpsys."""
        stdout, _ = _adb("shell", "dumpsys", "notification")
        lines = [l.strip() for l in stdout.splitlines() if "android.text" in l or "android.title" in l]
        return lines[:20]

    # ── WhatsApp ───────────────────────────────────────────────────────────
    def send_whatsapp(self, phone: str, message: str) -> dict:
        """
        Open WhatsApp with a pre-filled message via intent.
        phone: international format without + e.g. '919876543210'
        """
        encoded = message.replace(" ", "%20").replace("&", "%26")
        intent = f"intent://send/{phone}#Intent;scheme=smsto;package=com.whatsapp;S.sms_body={encoded};end"
        stdout, err = _adb(
            "shell", "am", "start", "-a", "android.intent.action.VIEW",
            "-d", f"https://api.whatsapp.com/send?phone={phone}&text={encoded}",
            "com.whatsapp",
        )
        return {"status": "sent" if not err else "error", "detail": stdout or err}

    # ── Shell commands ─────────────────────────────────────────────────────
    def shell(self, command: str) -> str:
        stdout, stderr = _adb("shell", command)
        return stdout or stderr

    # ── Input simulation ───────────────────────────────────────────────────
    def tap(self, x: int, y: int):
        _adb("shell", "input", "tap", str(x), str(y))

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300):
        _adb("shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms))

    def type_text(self, text: str):
        safe = text.replace(" ", "%s").replace("'", "")
        _adb("shell", "input", "text", safe)

    # ── App control ────────────────────────────────────────────────────────
    def launch_app(self, package: str):
        _adb("shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1")

    def kill_app(self, package: str):
        _adb("shell", "am", "force-stop", package)

    def install_apk(self, apk_path: str) -> str:
        stdout, stderr = _adb("install", "-r", apk_path, timeout=120)
        return stdout or stderr
