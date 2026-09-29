"""Order pricing: subtotal, discounts, tax and total."""

from __future__ import annotations

from dataclasses import dataclass, field

from depot.core.catalog import Catalog
from depot.core.discounts import DiscountResult, DiscountRule, apply_discounts
from depot.core.money import Money
from depot.core.orders import Order
from depot.core.tax import TaxTable


@dataclass(frozen=True)
class OrderPricing:
    subtotal: Money
    discount: Money
    taxable: Money
    tax: Money
    total: Money
    applied: list[str] = field(default_factory=list)

    def to_primitives(self) -> dict:
        return {
            "subtotal": self.subtotal.as_decimal(),
            "discount": self.discount.as_decimal(),
            "taxable": self.taxable.as_decimal(),
            "tax": self.tax.as_decimal(),
            "total": self.total.as_decimal(),
            "applied": list(self.applied),
        }


def price_order(
    order: Order,
    catalog: Catalog,
    taxes: TaxTable,
    rules: list[DiscountRule] | None = None,
    *,
    region: str | None = None,
) -> OrderPricing:
    subtotal = order.subtotal
    discount_result: DiscountResult = apply_discounts(order, catalog, rules or [])
    taxable = subtotal - discount_result.total
    if taxable.is_negative():
        taxable = Money(0)
    rate_region = region or order.warehouse
    tax = taxes.tax_for(taxable, rate_region)
    return OrderPricing(
        subtotal=subtotal,
        discount=discount_result.total,
        taxable=taxable,
        tax=tax,
        total=taxable + tax,
        applied=discount_result.applied,
    )
