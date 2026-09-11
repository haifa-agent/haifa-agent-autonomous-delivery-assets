"""In-memory repository for the bundled mini-project."""

from __future__ import annotations

RECORDS = [f"record-{index:02d}" for index in range(1, 51)]
MIN_PAGE_SIZE = 1
MAX_PAGE_SIZE = 100


def all_records() -> list[str]:
    """Return every record in the frozen default order."""
    return list(RECORDS)


def page(page_size: int) -> list[str]:
    """Return the first ``page_size`` records of the frozen default order."""
    if page_size < MIN_PAGE_SIZE or page_size > MAX_PAGE_SIZE:
        raise ValueError("page_size must be within 1..100")
    return list(RECORDS[:page_size])