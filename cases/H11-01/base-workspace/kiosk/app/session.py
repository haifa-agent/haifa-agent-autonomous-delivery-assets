"""One customer session at the kiosk."""

from __future__ import annotations

from kiosk.app.audit import AuditTrail
from kiosk.app.cart_service import Cart, build_cart
from kiosk.app.repository import CatalogRepository
from kiosk.core.errors import ValidationError


class Session:
    """The selection a customer built up, and the cart it prices to."""

    def __init__(self, repository: CatalogRepository, trail: AuditTrail | None = None) -> None:
        self._repository = repository
        self._trail = trail if trail is not None else AuditTrail()
        self._selection: dict[str, int] = {}

    @property
    def selection(self) -> dict[str, int]:
        """Return a copy of the current selection."""
        return dict(self._selection)

    def add(self, sku: str, quantity: int = 1) -> None:
        """Add ``quantity`` of ``sku`` to the selection."""
        if quantity < 1:
            raise ValidationError("quantity must be positive")
        item = self._repository.find(sku)
        self._selection[item.sku] = self._selection.get(item.sku, 0) + quantity
        self._trail.record("add", item.sku, str(quantity))

    def remove(self, sku: str, quantity: int = 1) -> None:
        """Remove ``quantity`` of ``sku``; the line disappears once nothing is left of it."""
        if sku not in self._selection:
            raise ValidationError(f"{sku} is not in the selection")
        remaining = self._selection[sku] - quantity
        if remaining > 0:
            self._selection[sku] = remaining
        else:
            del self._selection[sku]
        self._trail.record("remove", sku, str(quantity))

    def clear(self) -> None:
        """Drop the whole selection."""
        self._selection.clear()
        self._trail.record("clear", "-")

    def checkout(self) -> Cart:
        """Price the current selection."""
        cart = build_cart(self._repository, self._selection)
        self._trail.record("checkout", "-", str(cart.total.total_cents))
        return cart
