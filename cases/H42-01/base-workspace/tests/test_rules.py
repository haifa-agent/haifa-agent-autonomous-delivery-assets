import unittest
from datetime import UTC, datetime

from depot.core.catalog import Catalog, Product
from depot.core.ids import order_id
from depot.core.money import Money
from depot.core.orders import Order, OrderLine, OrderStatus
from depot.core.rules import OrderPolicy, validate_order
from depot.core.sku import Sku
from depot.core.units import Weight


def catalog():
    return Catalog(
        [
            Product(Sku("BEV-1001"), "Coffee", "beverages", Money.parse("10.00"), Weight(1)),
            Product(Sku("BEV-1003"), "Cocoa", "beverages", Money.parse("6.00"), Weight(1), active=False),
        ]
    )


def order(lines, warehouse="WH-CEN"):
    return Order(
        identifier=order_id("O-000101"),
        customer="Acme",
        warehouse=warehouse,
        status=OrderStatus.DRAFT,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        lines=[OrderLine(Sku(sku), qty, Money.parse("10.00")) for sku, qty in lines],
    )


class RulesTest(unittest.TestCase):
    def test_clean_order_has_no_problems(self):
        self.assertEqual([], validate_order(order([("BEV-1001", 2)]), catalog(), OrderPolicy()))

    def test_inactive_product(self):
        problems = validate_order(order([("BEV-1003", 1)]), catalog(), OrderPolicy())
        self.assertTrue(any("not active" in problem for problem in problems))

    def test_unknown_sku(self):
        problems = validate_order(order([("SNA-2001", 1)]), catalog(), OrderPolicy())
        self.assertTrue(any("not in the catalogue" in problem for problem in problems))

    def test_warehouse_policy(self):
        problems = validate_order(
            order([("BEV-1001", 2)], warehouse="WH-EAS"),
            catalog(),
            OrderPolicy(allowed_warehouses=("WH-CEN",)),
        )
        self.assertTrue(any("not allowed" in problem for problem in problems))

    def test_line_ceiling(self):
        problems = validate_order(
            order([("BEV-1001", 1000)]), catalog(), OrderPolicy(max_units_per_line=500)
        )
        self.assertTrue(any("maximum per line" in problem for problem in problems))


if __name__ == "__main__":
    unittest.main()
