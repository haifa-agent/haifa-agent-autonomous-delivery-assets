"""Which items the kiosk should restock first."""

from __future__ import annotations

from dataclasses import dataclass

from kiosk.core.catalog import Item
from kiosk.core.ordering import sort_items

# An item this popular is worth restocking even when it is expensive.
POPULARITY_FLOOR = 30


@dataclass(frozen=True)
class Suggestion:
    """One restock suggestion and why it was made."""

    sku: str
    name: str
    popularity: int
    reason: str


def suggestions(items: list[Item], limit: int = 5, floor: int = POPULARITY_FLOOR) -> list[Suggestion]:
    """Return at most ``limit`` restock suggestions, most popular first."""
    if limit < 0:
        raise ValueError("limit must not be negative")
    picked = [item for item in sort_items(items, "popularity") if item.popularity >= floor]
    return [
        Suggestion(
            sku=item.sku,
            name=item.name,
            popularity=item.popularity,
            reason="sells well" if item.popularity >= floor * 2 else "steady seller",
        )
        for item in picked[:limit]
    ]
