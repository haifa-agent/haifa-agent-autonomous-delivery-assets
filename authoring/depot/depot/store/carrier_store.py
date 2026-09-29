"""Carrier persistence."""

from __future__ import annotations

from pathlib import Path

from depot.core.errors import FormatError
from depot.core.shipping import Carrier, CarrierBoard
from depot.store.json_store import read_json


def load_carriers(path: Path) -> CarrierBoard:
    payload = read_json(path)
    if not isinstance(payload, dict) or "carriers" not in payload:
        raise FormatError(f"{path.name} must be an object with a carriers list", file=path.name)
    return CarrierBoard([Carrier.from_primitives(item) for item in payload["carriers"]])
