"""Listing helpers for the bundled mini-project."""

from __future__ import annotations

from repository import all_records

DEFAULT_PAGE_SIZE = 20


def list_records() -> list[dict[str, str]]:
    """Return the listing shown on the dashboard."""
    return all_records()[:DEFAULT_PAGE_SIZE]
