"""Injectable clock.

The domain never calls ``datetime.now`` directly; tests and services build a clock and pass it in.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass
class Clock:
    current: datetime

    def now(self) -> datetime:
        return self.current

    def advance(self, **delta: float) -> None:
        self.current = self.current + timedelta(**delta)


def fixed(moment: datetime | None = None) -> Clock:
    return Clock(moment or datetime(2026, 1, 1, tzinfo=UTC))


def parse_instant(text: str) -> datetime:
    normalized = text.strip().replace("Z", "+00:00")
    moment = datetime.fromisoformat(normalized)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC)


def format_instant(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
