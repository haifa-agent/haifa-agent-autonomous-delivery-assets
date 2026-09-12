"""Listing helpers for the bundled mini-project."""

from __future__ import annotations

from repository import all_records

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def list_records(page_size: int = DEFAULT_PAGE_SIZE) -> list[dict[str, str]]:
    """Return the listing shown on the dashboard, limited to ``page_size`` records."""
    if isinstance(page_size, bool) or not isinstance(page_size, int) or not 1 <= page_size <= MAX_PAGE_SIZE:
        raise ValueError(f"page_size must be an integer within 1..{MAX_PAGE_SIZE}")
    return all_records()[:page_size]
