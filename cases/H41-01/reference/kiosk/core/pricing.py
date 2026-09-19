"""Cart arithmetic: line totals, the subtotal and the discounted total."""

from __future__ import annotations

from dataclasses import dataclass

from kiosk.core.discount_tiers import TIERS, discount_of, tier_for
from kiosk.core.errors import ValidationError


@dataclass(frozen=True)
class Line:
    """One cart line: a quantity of one item at the price it was added for."""

    sku: str
    unit_price_cents: int
    quantity: int


@dataclass(frozen=True)
class Total:
    """What a cart costs: before the discount, the discount itself, and after it."""

    subtotal_cents: int
    discount_cents: int
    total_cents: int


def line_total(line: Line) -> int:
    """Return what one cart line costs."""
    if line.quantity < 0:
        raise ValidationError("quantity must not be negative")
    if line.unit_price_cents < 0:
        raise ValidationError("unit_price_cents must not be negative")
    return line.unit_price_cents * line.quantity


def subtotal(lines: list[Line]) -> int:
    """Return what the cart costs before any discount."""
    return sum(line_total(line) for line in lines)


def apply_discounts(subtotal_cents: int, tiers: tuple[tuple[int, int], ...] = TIERS) -> int:
    """Return the discount ``subtotal_cents`` earns, in whole cents."""
    if subtotal_cents < 0:
        raise ValidationError("subtotal must not be negative")
    return discount_of(subtotal_cents, tier_for(subtotal_cents, tiers))


def cart_total(lines: list[Line], tiers: tuple[tuple[int, int], ...] = TIERS) -> Total:
    """Return the full price breakdown of a cart.

    The discount is the percent of the subtotal that its tier earns, rounded down to whole cents.
    """
    gross = subtotal(lines)
    discount = apply_discounts(gross, tiers)
    return Total(subtotal_cents=gross, discount_cents=discount, total_cents=gross - discount)
