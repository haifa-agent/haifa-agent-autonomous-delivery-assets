"""Turning a customer selection into a priced cart."""

from __future__ import annotations

from dataclasses import dataclass

from kiosk.app.repository import CatalogRepository
from kiosk.core.errors import ValidationError
from kiosk.core.pricing import Line, Total, cart_total


@dataclass(frozen=True)
class Cart:
    """A priced cart: what was selected and what it costs."""

    lines: list[Line]
    total: Total


def build_cart(repository: CatalogRepository, selection: dict[str, int]) -> Cart:
    """Price ``selection`` (sku to quantity) against the catalogue."""
    lines: list[Line] = []
    for sku in sorted(selection):
        quantity = selection[sku]
        if quantity < 1:
            raise ValidationError(f"quantity of {sku} must be positive")
        item = repository.find(sku)
        lines.append(Line(sku=item.sku, unit_price_cents=item.price_cents, quantity=quantity))
    return Cart(lines=lines, total=cart_total(lines))
