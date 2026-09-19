"""How a field value is rendered when it leaves the product.

Every exporter renders values through these helpers, so that two export formats of the same
catalogue never disagree about a missing value, an over-long name or a timestamp.
"""

from __future__ import annotations

from datetime import datetime, timezone

# A field the catalogue does not carry is exported as this placeholder, never as an empty cell.
MISSING = "-"
# Names longer than this are shortened; the cut is always marked.
NAME_LIMIT = 40
ELLIPSIS = "..."


def present(value: object) -> str:
    """Render one field value; a missing or blank value becomes :data:`MISSING`."""
    if value is None:
        return MISSING
    text = str(value)
    return text if text.strip() else MISSING


def clip(text: str, limit: int = NAME_LIMIT) -> str:
    """Shorten ``text`` to ``limit`` characters, marking the cut with :data:`ELLIPSIS`."""
    if limit < len(ELLIPSIS):
        raise ValueError("limit must leave room for the ellipsis")
    if len(text) <= limit:
        return text
    return text[: limit - len(ELLIPSIS)] + ELLIPSIS


def iso_utc(epoch_millis: int) -> str:
    """Render epoch milliseconds as a UTC timestamp.

    Exports are read on machines in other time zones than the kiosk, so an exported timestamp is
    always UTC and never the local time of the exporting host.
    """
    moment = datetime.fromtimestamp(int(epoch_millis) / 1000, tz=timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")
