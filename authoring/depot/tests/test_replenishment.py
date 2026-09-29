import unittest

from depot.core.catalog import Catalog, Product
from depot.core.inventory import Inventory, StockItem
from depot.core.money import Money
from depot.core.replenishment import suggestions
from depot.core.sku import Sku
from depot.core.supplier import Supplier, SupplierDirectory
from depot.core.ids import supplier_id
from depot.core.units import Weight


def catalog():
    return Catalog([Product(Sku("BEV-1001"), "Coffee", "beverages", Money.parse("10.00"), Weight(100))])


def suppliers():
    return SupplierDirectory(
        [
            Supplier(supplier_id("SUP-001"), "Slow", 14, 100, supplies=("BEV-1001",)),
            Supplier(supplier_id("SUP-002"), "Fast", 5, 20, supplies=("BEV-1001",)),
        ]
    )


class ReplenishmentTest(unittest.TestCase):
    def test_suggestion_uses_fastest_supplier_and_respects_moq(self):
        inventory = Inventory([StockItem("BEV-1001", on_hand=5, reorder_point=40, safety_stock=10)])
        result = suggestions(inventory, suppliers(), catalog())
        self.assertEqual(1, len(result))
        self.assertEqual("SUP-002", result[0].supplier_id)
        self.assertEqual(45, result[0].quantity)

    def test_no_suggestion_when_stocked(self):
        inventory = Inventory([StockItem("BEV-1001", on_hand=100, reorder_point=40)])
        self.assertEqual([], suggestions(inventory, suppliers(), catalog()))

    def test_unknown_sku_is_skipped(self):
        inventory = Inventory([StockItem("ZZZ-9999", on_hand=0, reorder_point=10)])
        self.assertEqual([], suggestions(inventory, suppliers(), catalog()))


if __name__ == "__main__":
    unittest.main()
