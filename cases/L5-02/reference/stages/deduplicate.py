"""Deduplication stage."""

from __future__ import annotations


def deduplicate(batch: list[dict[str, object]]) -> list[dict[str, object]]:
    """Keep the first record of every id, in input order."""
    seen: set[object] = set()
    kept: list[dict[str, object]] = []
    for record in batch:
        if record["id"] not in seen:
            seen.add(record["id"])
            kept.append(record)
    return kept
