"""Pricing helpers for the bundled mini-project."""

from __future__ import annotations


def calculate(total: float, discount: float) -> float:
    """Return the discounted total."""
    return round(total - discount, 2)


def calc(x: float, y: float) -> float:
    """Deprecated alias of :func:`calculate`."""
    return calculate(x, y)