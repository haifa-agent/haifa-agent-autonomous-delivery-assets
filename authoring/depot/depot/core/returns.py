"""Returns and their disposition."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from depot.core.errors import ValidationError


class ReturnReason(StrEnum):
    DAMAGED = "DAMAGED"
    WRONG_ITEM = "WRONG_ITEM"
    UNSOLD = "UNSOLD"
    CUSTOMER_CHANGE = "CUSTOMER_CHANGE"


class Disposition(StrEnum):
    RESTOCK = "RESTOCK"
    REPAIR = "REPAIR"
    SCRAP = "SCRAP"


@dataclass(frozen=True)
class ReturnRequest:
    identifier: str
    order_id: str
    sku: str
    quantity: int
    reason: ReturnReason

    def __post_init__(self) -> None:
        if self.quantity < 1:
            raise ValidationError("return quantity must be at least 1", sku=self.sku)


def disposition_for(reason: ReturnReason, *, resellable: bool, repairable: bool) -> Disposition:
    if reason is ReturnReason.WRONG_ITEM:
        return Disposition.RESTOCK
    if reason is ReturnReason.UNSOLD:
        return Disposition.RESTOCK
    if reason is ReturnReason.CUSTOMER_CHANGE:
        return Disposition.RESTOCK if resellable else Disposition.SCRAP
    # Damaged goods are repaired when possible, otherwise scrapped.
    if repairable:
        return Disposition.REPAIR
    return Disposition.SCRAP


def apply_disposition(request: ReturnRequest, disposition: Disposition, inventory) -> None:
    if disposition is Disposition.RESTOCK:
        inventory.receive(request.sku, request.quantity)
