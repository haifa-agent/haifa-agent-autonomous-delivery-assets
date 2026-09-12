"""Batch import of records into a record sink."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class RecordSink(Protocol):
    def contains(self, record_id: str) -> bool: ...

    def add(self, row: dict[str, str]) -> None: ...


@dataclass
class ImportResult:
    imported: list[dict[str, str]] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def import_rows(rows: list[dict[str, str]], sink: RecordSink) -> ImportResult:
    """Add every row whose id is not yet known; report the ids skipped as duplicates."""
    result = ImportResult()
    for row in rows:
        record_id = str(row["id"])
        if sink.contains(record_id):
            result.skipped.append(record_id)
            continue
        sink.add(row)
        result.imported.append(row)
    return result
