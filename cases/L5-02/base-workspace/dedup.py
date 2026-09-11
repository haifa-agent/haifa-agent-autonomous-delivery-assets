"""Deduplication helpers for the bundled mini-project."""

from __future__ import annotations


def deduplicate(records: list[str]) -> list[str]:
    """Return the unique records in first-seen order."""
    unique: list[str] = []
    for record in records:
        duplicate = False
        for existing in unique:
            if existing == record:
                duplicate = True
                break
        if not duplicate:
            unique.append(record)
    return unique