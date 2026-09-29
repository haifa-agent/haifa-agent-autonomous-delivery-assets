"""Inventory levels as pure value logic.

``StockItem`` mirrors one row in the warehouse stock table; it never touches a file itself.
"""

from __future__ import annotations

from dataclasses import dataclass

from depot.core.errors import InsufficientStockError, ValidationError


@dataclass
class StockItem:
    sku: str
    on_hand: int
    reserved: int = 0
    reorder_point: int = 0
    safety_stock: int = 0

    def __post_init__(self) -> None:
        if self.on_hand < 0:
            raise ValidationError("on_hand must not be negative", sku=self.sku)
        if self.reserved < 0:
            raise ValidationError("reserved must not be negative", sku=self.sku)
        if self.reserved > self.on_hand:
            raise ValidationError("reserved must not exceed on_hand", sku=self.sku)

    @property
    def available(self) -> int:
        return self.on_hand - self.reserved

    def reserve(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValidationError("reserve quantity must be positive", sku=self.sku)
        if quantity > self.available:
            raise InsufficientStockError(
                f"cannot reserve {quantity} of {self.sku}: only {self.available} available",
                sku=self.sku,
                available=self.available,
            )
        self.reserved += quantity

    def release(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValidationError("release quantity must be positive", sku=self.sku)
        if quantity > self.reserved:
            raise ValidationError("cannot release more than is reserved", sku=self.sku)
        self.reserved -= quantity

    def pick(self, quantity: int) -> None:
        """Remove reserved stock from the shelf once it has been picked."""
        if quantity <= 0:
            raise ValidationError("pick quantity must be positive", sku=self.sku)
        if quantity > self.reserved:
            raise InsufficientStockError("cannot pick more than is reserved", sku=self.sku)
        self.reserved -= quantity
        self.on_hand -= quantity

    def receive(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValidationError("receive quantity must be positive", sku=self.sku)
        self.on_hand += quantity

    def needs_reorder(self) -> bool:
        return self.available + self.reserved <= self.reorder_point

    def to_primitives(self) -> dict:
        return {
            "sku": self.sku,
            "onHand": self.on_hand,
            "reserved": self.reserved,
            "reorderPoint": self.reorder_point,
            "safetyStock": self.safety_stock,
        }

    @classmethod
    def from_primitives(cls, payload: dict) -> StockItem:
        return cls(
            sku=str(payload["sku"]),
            on_hand=int(payload["onHand"]),
            reserved=int(payload.get("reserved", 0)),
            reorder_point=int(payload.get("reorderPoint", 0)),
            safety_stock=int(payload.get("safetyStock", 0)),
        )


class Inventory:
    """A mutable map of sku -> StockItem."""

    def __init__(self, items: list[StockItem]) -> None:
        self._items = {item.sku: item for item in items}

    def get(self, sku: str) -> StockItem:
        item = self._items.get(sku)
        if item is None:
            item = StockItem(sku=sku, on_hand=0)
            self._items[sku] = item
        return item

    def available(self, sku: str) -> int:
        return self.get(sku).available

    def all(self) -> list[StockItem]:
        return list(self._items.values())

    def low_stock(self) -> list[StockItem]:
        return [item for item in self._items.values() if item.needs_reorder()]

    def receive(self, sku: str, quantity: int) -> StockItem:
        item = self.get(sku)
        item.receive(quantity)
        return item
