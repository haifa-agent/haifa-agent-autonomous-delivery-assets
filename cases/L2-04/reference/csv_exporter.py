"""CSV exporter for the bundled mini-project."""

from __future__ import annotations

import csv
import io


def export(rows: list[dict[str, object]]) -> str:
    """Serialize ``rows`` as CSV using the first row's keys as the header."""
    if not rows:
        return ""
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().rstrip("\n")