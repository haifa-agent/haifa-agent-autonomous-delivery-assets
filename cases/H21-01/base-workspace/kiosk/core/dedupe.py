"""Dropping repeated rows out of an ingest batch."""

from __future__ import annotations

from kiosk.core.text import normalize


def drop_duplicates(rows: list[dict[str, object]], key: str = "sku") -> list[dict[str, object]]:
    """Return ``rows`` without repeats of ``key``; the first row of a key wins.

    A supplier feed regularly carries the same item twice. Keeping the first occurrence makes an
    import of the same feed produce the same catalogue every time.
    """
    seen: set[str] = set()
    kept: list[dict[str, object]] = []
    for row in rows:
        if key not in row:
            kept.append(row)
            continue
        identity = normalize(row[key])
        if identity in seen:
            continue
        seen.add(identity)
        kept.append(row)
    return kept
