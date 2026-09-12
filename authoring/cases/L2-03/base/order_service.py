"""Order service for the bundled mini-project."""

from __future__ import annotations

from dto import OrderRequest
from serializers import from_json, to_json


def create_order(request: OrderRequest) -> dict[str, object]:
    """Create the wire representation of ``request``."""
    return to_json({"orderId": request.order_id, "total": request.total})


def replay(payload: dict[str, object]) -> dict[str, object]:
    """Re-create an order from a recorded wire payload (used by the retry queue)."""
    return create_order(from_json(payload))
