import unittest
from datetime import UTC, datetime

from depot.core.catalog import Catalog, Product
from depot.core.discounts import ThresholdDiscount
from depot.core.ids import order_id
from depot.core.money import Money
from depot.core.orders import Order, OrderLine, OrderStatus
from depot.core.pricing import price_order
from depot.core.sku import Sku
from depot.core.tax import TaxTable
from depot.core.units import Weight


def setup():
    catalog = Catalog([Product(Sku("BEV-1001"), "Coffee", "beverages", Money.parse("10.00"), Weight(100))])
    order = Order(
        identifier=order_id("O-000101"),
        customer="Acme",
        warehouse="WH-CEN",
        status=OrderStatus.DRAFT,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        lines=[OrderLine(Sku("BEV-1001"), 2, Money.parse("10.00"))],
    )
    return catalog, order


class PricingTest(unittest.TestCase):
    def test_plain_order(self):
        catalog, order = setup()
        pricing = price_order(order, catalog, TaxTable(rates={"CN": 1000}), region="CN")
        self.assertEqual(Money.parse("20.00"), pricing.subtotal)
        self.assertEqual(Money.parse("2.00"), pricing.tax)
        self.assertEqual(Money.parse("22.00"), pricing.total)

    def test_discount_applies_before_tax(self):
        catalog, order = setup()
        rules = [ThresholdDiscount("bulk", threshold=Money.parse("10.00"), percent=10)]
        pricing = price_order(order, catalog, TaxTable(rates={"CN": 1000}), rules, region="CN")
        self.assertEqual(Money.parse("2.00"), pricing.discount)
        self.assertEqual(Money.parse("18.00"), pricing.taxable)
        self.assertEqual(Money.parse("1.80"), pricing.tax)
        self.assertEqual(Money.parse("19.80"), pricing.total)
        self.assertEqual(["bulk"], pricing.applied)

    def test_origin_region_has_no_rate(self):
        catalog, order = setup()
        pricing = price_order(order, catalog, TaxTable(rates={"SG": 900}), region="XX")
        self.assertEqual(Money(0), pricing.tax)


if __name__ == "__main__":
    unittest.main()
