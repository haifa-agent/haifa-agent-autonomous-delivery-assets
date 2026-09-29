"""Suppliers and their lead times."""

from __future__ import annotations

from dataclasses import dataclass, field

from depot.core.errors import NotFoundError, ValidationError
from depot.core.ids import Identifier, supplier_id


@dataclass(frozen=True)
class Supplier:
    identifier: Identifier
    name: str
    lead_time_days: int
    minimum_order_quantity: int
    active: bool = True
    supplies: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.lead_time_days < 0:
            raise ValidationError("lead time must not be negative", supplier=self.identifier.value)
        if self.minimum_order_quantity < 1:
            raise ValidationError("minimum order quantity must be at least 1")

    def can_supply(self, sku: str) -> bool:
        return self.active and (not self.supplies or sku in self.supplies)

    @classmethod
    def from_primitives(cls, payload: dict) -> Supplier:
        return cls(
            identifier=supplier_id(payload["id"]),
            name=payload["name"],
            lead_time_days=int(payload["leadTimeDays"]),
            minimum_order_quantity=int(payload["minimumOrderQuantity"]),
            active=bool(payload.get("active", True)),
            supplies=tuple(payload.get("supplies", ())),
        )

    def to_primitives(self) -> dict:
        return {
            "id": self.identifier.value,
            "name": self.name,
            "leadTimeDays": self.lead_time_days,
            "minimumOrderQuantity": self.minimum_order_quantity,
            "active": self.active,
            "supplies": list(self.supplies),
        }


class SupplierDirectory:
    def __init__(self, suppliers: list[Supplier]) -> None:
        layout: dict[str, Supplier] = {}
        for supplier in suppliers:
            layout[supplier.identifier.value] = supplier
        self._suppliers = tuple(sorted(suppliers, key=lambda item: item.identifier.value))
        self._by_id = layout

    def get(self, identifier: str | Identifier) -> Supplier:
        key = identifier.value if isinstance(identifier, Identifier) else str(identifier)
        supplier = self._by_id.get(key)
        if supplier is None:
            raise NotFoundError(f"unknown supplier: {key}", supplier=key)
        return supplier

    def all(self) -> list[Supplier]:
        return list(self._suppliers)

    def for_sku(self, sku: str) -> list[Supplier]:
        return [
            supplier
            for supplier in self._suppliers
            if supplier.can_supply(sku)
        ]

    def fastest_for(self, sku: str) -> Supplier | None:
        candidates = self.for_sku(sku)
        if not candidates:
            return None
        return min(candidates, key=lambda item: (item.lead_time_days, item.identifier.value))
