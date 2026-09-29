"""Tax table persistence."""

from __future__ import annotations

from pathlib import Path

from depot.core.errors import FormatError
from depot.core.tax import TaxTable
from depot.store.json_store import read_json


def load_tax_table(path: Path) -> TaxTable:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise FormatError(f"{path.name} must be an object", file=path.name)
    return TaxTable.from_primitives(payload)
