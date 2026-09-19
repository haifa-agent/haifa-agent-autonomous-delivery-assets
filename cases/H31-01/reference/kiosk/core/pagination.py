"""Cursor pagination over an ordered catalogue listing.

A cursor names the last item of the page that was handed out. The next page starts at the first
item that sorts after it, so the listing can be resumed without counting rows.
"""

from __future__ import annotations

import base64
import binascii

from kiosk.core.catalog import Item
from kiosk.core.errors import CursorError
from kiosk.core.ordering import DEFAULT_ORDER, resolve

SEPARATOR = "|"
# Wide enough for any popularity, so that an inverted value never turns negative.
_DESCENDING_CEILING = 10 ** 11


def _cursor_value(item: Item, order: str = DEFAULT_ORDER) -> str:
    """The value a cursor stores.

    Comparing two of these values must give the same answer as the listing order: the next page
    is everything that sorts after the cursor. A number is rendered zero padded so that comparing
    the text compares the number, and a descending order is inverted so that it still runs upwards.
    """
    resolved = resolve(order)
    value = resolved.value_of(item)
    if isinstance(value, (int, float)):
        number = int(value)
        return f"{_DESCENDING_CEILING - number if resolved.descending else number:012d}"
    return str(value)


def encode_cursor(item: Item, order: str = DEFAULT_ORDER) -> str:
    """Encode the position of ``item`` inside a listing ordered by ``order``."""
    raw = SEPARATOR.join((order, _cursor_value(item, order), item.sku))
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")


def decode_cursor(cursor: str) -> tuple[str, str, str]:
    """Return ``(order, value, sku)`` of ``cursor``."""
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError, ValueError) as error:
        raise CursorError("cursor is not readable") from error
    parts = raw.split(SEPARATOR)
    if len(parts) != 3:
        raise CursorError("cursor does not carry order, value and sku")
    return parts[0], parts[1], parts[2]


def _start_of_next_page(items: list[Item], value: str, sku: str, order: str) -> int:
    """Return the index of the first item that sorts after the cursor position."""
    for index, item in enumerate(items):
        if (_cursor_value(item, order), item.sku) > (value, sku):
            return index
    return len(items)


def page(
    items: list[Item], size: int, cursor: str | None = None, order: str = DEFAULT_ORDER
) -> tuple[list[Item], str | None]:
    """Return one page of the already ordered ``items`` and the cursor of the page after it.

    ``cursor`` is what the previous page returned; None starts at the beginning. The returned
    cursor is None once the last page was handed out.
    """
    if size < 1:
        raise ValueError("size must be positive")
    start = 0
    if cursor is not None:
        cursor_order, value, sku = decode_cursor(cursor)
        if cursor_order != order:
            raise CursorError("cursor belongs to another order")
        start = _start_of_next_page(items, value, sku, order)
    window = items[start : start + size]
    if not window or start + size >= len(items):
        return window, None
    return window, encode_cursor(window[-1], order)
