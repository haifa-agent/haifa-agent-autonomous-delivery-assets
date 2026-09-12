"""CSV import for the inventory tool."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from pathlib import Path

HEADER = ["sku", "name", "quantity"]


class ImportAborted(Exception):
    """The import cannot run at all; reported on stderr with exit code 2."""


@dataclass(frozen=True)
class RowOutcome:
    line: int
    sku: str | None
    item: dict[str, object] | None
    reason: str | None


def read_rows(path: Path) -> list[RowOutcome]:
    """Parse ``path`` and validate every data row; raise ``ImportAborted`` when the file is unusable."""
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as error:
        raise ImportAborted(f"cannot read {path}: {error}") from error
    reader = csv.reader(io.StringIO(text, newline=""))
    header = next(reader, None)
    if header != HEADER:
        raise ImportAborted(f"unexpected header {header!r}, expected {','.join(HEADER)}")
    outcomes: list[RowOutcome] = []
    for row in reader:
        if not row:
            continue
        outcomes.append(_validate(reader.line_num, row))
    return outcomes


def _validate(line: int, row: list[str]) -> RowOutcome:
    if len(row) != len(HEADER):
        return RowOutcome(line, None, None, f"expected {len(HEADER)} fields, got {len(row)}")
    sku, name, quantity = (value.strip() for value in row)
    if not sku:
        return RowOutcome(line, None, None, "empty sku")
    if not name:
        return RowOutcome(line, sku, None, "empty name")
    if not quantity.isdigit():
        return RowOutcome(line, sku, None, f"quantity is not a non-negative integer: {quantity!r}")
    return RowOutcome(line, sku, {"sku": sku, "name": name, "quantity": int(quantity)}, None)
