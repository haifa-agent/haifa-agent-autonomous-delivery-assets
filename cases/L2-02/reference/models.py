"""Order domain for the bundled mini-project."""

from __future__ import annotations

from enum import Enum


class OrderStatus(str, Enum):
    NEW = "NEW"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    FINISHED = "FINISHED"
    CANCELLED = "CANCELLED"