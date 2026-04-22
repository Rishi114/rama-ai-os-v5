"""
RAMA NetworkSentinel — background port monitor + threat detection
"""

import asyncio, socket, logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("rama.sentinel")

MONITORED_PORTS = [22, 80, 443, 3000, 3500, 5432, 6379, 7474, 8080]
SUSPICIOUS_PORTS = [1337, 4444, 5555, 6666, 31337, 12345]


class NetworkSentinel:
    def __init__(self):
        self.alerts: list = []
        self.status = "SCANNING"
        self.last_scan: Optional[str] = None
        self._running = False

    def _check_port(self, port: int, host: str = "0.0.0.0") -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            try:
                s.bind((host, port))
                return False   # port free
            except OSError:
                return True    # port in use

    async def scan_once(self) -> dict:
        open_ports = []
        threats = []

        for port in MONITORED_PORTS + SUSPICIOUS_PORTS:
            if self._check_port(port):
                open_ports.append(port)
                if port in SUSPICIOUS_PORTS:
                    alert = {
                        "ts": datetime.utcnow().isoformat(),
                        "port": port,
                        "severity": "HIGH",
                        "message": f"Suspicious port {port} is open — possible intrusion",
                    }
                    threats.append(alert)
                    self.alerts.append(alert)
                    logger.warning(f"THREAT DETECTED: port {port}")

        self.last_scan = datetime.utcnow().isoformat()
        self.status = "THREAT_DETECTED" if threats else "NOMINAL"

        if len(self.alerts) > 100:
            self.alerts = self.alerts[-80:]

        return {"open_ports": open_ports, "threats": threats, "status": self.status}

    async def monitor_loop(self, interval: int = 10):
        self._running = True
        logger.info("Sentinel monitor started")
        while self._running:
            try:
                await self.scan_once()
            except Exception as e:
                logger.error(f"Sentinel scan error: {e}")
            await asyncio.sleep(interval)

    def get_status(self) -> dict:
        return {
            "status": self.status,
            "last_scan": self.last_scan,
            "alert_count": len(self.alerts),
            "recent_alerts": self.alerts[-5:],
        }

    def stop(self):
        self._running = False
