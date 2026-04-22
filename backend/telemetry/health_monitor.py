"""
RAMA Telemetry — real-time system health monitoring
CPU / RAM / GPU / temps / battery / network
"""

import asyncio, logging, platform
from datetime import datetime
from typing import Optional

import psutil

logger = logging.getLogger("rama.telemetry")


def _safe(fn):
    try:
        return fn()
    except Exception:
        return None


class TelemetryMonitor:
    def __init__(self):
        self._latest: dict = {}
        self._history: list = []
        self._running = False

    def snapshot(self) -> dict:
        cpu = _safe(lambda: psutil.cpu_percent(interval=0.1))
        mem = _safe(psutil.virtual_memory)
        disk = _safe(lambda: psutil.disk_usage("/"))
        net = _safe(lambda: psutil.net_io_counters())
        temps = _safe(psutil.sensors_temperatures)

        gpu_info = None
        try:
            import subprocess
            r = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=3,
            )
            if r.returncode == 0:
                parts = r.stdout.strip().split(", ")
                if len(parts) >= 4:
                    gpu_info = {
                        "utilization_pct": float(parts[0]),
                        "memory_used_mb":  float(parts[1]),
                        "memory_total_mb": float(parts[2]),
                        "temp_c":          float(parts[3]),
                    }
        except Exception:
            pass

        snap = {
            "ts": datetime.utcnow().isoformat(),
            "platform": platform.system(),
            "cpu": {
                "usage_pct": cpu,
                "cores": psutil.cpu_count(),
                "freq_mhz": _safe(lambda: psutil.cpu_freq().current if psutil.cpu_freq() else None),
            },
            "memory": {
                "total_gb": round(mem.total / 1e9, 2) if mem else None,
                "used_gb":  round(mem.used  / 1e9, 2) if mem else None,
                "pct":      mem.percent if mem else None,
            },
            "disk": {
                "total_gb": round(disk.total / 1e9, 1) if disk else None,
                "free_gb":  round(disk.free  / 1e9, 1) if disk else None,
                "pct":      disk.percent if disk else None,
            },
            "network": {
                "bytes_sent_mb": round(net.bytes_sent / 1e6, 1) if net else None,
                "bytes_recv_mb": round(net.bytes_recv / 1e6, 1) if net else None,
            },
            "gpu": gpu_info,
            "temperatures": {
                k: [t.current for t in v]
                for k, v in (temps or {}).items()
            },
        }
        self._latest = snap
        self._history.append({"ts": snap["ts"], "cpu": cpu, "ram": mem.percent if mem else None})
        if len(self._history) > 120:
            self._history = self._history[-100:]
        return snap

    async def monitor_loop(self, interval: int = 5):
        self._running = True
        while self._running:
            try:
                self.snapshot()
            except Exception as e:
                logger.debug(f"Telemetry error: {e}")
            await asyncio.sleep(interval)

    def get_latest(self) -> dict:
        return self._latest or self.snapshot()

    def get_history(self) -> list:
        return self._history

    def alert_level(self) -> str:
        snap = self._latest
        if not snap:
            return "UNKNOWN"
        cpu = (snap.get("cpu") or {}).get("usage_pct", 0) or 0
        ram = (snap.get("memory") or {}).get("pct", 0) or 0
        if cpu > 90 or ram > 90:
            return "CRITICAL"
        if cpu > 70 or ram > 75:
            return "WARNING"
        return "NOMINAL"

    def stop(self):
        self._running = False
