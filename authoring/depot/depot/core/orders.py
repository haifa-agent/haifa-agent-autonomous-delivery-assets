"""Orders and their state machine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from depot.core.errors import StateError, ValidationError
from depot.core.ids import Identifier, order_id
from depot.core.money import Money
from depot.core.sku import Sku


class OrderStatus(StrEnum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    ALLOCATED = "ALLOCATED"
    PICKING = "PICKING"
    PACKED = "PACKED"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"
    RETURNED = "RETURNED"


#: Allowed forward transitions; cancellation is handled separately.
TRANSITIONS: dict[OrderStatus, tuple[OrderStatus, ...]] = {
    OrderStatus.DRAFT: (OrderStatus.CONFIRMED,),
    OrderStatus.CONFIRMED: (OrderStatus.ALLOCATED,),
    OrderStatus.ALLOCATED: (OrderStatus.PICKING,),
    OrderStatus.PICKING: (OrderStatus.PACKED,),
    OrderStatus.PACKED: (OrderStatus.SHIPPED,),
    OrderStatus.SHIPPED: (OrderStatus.RETURNED,),
    OrderStatus.CANCELLED: (),
    OrderStatus.RETURNED: (),
}

CANCELLABLE = (OrderStatus.DRAFT, OrderStatus.CONFIRMED, OrderStatus.ALLOCATED)


@dataclass
class OrderLine:
    sku: Sku
    quantity: int
    unit_price: Money

    def __post_init__(self) -> None:
        if self.quantity < 1:
            raise ValidationError("order line quantity must be at least 1", sku=self.sku.value)

    @property
    def total(self) -> Money:
        return self.unit_price.scale(self.quantity)

    def to_primitives(self) -> dict:
        return {
            "sku": self.sku.value,
            "quantity": self.quantity,
            "unitPrice": self.unit_price.as_decimal(),
        }

    @classmethod
    def from_primitives(cls, payload: dict) -> OrderLine:
        return cls(
            sku=Sku(str(payload["sku"])),
            quantity=int(payload["quantity"]),
            unit_price=Money.parse(str(payload["unitPrice"])),
        )


@dataclass
class Order:
    identifier: Identifier
    customer: str
    warehouse: str
    status: OrderStatus
    created_at: datetime
    lines: list[OrderLine] = field(default_factory=list)
    note: str | None = None
    discount_code: str | None = None

    @property
    def subtotal(self) -> Money:
        total = Money(0)
        for line in self.lines:
            total = total + line.total
        return total

    def line_for(self, sku: str) -> OrderLine | None:
        wanted = sku.strip().upper()
        for line in self.lines:
            if line.sku.value == wanted:
                return line
        return None

    def add_line(self, line: OrderLine) -> None:
        if self.status is not OrderStatus.DRAFT:
            raise StateError("lines may only be added to a draft order", order=self.identifier.value)
        existing = self.line_for(line.sku.value)
        if existing is not None:
            existing.quantity += line.quantity
            return
        self.lines.append(line)

    def transition(self, target: OrderStatus) -> None:
        if target is OrderStatus.CANCELLED:
            if self.status not in CANCELLABLE:
                raise StateError(
                    f"order {self.identifier.value} cannot be cancelled from {self.status.value}",
                    order=self.identifier.value,
                )
            self.status = target
            return
        if target not in TRANSITIONS.get(self.status, ()):
            raise StateError(
                f"order {self.identifier.value} cannot move from {self.status.value} to {target.value}",
                order=self.identifier.value,
            )
        self.status = target

    def to_primitives(self) -> dict:
        payload = {
            "id": self.identifier.value,
            "customer": self.customer,
            "warehouse": self.warehouse,
            "status": self.status.value,
            "createdAt": self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "lines": [line.to_primitives() for line in self.lines],
        }
        # Optional fields are omitted, never serialized as null (see AGENTS.md).
        if self.note:
            payload["note"] = self.note
        if self.discount_code:
            payload["discountCode"] = self.discount_code
        return payload

    @classmethod
    def from_primitives(cls, payload: dict, created_at: datetime) -> Order:
        return cls(
            identifier=order_id(str(payload["id"])),
            customer=str(payload["customer"]),
            warehouse=str(payload["warehouse"]),
            status=OrderStatus(str(payload["status"])),
            created_at=created_at,
            lines=[OrderLine.from_primitives(line) for line in payload.get("lines", [])],
            note=(payload.get("note") or None),
            discount_code=(payload.get("discountCode") or None),
        )
