"""Time window helpers shared by the aggregation jobs."""

from __future__ import annotations

from datetime import datetime, timedelta

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
DAY_FORMAT = "%Y-%m-%d"


def parse_timestamp(text: str) -> datetime:
    """Parse a ``YYYY-MM-DD HH:MM:SS`` timestamp."""
    return datetime.strptime(text.strip(), TIMESTAMP_FORMAT)


def day_window(day: str) -> tuple[datetime, datetime]:
    """Return the start of ``day`` (``YYYY-MM-DD``) and the start of the following day."""
    start = datetime.strptime(day, DAY_FORMAT)
    return start, start + timedelta(days=1)


def in_window(moment: datetime, start: datetime, end: datetime) -> bool:
    """Return True when ``moment`` belongs to the window delimited by ``start`` and ``end``."""
    return start <= moment <= end
