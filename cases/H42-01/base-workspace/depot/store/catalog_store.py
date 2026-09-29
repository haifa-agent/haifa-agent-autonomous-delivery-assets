"""Catalogue persistence."""

from __future__ import annotations

from pathlib import Path

from depot.core.catalog import Catalog, Product
from depot.core.money import Money
from depot.core.sku import Sku
from depot.core.units import Weight
from depot.store.json_store import read_json


def parse_product(payload: dict) -> Product:
    return Product(
        sku=Sku(str(payload["sku"])),
        name=str(payload["name"]),
        category=str(payload["category"]),
        unit_price=Money.parse(str(payload["unitPrice"])),
        weight=Weight(int(payload.get("weightGrams", 0))),
        active=bool(payload.get("active", True)),
        tags=tuple(payload.get("tags", ())),
    )


def load_catalog(path: Path) -> Catalog:
    payload = read_json(path)
    if not isinstance(payload, dict) or "products" not in payload:
        from depot.core.errors import FormatError

        raise FormatError(f"{path.name} must be an object with a products list", file=path.name)
    return Catalog([parse_product(item) for item in payload["products"]])
