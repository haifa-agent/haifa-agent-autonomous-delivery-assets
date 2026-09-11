"""Listing helpers for the bundled mini-project."""

from __future__ import annotations

from repository import page

DEFAULT_PAGE_SIZE = 20


def list_records(page_size: int = DEFAULT_PAGE_SIZE) -> list[str]:
    """Return the requested page of records in the frozen default order."""
    return page(page_size)