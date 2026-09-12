"""Pricing helpers for the bundled mini-project."""

from __future__ import annotations


def calc(x: float, y: float) -> float:
    """Return the discounted total: ``x`` is the order total and ``y`` the discount."""
    if y < 0:
        raise ValueError("discount must not be negative")
    return round(max(x - y, 0.0), 2)
