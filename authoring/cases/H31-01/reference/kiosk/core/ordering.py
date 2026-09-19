"""The orders a catalogue listing can be sorted by."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from kiosk.core.catalog import Item
from kiosk.core.errors import CatalogError


@dataclass(frozen=True)
class Order:
    """One named catalogue order: how to read its value and in which direction it runs."""

    name: str
    value_of: Callable[[Item], object]
    descending: bool = False


ORDERS: dict[str, Order] = {
    "name": Order("name", lambda item: item.name.lower()),
    "sku": Order("sku", lambda item: item.sku),
    "price": Order("price", lambda item: item.price_cents),
    "popularity": Order("popularity", lambda item: item.popularity, descending=True),
}

# The order a listing uses when the caller does not name one.
DEFAULT_ORDER = "popularity"


def resolve(order: str | None) -> Order:
    """Return the named order, or the default one when ``order`` is None."""
    name = DEFAULT_ORDER if order is None else order
    try:
        return ORDERS[name]
    except KeyError as error:
        raise CatalogError(f"unknown order: {name}") from error


def sort_key(order: str | None = None) -> Callable[[Item], tuple]:
    """Return the sort key of one order.

    Two items with the same order value are separated by their sku, so that a listing has exactly
    one possible sequence and a reader can resume it from any position.
    """
    resolved = resolve(order)

    def key(item: Item) -> tuple:
        value = resolved.value_of(item)
        if resolved.descending:
            return (-_as_number(value), item.sku)
        return (value, item.sku)

    return key


def sort_items(items: list[Item], order: str | None = None) -> list[Item]:
    """Return ``items`` sorted by the named order without touching the input list."""
    return sorted(items, key=sort_key(order))


def _as_number(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    raise CatalogError("a descending order must sort by a number")
