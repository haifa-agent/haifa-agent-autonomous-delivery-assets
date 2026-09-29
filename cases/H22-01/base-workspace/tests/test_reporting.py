import unittest
from datetime import UTC, datetime

from depot.core.catalog import Catalog, Product
from depot.core.ids import order_id
from depot.core.inventory import Inventory, StockItem
from depot.core.money import Money
from depot.core.orders import Order, OrderLine, OrderStatus
from depot.core.reporting import (
    category_breakdown,
    fill_rate,
    inventory_valuation,
    ordered_units,
    revenue,
    status_counts,
)
from depot.core.sku import Sku
from depot.core.units import Weight


def catalog():
    return Catalog(
        [
            Product(Sku("BEV-1001"), "Coffee", "beverages", Money.parse("10.00"), Weight(1)),
            Product(Sku("SNA-2001"), "Almonds", "snacks", Money.parse("5.00"), Weight(1)),
        ]
    )


def order(identifier, status, lines):
    return Order(
        identifier=order_id(identifier),
        customer="Acme",
        warehouse="WH-CEN",
        status=status,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        lines=[OrderLine(Sku(sku), qty, Money.parse(price)) for sku, qty, price in lines],
    )


class ReportingTest(unittest.TestCase):
    def setUp(self):
        self.orders = [
            order("O-000101", OrderStatus.CONFIRMED, [("BEV-1001", 2, "10.00")]),
            order("O-000102", OrderStatus.CANCELLED, [("SNA-2001", 4, "5.00")]),
        ]

    def test_status_counts(self):
        self.assertEqual({"CANCELLED": 1, "CONFIRMED": 1}, status_counts(self.orders))

    def test_revenue_skips_cancelled(self):
        totals = {"O-000101": Money.parse("20.00"), "O-000102": Money.parse("20.00")}
        self.assertEqual(Money.parse("20.00"), revenue(self.orders, totals))

    def test_units_and_fill_rate(self):
        self.assertEqual(6, ordered_units(self.orders))
        self.assertEqual(0.5, fill_rate(4, 2))
        self.assertEqual(1.0, fill_rate(0, 0))

    def test_valuation_uses_on_hand(self):
        inventory = Inventory([StockItem("BEV-1001", on_hand=3), StockItem("SNA-2001", on_hand=2)])
        self.assertEqual(Money.parse("40.00"), inventory_valuation(inventory, catalog()))

    def test_category_breakdown_is_sorted(self):
        breakdown = category_breakdown(self.orders, catalog())
        self.assertEqual(["beverages", "snacks"], list(breakdown))
        self.assertEqual(Money.parse("20.00"), breakdown["beverages"])


if __name__ == "__main__":
    unittest.main()
