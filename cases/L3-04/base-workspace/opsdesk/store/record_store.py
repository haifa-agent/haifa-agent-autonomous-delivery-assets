"""In-memory record store used by the batch importer."""

from __future__ import annotations


class RecordStore:
    """Keeps imported records in insertion order and rejects duplicate ids."""

    def __init__(self, rows: list[dict[str, str]] | None = None) -> None:
        self._rows: list[dict[str, str]] = []
        for row in rows or []:
            self.add(row)

    def contains(self, record_id: str) -> bool:
        return any(str(row["id"]) == record_id for row in self._rows)

    def add(self, row: dict[str, str]) -> None:
        record_id = str(row["id"])
        if self.contains(record_id):
            raise ValueError(f"duplicate record id: {record_id}")
        self._rows.append(dict(row))

    def get(self, record_id: str) -> dict[str, str]:
        for row in self._rows:
            if str(row["id"]) == record_id:
                return dict(row)
        raise KeyError(record_id)

    def rows(self) -> list[dict[str, str]]:
        return [dict(row) for row in self._rows]

    def __len__(self) -> int:
        return len(self._rows)
