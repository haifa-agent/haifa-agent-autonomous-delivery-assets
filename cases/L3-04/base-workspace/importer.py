"""Batch import for the bundled mini-project."""

from __future__ import annotations


def import_rows(
    rows: list[dict[str, str]],
    existing: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[str]]:
    """Return the imported rows and the ids that were skipped as duplicates."""
    imported: list[dict[str, str]] = []
    skipped: list[str] = []
    known = list(existing)
    for row in rows:
        row_id = str(row["id"])
        if any(str(known_row["id"]) == row_id for known_row in known):
            skipped.append(row_id)
            continue
        known.append(row)
        imported.append(row)
    return imported, skipped