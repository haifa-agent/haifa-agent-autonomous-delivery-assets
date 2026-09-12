"""Pricing helpers for the bundled mini-project."""

from __future__ import annotations

import warnings


def calculate(total: float, discount: float) -> float:
    """Return the discounted total, never below zero, rounded to cents."""
    if discount < 0:
        raise ValueError("discount must not be negative")
    return round(max(total - discount, 0.0), 2)


def calc(x: float, y: float) -> float:
    """Deprecated alias of :func:`calculate`; ``x`` is the total and ``y`` the discount."""
    warnings.warn("pricing.calc is deprecated; use pricing.calculate instead", DeprecationWarning, stacklevel=2)
    return calculate(x, y)
