"""Keeps generation inside the Gemini free tier: requests per minute and per day."""

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class QuotaExhausted(RuntimeError):
    """The daily request budget is used up; the run stops and can be resumed tomorrow."""


@dataclass
class GenerationLog:
    """Append-only record of generation attempts (data/generation_log.jsonl).

    It makes runs resumable (finished targets are skipped) and lets the limiter count today's
    requests across separate runs."""

    path: Path

    def entries(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text().splitlines() if line.strip()]

    def append(self, **entry: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {"at": datetime.now(UTC).isoformat(timespec="seconds"), **entry}
        with self.path.open("a") as handle:
            handle.write(json.dumps(record) + "\n")

    def requests_today(self) -> int:
        # Gemini's daily quota resets at midnight Pacific time, so counting by UTC date is only an
        # approximation. If Gemini still reports the daily quota used up, the run stops cleanly anyway.
        today = datetime.now(UTC).date().isoformat()
        return sum(
            int(e.get("requests", 0)) for e in self.entries() if str(e.get("at", "")).startswith(today)
        )

    def staged_targets(self) -> set[str]:
        return {e["target_id"] for e in self.entries() if e.get("status") == "staged"}


@dataclass
class RateLimiter:
    requests_per_minute: int
    requests_per_day: int
    #: Requests already made today before this run started.
    used_today: int = 0
    clock: Callable[[], float] = time.monotonic
    sleep: Callable[[float], None] = time.sleep
    _last: float | None = field(default=None, init=False)
    made: int = field(default=0, init=False)

    def acquire(self) -> None:
        """Waits until the next request is allowed, or raises QuotaExhausted for the day."""
        if self.used_today + self.made >= self.requests_per_day:
            raise QuotaExhausted(f"daily budget of {self.requests_per_day} requests is used up")
        interval = 60.0 / self.requests_per_minute
        if self._last is not None:
            wait = self._last + interval - self.clock()
            if wait > 0:
                self.sleep(wait)
        self._last = self.clock()
        self.made += 1
