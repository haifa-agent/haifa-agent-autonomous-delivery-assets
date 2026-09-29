"""CSV exchange files with a stable field order."""

from __future__ import annotations

import csv
import io

from depot.core.errors import FormatError


def export_rows(rows: list[dict], fields: list[str]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return buffer.getvalue()


def parse_rows(text: str, fields: list[str]) -> list[dict]:
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames != fields:
        raise FormatError(
            f"unexpected header {reader.fieldnames}, expected {fields}", header=reader.fieldnames
        )
    rows: list[dict] = []
    for number, row in enumerate(reader, start=2):
        if None in row or any(value is None for value in row.values()):
            raise FormatError(f"row {number} has more columns than the header", row=number)
        rows.append({field: (row.get(field) or "") for field in fields})
    return rows
