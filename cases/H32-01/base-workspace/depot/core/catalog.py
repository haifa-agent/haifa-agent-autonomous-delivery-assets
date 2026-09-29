"""Product catalogue domain."""

from __future__ import annotations

from dataclasses import dataclass, field

from depot.core.errors import NotFoundError, ValidationError
from depot.core.money import Money
from depot.core.sku import Sku
from depot.core.units import Weight


@dataclass(frozen=True)
class Product:
    sku: Sku
    name: str
    category: str
    unit_price: Money
    weight: Weight
    active: bool = True
    tags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("product name must not be empty", sku=self.sku.value)
        if not self.category.strip():
            raise ValidationError("product category must not be empty", sku=self.sku.value)

    def with_price(self, price: Money) -> Product:
        return Product(
            sku=self.sku,
            name=self.name,
            category=self.category,
            unit_price=price,
            weight=self.weight,
            active=self.active,
            tags=self.tags,
        )

    def published(self) -> tuple[str, ...]:
        return (self.sku.value, self.name, self.category, self.unit_price.as_decimal())


class Catalog:
    """An immutable, indexed view over a set of products."""

    def __init__(self, products: list[Product]) -> None:
        by_sku: dict[str, Product] = {}
        for product in products:
            if product.sku.value in by_sku:
                raise ValidationError(f"duplicate sku in catalogue: {product.sku.value}")
            by_sku[product.sku.value] = product
        self._products = tuple(sorted(products, key=lambda item: item.sku.value))
        self._by_sku = by_sku

    def get(self, sku: str | Sku) -> Product:
        key = sku.value if isinstance(sku, Sku) else str(sku).strip().upper()
        product = self._by_sku.get(key)
        if product is None:
            raise NotFoundError(f"unknown product: {key}", sku=key)
        return product

    def find(self, sku: str | Sku) -> Product | None:
        key = sku.value if isinstance(sku, Sku) else str(sku).strip().upper()
        return self._by_sku.get(key)

    def all(self) -> list[Product]:
        return list(self._products)

    def active(self) -> list[Product]:
        return [product for product in self._products if product.active]

    def by_category(self, category: str) -> list[Product]:
        wanted = category.strip().lower()
        return [product for product in self._products if product.category.lower() == wanted]

    def search(self, term: str) -> list[Product]:
        needle = term.strip().lower()
        if not needle:
            return []
        return [
            product
            for product in self._products
            if needle in product.name.lower() or any(needle in tag.lower() for tag in product.tags)
        ]

    def __len__(self) -> int:
        return len(self._products)
