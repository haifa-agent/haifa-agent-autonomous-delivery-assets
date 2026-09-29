import unittest

from depot.core.catalog import Catalog, Product
from depot.core.errors import NotFoundError, ValidationError
from depot.core.money import Money
from depot.core.sku import Sku
from depot.core.units import Weight


def product(sku, name, category, price, active=True, tags=()):
    return Product(
        sku=Sku(sku),
        name=name,
        category=category,
        unit_price=Money.parse(price),
        weight=Weight(100),
        active=active,
        tags=tuple(tags),
    )


class CatalogTest(unittest.TestCase):
    def setUp(self):
        self.catalog = Catalog(
            [
                product("BEV-1001", "Coffee", "beverages", "12.50", tags=["coffee"]),
                product("SNA-2001", "Almonds", "snacks", "9.90", active=False),
                product("BEV-1002", "Tea", "beverages", "8.00", tags=["tea"]),
            ]
        )

    def test_get_and_find(self):
        self.assertEqual("Coffee", self.catalog.get("BEV-1001").name)
        self.assertIsNone(self.catalog.find("NOPE-0001"))
        with self.assertRaises(NotFoundError):
            self.catalog.get("NOPE-0001")

    def test_active_and_category(self):
        self.assertEqual(2, len(self.catalog.active()))
        self.assertEqual(["BEV-1001", "BEV-1002"], [p.sku.value for p in self.catalog.by_category("beverages")])

    def test_search(self):
        self.assertEqual(["BEV-1001"], [p.sku.value for p in self.catalog.search("coffee")])
        self.assertEqual([], self.catalog.search(""))

    def test_duplicate_skus_are_rejected(self):
        with self.assertRaises(ValidationError):
            Catalog([product("BEV-1001", "A", "x", "1.00"), product("BEV-1001", "B", "y", "2.00")])


if __name__ == "__main__":
    unittest.main()
