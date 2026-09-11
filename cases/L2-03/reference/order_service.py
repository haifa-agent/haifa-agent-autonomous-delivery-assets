"""Order service for the bundled mini-project."""

from __future__ import annotations

from dto import OrderRequest
from serializers import to_json


def create_order(request: OrderRequest) -> dict[str, object]:
    """Create the wire representation of ``request``."""
    return to_json(
        {
            "orderId": request.order_id,
            "total": request.total,
            "coupon_code": request.coupon_code,
        }
    )