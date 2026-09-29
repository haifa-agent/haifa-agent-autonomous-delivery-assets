import unittest
from datetime import UTC, datetime

from depot.core.allocation import allocate
from depot.core.errors import InsufficientStockError
from depot.core.ids import order_id
from depot.core.inventory import Inventory, StockItem
from depot.core.money import Money
from depot.core.orders import Order, OrderLine, OrderStatus
from depot.core.sku import Sku


def order(lines):
    return Order(
        identifier=order_id("O-000101"),
        customer="Acme",
        warehouse="WH-CEN",
        status=OrderStatus.CONFIRMED,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        lines=[OrderLine(Sku(sku), qty, Money.parse("1.00")) for sku, qty in lines],
    )


class AllocationTest(unittest.TestCase):
    def test_full_allocation(self):
        inventory = Inventory([StockItem("BEV-1001", on_hand=10)])
        allocation = allocate(order([("BEV-1001", 4)]), inventory)
        self.assertEqual({"BEV-1001": 4}, allocation.reserved)
        self.assertEqual(6, inventory.available("BEV-1001"))

    def test_shortfall_is_refused_by_default(self):
        inventory = Inventory([StockItem("BEV-1001", on_hand=2)])
        with self.assertRaises(InsufficientStockError):
            allocate(order([("BEV-1001", 4)]), inventory)
        # Nothing was reserved on failure.
        self.assertEqual(2, inventory.available("BEV-1001"))

    def test_partial_allocation(self):
        inventory = Inventory([StockItem("BEV-1001", on_hand=2)])
        allocation = allocate(order([("BEV-1001", 4)]), inventory, allow_partial=True)
        self.assertEqual({"BEV-1001": 2}, allocation.reserved)


if __name__ == "__main__":
    unittest.main()
