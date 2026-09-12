"""In-memory record repository for the bundled mini-project."""

from __future__ import annotations


def _seed() -> dict[str, dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    for index in range(60):
        number = (index * 37) % 97 + 1
        record_id = f"rec-{number:03d}"
        records[record_id] = {"id": record_id, "name": f"Record {number}"}
    return records


_RECORDS = _seed()


def all_records() -> list[dict[str, str]]:
    """Return copies of every record, in creation order."""
    return [dict(record) for record in _RECORDS.values()]


def sorted_by_id() -> list[dict[str, str]]:
    """Return copies of every record sorted by id (used by the admin export)."""
    return sorted(all_records(), key=lambda record: record["id"])
