"""Parcel packing: group ordered units into parcels under a weight ceiling."""

from __future__ import annotations

from dataclasses import dataclass, field

from depot.core.catalog import Catalog
from depot.core.orders import Order
from depot.core.units import Weight


@dataclass
class Parcel:
    units: dict[str, int] = field(default_factory=dict)

    @property
    def total_units(self) -> int:
        return sum(self.units.values())

    def add(self, sku: str, quantity: int) -> None:
        self.units[sku] = self.units.get(sku, 0) + quantity

    def to_primitives(self) -> dict:
        return {"units": dict(sorted(self.units.items()))}


def pack(order: Order, catalog: Catalog, max_weight: Weight) -> list[Parcel]:
    """Greedy first-fit packing in order-line order; a line may span several parcels."""
    parcels: list[Parcel] = []
    current = Parcel()
    current_weight = Weight(0)
    for line in order.lines:
        product = catalog.find(line.sku.value)
        unit_weight = product.weight if product is not None else Weight(0)
        remaining = line.quantity
        while remaining > 0:
            room = max_weight.grams - current_weight.grams
            if unit_weight.grams > 0:
                fit = room // unit_weight.grams
            else:
                fit = remaining
            if fit <= 0:
                parcels.append(current)
                current = Parcel()
                current_weight = Weight(0)
                if unit_weight.grams > max_weight.grams:
                    # An over-weight item still ships in its own parcel.
                    current.add(line.sku.value, remaining)
                    parcels.append(current)
                    current = Parcel()
                    current_weight = Weight(0)
                    remaining = 0
                    break
                continue
            take = min(fit, remaining)
            current.add(line.sku.value, take)
            current_weight = current_weight + Weight(unit_weight.grams * take)
            remaining -= take
    if current.total_units:
        parcels.append(current)
    return parcels
