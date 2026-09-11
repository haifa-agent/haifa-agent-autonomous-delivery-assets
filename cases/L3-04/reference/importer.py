"""Batch import for the bundled mini-project."""

from __future__ import annotations


def import_rows(
    rows: list[dict[str, str]],
    existing: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[str]]:
    """Return the imported rows and the ids that were skipped as duplicates."""
    imported: list[dict[str, str]] = []
    skipped: list[str] = []
    known_ids = {str(row["id"]) for row in existing}
    for row in rows:
        row_id = str(row["id"])
        if row_id in known_ids:
            skipped.append(row_id)
            continue
        known_ids.add(row_id)
        imported.append(row)
    return imported, skipped