import unittest

from kiosk.core.catalog import Item
from kiosk.core.errors import CatalogError
from kiosk.core.ordering import DEFAULT_ORDER, ORDERS, resolve, sort_items

ITEMS = [
    Item("K-003", "Cold Brew", 3900, popularity=95),
    Item("K-001", "Almond Croissant", 3200, popularity=40),
    Item("K-002", "Barista Special", 4500, popularity=95),
]


class ResolveTest(unittest.TestCase):
    def test_none_resolves_to_the_default_order(self):
        self.assertEqual(DEFAULT_ORDER, resolve(None).name)

    def test_every_published_order_resolves(self):
        for name in ORDERS:
            self.assertEqual(name, resolve(name).name)

    def test_an_unknown_order_is_rejected(self):
        with self.assertRaises(CatalogError):
            resolve("colour")


class SortTest(unittest.TestCase):
    def test_the_input_list_is_not_touched(self):
        original = list(ITEMS)
        sort_items(ITEMS)

        self.assertEqual(original, ITEMS)

    def test_sorting_by_name(self):
        self.assertEqual(["K-001", "K-002", "K-003"], [item.sku for item in sort_items(ITEMS, "name")])

    def test_sorting_by_price(self):
        self.assertEqual(["K-001", "K-003", "K-002"], [item.sku for item in sort_items(ITEMS, "price")])

    def test_a_descending_order_runs_from_the_highest_value(self):
        ordered = sort_items(ITEMS, "popularity")

        self.assertEqual([95, 95, 40], [item.popularity for item in ordered])

    def test_items_with_the_same_value_are_separated_by_sku(self):
        ordered = sort_items(ITEMS, "popularity")

        self.assertEqual(["K-002", "K-003"], [item.sku for item in ordered[:2]])


if __name__ == "__main__":
    unittest.main()
