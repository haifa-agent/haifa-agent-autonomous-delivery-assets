"""Bin locations per sku."""

from __future__ import annotations

from pathlib import Path

from depot.core.errors import FormatError
from depot.store.json_store import read_json


def load_locations(path: Path) -> dict[str, str]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise FormatError(f"{path.name} must be an object", file=path.name)
    locations = payload.get("locations", payload)
    if not isinstance(locations, dict):
        raise FormatError(f"{path.name} locations must be an object", file=path.name)
    return {str(sku): str(bin_name) for sku, bin_name in locations.items()}
