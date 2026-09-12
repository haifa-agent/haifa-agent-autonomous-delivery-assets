"""Normalization stage."""

from __future__ import annotations


def normalize(batch: list[dict[str, object]]) -> list[dict[str, object]]:
    """Trim and lower-case record ids and trim names."""
    for record in batch:
        record["id"] = str(record["id"]).strip().lower()
        record["name"] = str(record.get("name", "")).strip()
    return batch
