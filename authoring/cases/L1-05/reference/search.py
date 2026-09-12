"""Record search helpers for the bundled mini-project."""

from __future__ import annotations


def matches(query: str, records: list[str]) -> list[str]:
    """Return the records that contain ``query`` ignoring ASCII case, in their original order."""
    if not query:
        return []
    needle = query.lower()
    return [record for record in records if needle in record.lower()]
