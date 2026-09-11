"""Record search helpers for the bundled mini-project."""

from __future__ import annotations


def matches(query: str, records: list[str]) -> list[str]:
    """Return the records that contain ``query``."""
    if not query:
        return []
    return [record for record in records if query in record]