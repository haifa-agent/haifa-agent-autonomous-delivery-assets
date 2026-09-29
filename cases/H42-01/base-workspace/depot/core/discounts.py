"""Discount rules.

Discounts are evaluated in a deterministic order (highest priority first, then by name) and only
one percentage rule per ``scope`` may apply; the first match wins.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from depot.core.catalog import Catalog
from depot.core.money import Money
from depot.core.orders import Order


@dataclass(frozen=True)
class DiscountRule:
    name: str
    priority: int = 0
    scope: str = "order"

    def discount_for(self, order: Order, catalog: Catalog, running: Money) -> Money:
        raise NotImplementedError


@dataclass(frozen=True)
class ThresholdDiscount(DiscountRule):
    threshold: Money = Money(0)
    percent: int = 0

    def discount_for(self, order: Order, catalog: Catalog, running: Money) -> Money:
        if order.subtotal < self.threshold:
            return Money(0)
        return order.subtotal.apply_rate(self.percent, 100, rounding="half_up")


@dataclass(frozen=True)
class CategoryDiscount(DiscountRule):
    category: str = ""
    percent: int = 0

    def discount_for(self, order: Order, catalog: Catalog, running: Money) -> Money:
        base = Money(0)
        for line in order.lines:
            product = catalog.find(line.sku.value)
            if product is not None and product.category.lower() == self.category.lower():
                base = base + line.total
        return base.apply_rate(self.percent, 100, rounding="half_up")


@dataclass(frozen=True)
class PromoCodeDiscount(DiscountRule):
    code: str = ""
    amount: Money = Money(0)

    def discount_for(self, order: Order, catalog: Catalog, running: Money) -> Money:
        return self.amount


@dataclass(frozen=True)
class DiscountResult:
    total: Money = Money(0)
    applied: list[str] = field(default_factory=list)


def apply_discounts(order: Order, catalog: Catalog, rules: list[DiscountRule]) -> DiscountResult:
    ordered = sorted(rules, key=lambda rule: (-rule.priority, rule.name))
    used_scopes: set[str] = set()
    running = Money(0)
    applied: list[str] = []
    for rule in ordered:
        if rule.scope in used_scopes:
            continue
        value = rule.discount_for(order, catalog, running)
        if value.cents <= 0:
            continue
        if running + value > order.subtotal:
            value = order.subtotal - running
        running = running + value
        used_scopes.add(rule.scope)
        applied.append(rule.name)
        if running == order.subtotal:
            break
    return DiscountResult(total=running, applied=applied)
