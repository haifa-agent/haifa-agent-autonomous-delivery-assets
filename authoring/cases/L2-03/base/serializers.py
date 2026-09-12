"""JSON serialization for the bundled mini-project."""

from __future__ import annotations

from dto import OrderRequest


def to_json(order: dict[str, object]) -> dict[str, object]:
    """Return the wire representation of ``order``."""
    return {
        "orderId": order["orderId"],
        "total": order["total"],
    }


def from_json(payload: dict[str, object]) -> OrderRequest:
    """Read an order request back from its wire representation."""
    return OrderRequest(order_id=str(payload["orderId"]), total=float(payload["total"]))
