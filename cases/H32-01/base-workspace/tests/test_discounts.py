import unittest
from datetime import UTC, datetime

from depot.core.catalog import Catalog, Product
from depot.core.discounts import (
    CategoryDiscount,
    PromoCodeDiscount,
    ThresholdDiscount,
    apply_discounts,
)
from depot.core.ids import order_id
from depot.core.money import Money
from depot.core.orders import Order, OrderLine, OrderStatus
from depot.core.sku import Sku
from depot.core.units import Weight


def catalog():
    return Catalog(
        [
            Product(Sku("BEV-1001"), "Coffee", "beverages", Money.parse("10.00"), Weight(1)),
            Product(Sku("SNA-2001"), "Almonds", "snacks", Money.parse("5.00"), Weight(1)),
        ]
    )


def order(lines, status=OrderStatus.DRAFT):
    return Order(
        identifier=order_id("O-000101"),
        customer="Acme",
        warehouse="WH-CEN",
        status=status,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        lines=[OrderLine(Sku(sku), qty, Money.parse(price)) for sku, qty, price in lines],
    )


class DiscountTest(unittest.TestCase):
    def test_threshold(self):
        subject = order([("BEV-1001", 6, "10.00")])
        result = apply_discounts(subject, catalog(), [ThresholdDiscount("bulk", threshold=Money.parse("50.00"), percent=10)])
        self.assertEqual(Money.parse("6.00"), result.total)
        self.assertEqual(["bulk"], result.applied)

    def test_threshold_does_not_apply_below(self):
        subject = order([("BEV-1001", 2, "10.00")])
        result = apply_discounts(subject, catalog(), [ThresholdDiscount("bulk", threshold=Money.parse("50.00"), percent=10)])
        self.assertEqual(Money(0), result.total)

    def test_category(self):
        subject = order([("SNA-2001", 4, "5.00"), ("BEV-1001", 1, "10.00")])
        result = apply_discounts(subject, catalog(), [CategoryDiscount("snack", category="snacks", percent=25)])
        self.assertEqual(Money.parse("5.00"), result.total)

    def test_only_one_rule_per_scope(self):
        subject = order([("BEV-1001", 10, "10.00")])
        rules = [
            ThresholdDiscount("a", priority=1, scope="order", threshold=Money.parse("10.00"), percent=10),
            ThresholdDiscount("b", priority=0, scope="order", threshold=Money.parse("10.00"), percent=20),
        ]
        result = apply_discounts(subject, catalog(), rules)
        self.assertEqual(["a"], result.applied)
        self.assertEqual(Money.parse("10.00"), result.total)

    def test_total_never_exceeds_subtotal(self):
        subject = order([("BEV-1001", 1, "10.00")])
        result = apply_discounts(
            subject,
            catalog(),
            [
                PromoCodeDiscount("gift", scope="order", amount=Money.parse("5.00")),
            ],
        )
        self.assertEqual(Money.parse("5.00"), result.total)


if __name__ == "__main__":
    unittest.main()
