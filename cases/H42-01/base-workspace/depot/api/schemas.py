"""Primitive response builders for the command line and the exchange files."""

from __future__ import annotations

from depot.api.service import DepotService
from depot.core.orders import Order
from depot.core.reporting import (
    category_breakdown,
    inventory_valuation,
    ordered_units,
    status_counts,
)


def product_view(service: DepotService) -> dict:
    return {
        "products": [
            {
                "sku": product.sku.value,
                "name": product.name,
                "category": product.category,
                "unitPrice": product.unit_price.as_decimal(),
                "active": product.active,
            }
            for product in service.catalog.all()
        ]
    }


def order_view(order: Order) -> dict:
    return order.to_primitives()


def pricing_view(service: DepotService, order: Order) -> dict:
    pricing = service.pricing(order)
    return {"orderId": order.identifier.value, **pricing.to_primitives()}


def pick_view(service: DepotService, order: Order) -> dict:
    return service.pick_list(order).to_primitives()


def pack_view(service: DepotService, order: Order) -> dict:
    parcels = service.parcels(order)
    return {
        "orderId": order.identifier.value,
        "parcels": [parcel.to_primitives() for parcel in parcels],
    }


def shipment_view(service: DepotService, order: Order) -> dict:
    carrier = service.select_carrier(order)
    total_weight = sum(service._parcel_weight(parcel).grams for parcel in service.parcels(order))
    return {
        "orderId": order.identifier.value,
        "carrier": carrier.code,
        "transitDays": carrier.transit_days,
        "weightGrams": total_weight,
    }


def summary_view(service: DepotService) -> dict:
    orders = service.orders
    counts = status_counts(orders)
    return {
        "orders": len(orders),
        "statusCounts": counts,
        "orderedUnits": ordered_units(orders),
        "inventoryValue": inventory_valuation(service.inventory, service.catalog).as_decimal(),
        "categories": {
            name: amount.as_decimal()
            for name, amount in category_breakdown(orders, service.catalog).items()
        },
    }
