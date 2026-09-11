"""JSON serialization for the bundled mini-project."""

from __future__ import annotations


def to_json(order: dict[str, object]) -> dict[str, object]:
    """Return the wire representation of ``order``."""
    return {
        "orderId": order["orderId"],
        "total": order["total"],
        "couponCode": order.get("coupon_code"),
    }