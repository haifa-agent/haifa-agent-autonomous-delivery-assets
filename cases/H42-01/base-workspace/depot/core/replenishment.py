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


def suggestions(
    inventory: Inventory,
    suppliers: SupplierDirectory,
    catalog: Catalog,
) -> list[ReorderSuggestion]:
    result: list[ReorderSuggestion] = []
    for item in inventory.all():
        deficit = _deficit(item)
        if deficit <= 0:
            continue
        supplier: Supplier | None = suppliers.fastest_for(item.sku)
        if supplier is None:
            continue
        quantity = max(deficit, supplier.minimum_order_quantity)
        product = catalog.find(item.sku)
        cost = product.unit_price.scale(quantity).as_decimal() if product is not None else "0.00"
        result.append(
            ReorderSuggestion(
                sku=item.sku,
                quantity=quantity,
                supplier_id=supplier.identifier.value,
                lead_time_days=supplier.lead_time_days,
                estimated_cost=cost,
            )
        )
    result.sort(key=lambda suggestion: suggestion.sku)
    return result
