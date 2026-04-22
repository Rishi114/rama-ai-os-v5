"""
RAMA Windows Bridge — native Windows integration
Clipboard monitoring, screen recording, process management, notifications
"""

import asyncio, logging, subprocess, os, json
from pathlib import Path
from typing import Optional
import platform

logger = logging.getLogger("rama.windows")

IS_WINDOWS = platform.system() == "Windows"


class WindowsBridge:
    def __init__(self):
        self.clipboard_last = ""
        self._listening = False

    # ── Clipboard monitoring ────────────────────────────────────────────
    async def get_clipboard(self) -> str:
        if not IS_WINDOWS:
            return ""
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-Clipboard"],
                capture_output=True, text=True, timeout=2,
            )
            return result.stdout.strip()
        except Exception:
            return ""

    async def set_clipboard(self, text: str) -> bool:
        if not IS_WINDOWS:
            return False
        try:
            subprocess.run(
                ["powershell", "-Command", f'Set-Clipboard -Value "{text.replace(chr(34), chr(34)+chr(34))}"'],
                capture_output=True, timeout=2,
            )
            return True
        except Exception:
            return False

    async def monitor_clipboard(self, callback):
        """Monitor clipboard for changes and trigger callback."""
        if not IS_WINDOWS:
            return
        self._listening = True
        while self._listening:
            try:
                current = await self.get_clipboard()
                if current and current != self.clipboard_last:
                    self.clipboard_last = current
                    asyncio.create_task(callback(current))
            except Exception:
                pass
            await asyncio.sleep(1)

    # ── Screen recording ────────────────────────────────────────────────
    def record_screen(self, output_path: str = "data/screen.mp4", duration_sec: int = 30) -> bool:
        """Record screen using ffmpeg (requires ffmpeg installed)."""
        if not IS_WINDOWS:
            return False
        try:
            cmd = [
                "ffmpeg", "-y",
                "-f", "gdigrab",
                "-framerate", "30",
                "-i", "desktop",
                "-t", str(duration_sec),
                "-c:v", "libx264",
                "-preset", "ultrafast",
                output_path,
            ]
            subprocess.run(cmd, capture_output=True, timeout=duration_sec + 10)
            logger.info(f"Screen recorded → {output_path}")
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.warning(f"Screen record failed: {e}")
            return False

    # ── Screenshot via Windows API ──────────────────────────────────────
    def screenshot(self, output_path: str = "data/screenshot.png") -> Optional[str]:
        """Take screenshot using Windows API."""
        if not IS_WINDOWS:
            return None
        try:
            import pyautogui
            img = pyautogui.screenshot()
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path)
            return output_path
        except ImportError:
            logger.warning("pyautogui not available — install with: pip install pyautogui")
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
        return None

    # ── Windows notifications ────────────────────────────────────────────
    def notify(self, title: str, message: str, icon: str = "info") -> bool:
        """Send Windows notification (Windows 10+)."""
        if not IS_WINDOWS:
            return False
        try:
            icon_map = {
                "info": "information",
                "warning": "warning",
                "error": "critical",
                "success": "success",
            }
            ps_code = (
                f'[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, '
                f'ContentType = WindowsRuntime] | Out-Null\n'
                f'[Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, '
                f'ContentType = WindowsRuntime] | Out-Null\n'
                f'[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, '
                f'ContentType = WindowsRuntime] | Out-Null\n'
                f'$xml = @"\n'
                f'<toast>\n'
                f'  <visual>\n'
                f'    <binding template="ToastText02">\n'
                f'      <text id="1">{title}</text>\n'
                f'      <text id="2">{message}</text>\n'
                f'    </binding>\n'
                f'  </visual>\n'
                f'</toast>\n'
                f'"@\n'
                f'$doc = New-Object Windows.Data.Xml.Dom.XmlDocument\n'
                f'$doc.LoadXml($xml)\n'
                f'$toast = New-Object Windows.UI.Notifications.ToastNotification $doc\n'
                f'[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("RAMA").Show($toast)'
            )
            subprocess.run(
                ["powershell", "-Command", ps_code],
                capture_output=True, timeout=5,
            )
            return True
        except Exception as e:
            logger.warning(f"Notification failed: {e}")
        return False

    # ── Process management ──────────────────────────────────────────────
    def get_running_apps(self) -> list[dict]:
        """Get list of running processes/apps."""
        if not IS_WINDOWS:
            return []
        try:
            result = subprocess.run(
                ["tasklist", "/FO", "CSV"],
                capture_output=True, text=True, timeout=5,
            )
            lines = result.stdout.strip().split('\n')[1:]  # skip header
            apps = []
            for line in lines[:30]:  # first 30
                parts = line.strip().split('","')
                if len(parts) >= 2:
                    name = parts[0].strip('"')
                    pid = parts[1].strip('"')
                    apps.append({"name": name, "pid": int(pid) if pid.isdigit() else 0})
            return apps
        except Exception as e:
            logger.error(f"get_running_apps failed: {e}")
            return []

    def kill_process(self, pid: int) -> bool:
        """Kill a process by PID."""
        if not IS_WINDOWS:
            return False
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, timeout=5)
            return True
        except Exception:
            return False

    # ── Environment/registry shortcuts ──────────────────────────────────
    def create_shortcut(self, target: str, shortcut_path: str, args: str = "") -> bool:
        """Create a Windows .lnk shortcut."""
        if not IS_WINDOWS:
            return False
        try:
            ps_code = (
                f'$WshShell = New-Object -ComObject WScript.Shell\n'
                f'$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")\n'
                f'$Shortcut.TargetPath = "{target}"\n'
                f'$Shortcut.Arguments = "{args}"\n'
                f'$Shortcut.Save()'
            )
            subprocess.run(
                ["powershell", "-Command", ps_code],
                capture_output=True, timeout=5,
            )
            logger.info(f"Shortcut created: {shortcut_path}")
            return True
        except Exception as e:
            logger.error(f"Shortcut creation failed: {e}")
            return False

    # ── PowerShell command execution ────────────────────────────────────
    def powershell(self, command: str, timeout: int = 30) -> tuple[str, str]:
        """Execute a PowerShell command."""
        if not IS_WINDOWS:
            return "", "Not Windows"
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True, text=True, timeout=timeout,
            )
            return result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return "", "Command timeout"
        except Exception as e:
            return "", str(e)

    def stop(self):
        self._listening = False
