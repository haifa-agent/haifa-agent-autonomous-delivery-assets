"""The plain-text reports the kiosk prints."""

from __future__ import annotations

from kiosk.app.cart_service import Cart
from kiosk.app.restock import Suggestion
from kiosk.core.catalog import Item
from kiosk.core.format_rules import clip, present


def money(cents: int) -> str:
    """Render whole cents as a decimal amount."""
    return f"{cents / 100:.2f}"


def catalogue_lines(items: list[Item]) -> list[str]:
    """Render a catalogue listing as one line per item."""
    return [f"{item.sku:<10} {clip(present(item.name), 32):<32} {money(item.price_cents):>10}" for item in items]


def receipt_lines(cart: Cart) -> list[str]:
    """Render a priced cart as a receipt."""
    lines = [f"{line.sku:<10} x{line.quantity:<4} {money(line.unit_price_cents * line.quantity):>10}" for line in cart.lines]
    lines.append(f"{'subtotal':<16} {money(cart.total.subtotal_cents):>10}")
    lines.append(f"{'discount':<16} {money(cart.total.discount_cents):>10}")
    lines.append(f"{'total':<16} {money(cart.total.total_cents):>10}")
    return lines


def restock_lines(items: list[Suggestion]) -> list[str]:
    """Render restock suggestions as one line per item."""
    return [f"{item.sku:<10} {clip(present(item.name), 32):<32} {item.popularity:>4}  {item.reason}" for item in items]
