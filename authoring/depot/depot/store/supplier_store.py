"""Supplier persistence."""

from __future__ import annotations

from pathlib import Path

from depot.core.errors import FormatError
from depot.core.supplier import Supplier, SupplierDirectory
from depot.store.json_store import read_json


def load_suppliers(path: Path) -> SupplierDirectory:
    payload = read_json(path)
    if not isinstance(payload, dict) or "suppliers" not in payload:
        raise FormatError(f"{path.name} must be an object with a suppliers list", file=path.name)
    return SupplierDirectory([Supplier.from_primitives(item) for item in payload["suppliers"]])
