"""Checkout flow of the bundled mini-project."""

from __future__ import annotations

from pricing import calc


def checkout_total(subtotal: float, voucher: float) -> float:
    """Return the amount charged at checkout."""
    return calc(subtotal, voucher)
