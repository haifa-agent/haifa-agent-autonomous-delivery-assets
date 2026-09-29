"""Replenishment suggestions derived from stock levels and supplier lead times."""

from __future__ import annotations

from dataclasses import dataclass

from depot.core.catalog import Catalog
from depot.core.inventory import Inventory, StockItem
from depot.core.supplier import Supplier, SupplierDirectory


@dataclass(frozen=True)
class ReorderSuggestion:
    sku: str
    quantity: int
    supplier_id: str
    lead_time_days: int
    estimated_cost: str

    def to_primitives(self) -> dict:
        return {
            "sku": self.sku,
            "quantity": self.quantity,
            "supplierId": self.supplier_id,
            "leadTimeDays": self.lead_time_days,
            "estimatedCost": self.estimated_cost,
        }


def _deficit(item: StockItem) -> int:
    return max(0, item.reorder_point + item.safety_stock - item.on_hand)


def _choose(suppliers: SupplierDirectory, sku: str, supplier: str | None) -> Supplier | None:
    if supplier is None:
        return suppliers.fastest_for(sku)
    wanted = supplier.strip().upper()
    candidates = [entry for entry in suppliers.for_sku(sku) if entry.identifier.value == wanted]
    if not candidates:
        return None
    return min(candidates, key=lambda entry: (entry.lead_time_days, entry.identifier.value))


def suggestions(
    inventory: Inventory,
    suppliers: SupplierDirectory,
    catalog: Catalog,
    *,
    supplier: str | None = None,
) -> list[ReorderSuggestion]:
    result: list[ReorderSuggestion] = []
    for item in inventory.all():
        deficit = _deficit(item)
        if deficit <= 0:
            continue
        chosen = _choose(suppliers, item.sku, supplier)
        if chosen is None:
            continue
        quantity = max(deficit, chosen.minimum_order_quantity)
        product = catalog.find(item.sku)
        cost = product.unit_price.scale(quantity).as_decimal() if product is not None else "0.00"
        result.append(
            ReorderSuggestion(
                sku=item.sku,
                quantity=quantity,
                supplier_id=chosen.identifier.value,
                lead_time_days=chosen.lead_time_days,
                estimated_cost=cost,
            )
        )
    result.sort(key=lambda suggestion: suggestion.sku)
    return result
