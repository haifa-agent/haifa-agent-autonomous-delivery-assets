"""Order validation against an explicit policy."""

from __future__ import annotations

from dataclasses import dataclass, field

from depot.core.catalog import Catalog
from depot.core.orders import Order


@dataclass(frozen=True)
class OrderPolicy:
    max_lines: int = 50
    max_units_per_line: int = 500
    allowed_warehouses: tuple[str, ...] = ()
    require_active_products: bool = True


def validate_order(order: Order, catalog: Catalog, policy: OrderPolicy) -> list[str]:
    """Return a sorted list of human-readable problems; empty means the order is acceptable."""
    problems: list[str] = []
    if len(order.lines) > policy.max_lines:
        problems.append(f"order has {len(order.lines)} lines, the maximum is {policy.max_lines}")
    if policy.allowed_warehouses and order.warehouse not in policy.allowed_warehouses:
        problems.append(f"warehouse {order.warehouse} is not allowed")
    for line in order.lines:
        if line.quantity > policy.max_units_per_line:
            problems.append(
                f"{line.sku.value} orders {line.quantity} units, the maximum per line is "
                f"{policy.max_units_per_line}"
            )
        product = catalog.find(line.sku.value)
        if product is None:
            problems.append(f"{line.sku.value} is not in the catalogue")
        elif policy.require_active_products and not product.active:
            problems.append(f"{line.sku.value} is not active")
    return sorted(problems)
