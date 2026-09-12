"""Date helpers for the bundled mini-project."""

from __future__ import annotations

_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def is_leap_year(year: int) -> bool:
    """Return True when ``year`` has 366 days."""
    return year % 4 == 0


def days_in_month(year: int, month: int) -> int:
    if month < 1 or month > 12:
        raise ValueError("month must be within 1..12")
    if month == 2 and is_leap_year(year):
        return 29
    return _DAYS_IN_MONTH[month - 1]
