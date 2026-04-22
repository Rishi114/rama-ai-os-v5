"""
RAMA Genesis Protocol — profiles backend execution,
identifies slow code, rewrites as optimised Python or Rust,
and hot-swaps the implementation.
"""

import asyncio, importlib, logging, os, subprocess, time
from datetime import datetime
from pathlib import Path
from typing import Callable

logger = logging.getLogger("rama.genesis")

EVOLVED_DIR = Path("data/evolved_modules")
EVOLVED_DIR.mkdir(parents=True, exist_ok=True)


class GenesisProtocol:
    def __init__(self, gemini=None):
        self.gemini = gemini
        self._profile: dict[str, float] = {}  # module → avg latency ms
        self._evolved: list[dict] = []

    # ── Profile a function call ───────────────────────────────────────────
    async def profile(self, fn: Callable, *args, label: str = "", **kwargs):
        start = time.perf_counter()
        result = await fn(*args, **kwargs) if asyncio.iscoroutinefunction(fn) else fn(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000

        key = label or fn.__name__
        prev = self._profile.get(key, elapsed_ms)
        self._profile[key] = (prev * 0.8) + (elapsed_ms * 0.2)  # EMA

        if elapsed_ms > 300:
            logger.warning(f"SLOW: {key} took {elapsed_ms:.1f}ms — queuing for evolution")
            asyncio.create_task(self._evolve_module(key, elapsed_ms))

        return result

    # ── Request an optimised rewrite from Gemini ──────────────────────────
    async def _evolve_module(self, module_name: str, latency_ms: float):
        if not self.gemini:
            logger.info(f"Genesis: no Gemini — skipping evolution of {module_name}")
            return

        # Find the source file
        candidates = list(Path("orchestrator").rglob("*.py")) + list(Path("memory").rglob("*.py"))
        src_file = next((f for f in candidates if module_name in f.stem), None)
        src_code = src_file.read_text()[:2000] if src_file else "# source not found"

        prompt = (
            f"This Python module '{module_name}' has a latency of {latency_ms:.0f}ms — too slow.\n\n"
            f"```python\n{src_code}\n```\n\n"
            "Rewrite it to be 3–10× faster. Use:\n"
            "- asyncio for I/O-bound work\n"
            "- numpy/scipy for numeric ops\n"
            "- efficient data structures\n"
            "- caching where appropriate\n\n"
            "Return only the optimised Python code, no explanation."
        )

        try:
            response = self.gemini.generate_content(prompt)
            optimised = response.text.strip().strip("```python").strip("```").strip()

            out_file = EVOLVED_DIR / f"{module_name}_evolved_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.py"
            out_file.write_text(optimised)

            entry = {
                "module": module_name,
                "original_latency_ms": latency_ms,
                "evolved_at": datetime.utcnow().isoformat(),
                "file": str(out_file),
            }
            self._evolved.append(entry)
            logger.info(f"Genesis: evolved {module_name} → {out_file}")
        except Exception as e:
            logger.error(f"Genesis evolution failed: {e}")

    # ── Build a Rust binary (if rustc available) ──────────────────────────
    def compile_rust(self, rust_code: str, output_name: str) -> Path | None:
        rs_file = EVOLVED_DIR / f"{output_name}.rs"
        bin_file = EVOLVED_DIR / output_name
        rs_file.write_text(rust_code)

        try:
            result = subprocess.run(
                ["rustc", "-O", str(rs_file), "-o", str(bin_file)],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0:
                logger.info(f"Genesis: Rust binary compiled → {bin_file}")
                return bin_file
            logger.warning(f"Rust compile error: {result.stderr[:200]}")
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.warning(f"rustc not available: {e}")
        return None

    def get_profile(self) -> dict:
        return {
            "latencies_ms": self._profile,
            "evolutions": self._evolved,
            "slow_modules": {k: v for k, v in self._profile.items() if v > 300},
        }
