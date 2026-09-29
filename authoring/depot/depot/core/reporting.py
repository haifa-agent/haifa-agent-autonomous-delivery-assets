"""Pure aggregations used by the reports."""

from __future__ import annotations

from depot.core.catalog import Catalog
from depot.core.inventory import Inventory
from depot.core.money import Money
from depot.core.orders import Order, OrderStatus


def status_counts(orders: list[Order]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for order in orders:
        key = order.status.value
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def ordered_units(orders: list[Order]) -> int:
    return sum(line.quantity for order in orders for line in order.lines)


def revenue(orders: list[Order], priced_totals: dict[str, Money]) -> Money:
    total = Money(0)
    for order in orders:
        if order.status in (OrderStatus.CANCELLED, OrderStatus.RETURNED):
            continue
        amount = priced_totals.get(order.identifier.value)
        if amount is not None:
            total = total + amount
    return total


def fill_rate(units_ordered: int, units_shipped: int) -> float:
    if units_ordered <= 0:
        return 1.0
    return round(min(units_shipped, units_ordered) / units_ordered, 4)


def inventory_valuation(inventory: Inventory, catalog: Catalog) -> Money:
    total = Money(0)
    for item in inventory.all():
        product = catalog.find(item.sku)
        if product is None:
            continue
        total = total + product.unit_price.scale(item.on_hand)
    return total


def category_breakdown(orders: list[Order], catalog: Catalog) -> dict[str, Money]:
    totals: dict[str, Money] = {}
    for order in orders:
        for line in order.lines:
            product = catalog.find(line.sku.value)
            category = product.category if product is not None else "UNKNOWN"
            totals[category] = totals.get(category, Money(0)) + line.total
    return {category: totals[category] for category in sorted(totals)}
