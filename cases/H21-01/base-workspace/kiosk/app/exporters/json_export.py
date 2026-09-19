"""The JSON export of a catalogue listing.

This is the oldest export format of the kiosk; the rules it follows for missing values, long
names and timestamps are the rules every export format follows.
"""

from __future__ import annotations

import json

from kiosk.core.catalog import Item
from kiosk.core.format_rules import MISSING, clip, iso_utc, present

# The exported columns, in the order every format writes them.
FIELDS = ("sku", "name", "price", "updated", "supplier")


def row_of(item: Item) -> dict[str, str]:
    """Render one catalogue item into the exported field values."""
    return {
        "sku": present(item.sku),
        "name": clip(present(item.name)),
        "price": present(f"{item.price_cents / 100:.2f}"),
        "updated": iso_utc(item.updated_at_millis) if item.updated_at_millis else MISSING,
        "supplier": present(item.supplier),
    }


def export_json(items: list[Item]) -> str:
    """Return the JSON export of ``items``."""
    payload = {"fields": list(FIELDS), "items": [row_of(item) for item in items]}
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"
