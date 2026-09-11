"""Order status transitions for the bundled mini-project."""

from __future__ import annotations

from models import OrderStatus

_ALLOWED = {
    OrderStatus.NEW: (OrderStatus.PAID, OrderStatus.CANCELLED),
    OrderStatus.PAID: (OrderStatus.SHIPPED, OrderStatus.CANCELLED),
    OrderStatus.SHIPPED: (OrderStatus.FINISHED,),
    OrderStatus.FINISHED: (),
    OrderStatus.CANCELLED: (),
}


def can_transition(current: OrderStatus, target: OrderStatus) -> bool:
    """Return True when ``current`` may move to ``target``."""
    return target in _ALLOWED[current]