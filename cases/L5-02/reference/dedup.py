"""Deduplication helpers for the bundled mini-project."""

from __future__ import annotations


def deduplicate(records: list[str]) -> list[str]:
    """Return the unique records in first-seen order."""
    return list(dict.fromkeys(records))