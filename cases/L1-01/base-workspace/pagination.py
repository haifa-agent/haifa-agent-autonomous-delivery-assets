"""Pagination helpers for the bundled mini-project."""

from __future__ import annotations


def page_count(total_items: int, size: int) -> int:
    """Return the number of pages needed for ``total_items`` items of ``size`` each."""
    if size <= 0:
        raise ValueError("size must be positive")
    if total_items <= 0:
        return 0
    return (total_items + size - 1) // size


class PageWindow:
    """Stateless result-window slicer used by the mini-project's HTTP layer."""

    @staticmethod
    def slice(items: list[str], page: int, size: int) -> list[str]:
        if size <= 0:
            raise ValueError("size must be positive")
        if page < 1:
            raise ValueError("page must be >= 1")
        start = (page - 1) * size
        if start >= len(items):
            return []
        end = start + size
        if end > len(items):
            start = len(items) - size
        return list(items[start:end])