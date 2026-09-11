"""Conversion metrics for the bundled mini-project."""

from __future__ import annotations


def conversion_rate(clicks: int, visits: int) -> float:
    """Return the conversion ratio rounded to two decimals."""
    if visits <= 0:
        raise ValueError("visits must be positive")
    return round(clicks / visits, 2)