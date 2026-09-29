import unittest

from depot.core.errors import InsufficientStockError, ValidationError
from depot.core.inventory import Inventory, StockItem


class StockItemTest(unittest.TestCase):
    def test_lifecycle(self):
        item = StockItem(sku="BEV-1001", on_hand=10)
        item.reserve(4)
        self.assertEqual(6, item.available)
        item.pick(3)
        self.assertEqual(7, item.on_hand)
        self.assertEqual(1, item.reserved)
        item.release(1)
        item.receive(5)
        self.assertEqual(12, item.on_hand)

    def test_over_reserve_is_refused(self):
        item = StockItem(sku="BEV-1001", on_hand=2)
        with self.assertRaises(InsufficientStockError):
            item.reserve(3)

    def test_invalid_construction(self):
        with self.assertRaises(ValidationError):
            StockItem(sku="BEV-1001", on_hand=-1)
        with self.assertRaises(ValidationError):
            StockItem(sku="BEV-1001", on_hand=1, reserved=2)

    def test_reorder(self):
        item = StockItem(sku="BEV-1001", on_hand=5, reorder_point=10)
        self.assertTrue(item.needs_reorder())


class InventoryTest(unittest.TestCase):
    def test_missing_sku_is_zero(self):
        inventory = Inventory([])
        self.assertEqual(0, inventory.available("BEV-1001"))

    def test_low_stock(self):
        inventory = Inventory(
            [
                StockItem(sku="A", on_hand=5, reorder_point=10),
                StockItem(sku="B", on_hand=50, reorder_point=10),
            ]
        )
        self.assertEqual(["A"], [item.sku for item in inventory.low_stock()])

    def test_receive_creates_missing(self):
        inventory = Inventory([])
        inventory.receive("NEW", 3)
        self.assertEqual(3, inventory.available("NEW"))


if __name__ == "__main__":
    unittest.main()
