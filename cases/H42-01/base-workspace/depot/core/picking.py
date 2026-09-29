"""Pick lists."""

from __future__ import annotations

from dataclasses import dataclass, field

from depot.core.orders import Order


@dataclass(frozen=True)
class PickEntry:
    sku: str
    quantity: int
    location: str

    def to_primitives(self) -> dict:
        return {"sku": self.sku, "quantity": self.quantity, "location": self.location}


@dataclass
class PickList:
    order_id: str
    entries: list[PickEntry] = field(default_factory=list)

    @property
    def units(self) -> int:
        return sum(entry.quantity for entry in self.entries)

    def to_primitives(self) -> dict:
        return {"orderId": self.order_id, "entries": [e.to_primitives() for e in self.entries]}


def build_pick_list(order: Order, locations: dict[str, str]) -> PickList:
    """Build a walk-ordered pick list; unknown skus default to location ``UNASSIGNED``."""
    entries = [
        PickEntry(
            sku=line.sku.value,
            quantity=line.quantity,
            location=locations.get(line.sku.value, "UNASSIGNED"),
        )
        for line in order.lines
    ]
    entries.sort(key=lambda entry: (entry.location, entry.sku))
    return PickList(order_id=order.identifier.value, entries=entries)
