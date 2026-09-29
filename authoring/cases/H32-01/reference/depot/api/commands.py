"""Command handlers registered in the shared handler registry."""

from __future__ import annotations

from depot.adapter.registry import HandlerRegistry
from depot.api import schemas
from depot.api.service import DepotService


def build_registry(service: DepotService) -> HandlerRegistry:
    registry = HandlerRegistry()
    registry.register("products", lambda **_: schemas.product_view(service))
    registry.register("orders", lambda **_: {"orders": [o.to_primitives() for o in service.orders]})
    registry.register(
        "price",
        lambda *, order=None, **_: schemas.pricing_view(service, service.find_order(order)),
    )
    registry.register(
        "pick",
        lambda *, order=None, **_: schemas.pick_view(service, service.find_order(order)),
    )
    registry.register(
        "pack",
        lambda *, order=None, **_: schemas.pack_view(service, service.find_order(order)),
    )
    registry.register(
        "ship",
        lambda *, order=None, **_: schemas.shipment_view(service, service.find_order(order)),
    )
    registry.register(
        "reorders",
        lambda *, supplier=None, **_: {
            "suggestions": [
                suggestion.to_primitives()
                for suggestion in service.reorder_suggestions(supplier)
            ]
        },
    )
    registry.register("summary", lambda **_: schemas.summary_view(service))
    return registry
