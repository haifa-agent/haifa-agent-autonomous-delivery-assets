"""In-memory repository for the bundled mini-project."""

from __future__ import annotations

RECORDS = [f"record-{index:02d}" for index in range(1, 51)]


def all_records() -> list[str]:
    """Return every record in the frozen default order."""
    return list(RECORDS)