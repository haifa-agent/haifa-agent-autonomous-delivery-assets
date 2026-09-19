"""The CSV export of a catalogue listing."""

from __future__ import annotations

import csv
import io

from kiosk.app.exporters.json_export import FIELDS, row_of
from kiosk.core.catalog import Item


def export_csv(items: list[Item]) -> str:
    """Return the CSV export of ``items``, header first."""
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(FIELDS)
    for item in items:
        row = row_of(item)
        writer.writerow([row[field] for field in FIELDS])
    return buffer.getvalue()
