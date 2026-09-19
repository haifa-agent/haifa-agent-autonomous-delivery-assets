"""The discount tiers of the kiosk and the arithmetic that applies them."""

from __future__ import annotations

# (minimum order value in cents, discount in percent), ascending by minimum.
TIERS: tuple[tuple[int, int], ...] = (
    (0, 0),
    (5_000, 5),
    (20_000, 10),
    (50_000, 15),
)


def tier_for(amount_cents: int, tiers: tuple[tuple[int, int], ...] = TIERS) -> int:
    """Return the discount percent that ``amount_cents`` earns.

    A tier starts at its minimum: an order of exactly the minimum already earns that tier.
    """
    percent = 0
    for minimum, value in tiers:
        if amount_cents > minimum:
            percent = value
    return percent


def discount_of(amount_cents: int, percent: int) -> int:
    """Return ``percent`` of ``amount_cents``, rounded down to whole cents.

    Rounding down keeps the discount from ever exceeding the tier the customer earned.
    """
    if percent < 0:
        raise ValueError("percent must not be negative")
    return amount_cents * percent // 100
