"""Filtering the catalogue before it is listed."""

from __future__ import annotations

from dataclasses import dataclass

from kiosk.core.catalog import Item
from kiosk.core.errors import ValidationError
from kiosk.core.text import contains_all, normalize, tokens


@dataclass(frozen=True)
class Query:
    """What a customer asked the catalogue for."""

    text: str | None = None
    tag: str | None = None
    max_price_cents: int | None = None

    def is_empty(self) -> bool:
        return self.text is None and self.tag is None and self.max_price_cents is None


def _haystack(item: Item) -> str:
    return normalize(" ".join([item.sku, item.name, item.supplier or "", *item.tags]))


def matches(item: Item, query: Query) -> bool:
    """Return whether ``item`` satisfies every part of ``query``."""
    if query.max_price_cents is not None and item.price_cents > query.max_price_cents:
        return False
    if query.tag is not None and normalize(query.tag) not in {normalize(tag) for tag in item.tags}:
        return False
    if query.text is not None and not contains_all(_haystack(item), tokens(query.text)):
        return False
    return True


def filter_items(items: list[Item], query: Query) -> list[Item]:
    """Return the items of ``items`` that satisfy ``query``, in the order they arrived."""
    if query.max_price_cents is not None and query.max_price_cents < 0:
        raise ValidationError("max_price_cents must not be negative")
    if query.is_empty():
        return list(items)
    return [item for item in items if matches(item, query)]
