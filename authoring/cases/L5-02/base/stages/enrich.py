"""Enrichment stage."""

from __future__ import annotations


def enrich(batch: list[dict[str, object]]) -> list[dict[str, object]]:
    """Number the exported records consecutively, starting at 1."""
    for position, record in enumerate(batch, start=1):
        record["position"] = position
    return batch
