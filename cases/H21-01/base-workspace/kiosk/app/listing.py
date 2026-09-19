"""The catalogue listing service."""

from __future__ import annotations

from dataclasses import dataclass

from kiosk.app.cache import FileCache
from kiosk.app.repository import CatalogRepository
from kiosk.core.catalog import Item, by_sku
from kiosk.core.ordering import resolve, sort_items
from kiosk.core.pagination import page
from kiosk.core.search import Query, filter_items

# The listing everybody sees first is the one worth caching.
DEFAULT_LISTING_KEY = "listing:default"
DEFAULT_PAGE_SIZE = 20


@dataclass(frozen=True)
class Page:
    """One page of the catalogue listing."""

    items: list[Item]
    next_cursor: str | None


def default_sku_order(repository: CatalogRepository, cache: FileCache) -> list[str]:
    """Return the sku sequence of the default listing, reusing the cached one when present."""
    cached = cache.get(DEFAULT_LISTING_KEY)
    if isinstance(cached, list):
        return [str(sku) for sku in cached]
    order = [item.sku for item in sort_items(repository.items())]
    cache.put(DEFAULT_LISTING_KEY, order)
    return order


def ordered_items(repository: CatalogRepository, cache: FileCache, order: str | None = None) -> list[Item]:
    """Return every catalogue item in the requested order."""
    items = repository.items()
    if order is not None:
        return sort_items(items, order)
    index = by_sku(items)
    return [index[sku] for sku in default_sku_order(repository, cache) if sku in index]


def list_page(
    repository: CatalogRepository,
    cache: FileCache,
    size: int = DEFAULT_PAGE_SIZE,
    cursor: str | None = None,
    order: str | None = None,
    query: Query | None = None,
) -> Page:
    """Return one page of the catalogue listing, narrowed by ``query`` when one is given."""
    items = ordered_items(repository, cache, order)
    if query is not None:
        items = filter_items(items, query)
    window, next_cursor = page(items, size, cursor, resolve(order).name)
    return Page(items=window, next_cursor=next_cursor)
