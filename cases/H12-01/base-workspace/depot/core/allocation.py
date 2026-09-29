"""Stock allocation across an order's lines."""

from __future__ import annotations

from dataclasses import dataclass, field

from depot.core.errors import InsufficientStockError
from depot.core.inventory import Inventory
from depot.core.orders import Order


@dataclass
class Allocation:
    order_id: str
    reserved: dict[str, int] = field(default_factory=dict)

    @property
    def units(self) -> int:
        return sum(self.reserved.values())

    def to_primitives(self) -> dict:
        return {"orderId": self.order_id, "reserved": dict(sorted(self.reserved.items()))}


def allocate(order: Order, inventory: Inventory, *, allow_partial: bool = False) -> Allocation:
    """Reserve every ordered unit. With ``allow_partial`` reserve what is available."""
    shortfalls: list[str] = []
    tentative: list[tuple[str, int]] = []
    for line in order.lines:
        want = line.quantity
        have = inventory.available(line.sku.value)
        if have < want:
            if not allow_partial:
                shortfalls.append(f"{line.sku.value}: want {want}, have {have}")
                continue
        granted = min(want, have)
        tentative.append((line.sku.value, granted))
    if shortfalls:
        raise InsufficientStockError("cannot allocate order: " + "; ".join(shortfalls))
    for sku, quantity in tentative:
        if quantity:
            inventory.get(sku).reserve(quantity)
    return Allocation(order_id=order.identifier.value, reserved={sku: qty for sku, qty in tentative if qty})
