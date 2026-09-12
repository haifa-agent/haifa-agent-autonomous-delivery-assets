"""JSON serialization for the bundled mini-project."""

from __future__ import annotations

from dto import OrderRequest


def to_json(order: dict[str, object]) -> dict[str, object]:
    """Return the wire representation of ``order``."""
    return {
        "orderId": order["orderId"],
        "total": order["total"],
        "couponCode": order.get("couponCode"),
    }


def from_json(payload: dict[str, object]) -> OrderRequest:
    """Read an order request back from its wire representation."""
    coupon = payload.get("couponCode")
    return OrderRequest(
        order_id=str(payload["orderId"]),
        total=float(payload["total"]),
        coupon_code=None if coupon is None else str(coupon),
    )
