"""Batch export entry point."""

from __future__ import annotations

from pipeline_config import build_engine


def export_batch(records: list[dict[str, object]]) -> list[dict[str, object]]:
    """Run ``records`` through the export pipeline and return the exported records."""
    return build_engine().run(records)
