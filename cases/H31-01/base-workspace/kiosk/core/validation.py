"""What makes an ingest row acceptable."""

from __future__ import annotations

from kiosk.core.catalog import REQUIRED_FIELDS

MAX_NAME_LENGTH = 120


def rejection_reason(row: dict[str, object]) -> str | None:
    """Return why ``row`` cannot be ingested, or None when it is acceptable."""
    for name in REQUIRED_FIELDS:
        if name not in row:
            return f"missing field: {name}"
    if not str(row["sku"]).strip():
        return "empty sku"
    name = str(row["name"]).strip()
    if not name:
        return "empty name"
    if len(name) > MAX_NAME_LENGTH:
        return f"name longer than {MAX_NAME_LENGTH} characters"
    try:
        price = int(row["price_cents"])  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "price_cents is not an integer"
    if price < 0:
        return "negative price_cents"
    return None


def is_acceptable(row: dict[str, object]) -> bool:
    """Return whether ``row`` can be ingested."""
    return rejection_reason(row) is None
