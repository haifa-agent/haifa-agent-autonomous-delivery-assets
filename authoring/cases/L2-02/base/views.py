"""Summary rendering for the bundled mini-project."""

from __future__ import annotations

from models import OrderStatus

_LABELS = {
    OrderStatus.NEW: "New order",
    OrderStatus.PAID: "Paid",
    OrderStatus.SHIPPED: "Shipped",
    OrderStatus.FINISHED: "Finished",
}


def render(status: OrderStatus) -> str:
    """Return the human readable label for ``status``."""
    return _LABELS[status]
