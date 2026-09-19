import unittest

from kiosk.core.catalog import Item
from kiosk.app.restock import POPULARITY_FLOOR, suggestions

ITEMS = [
    Item("K-001", "Rare", 100, popularity=1),
    Item("K-002", "Steady", 100, popularity=POPULARITY_FLOOR),
    Item("K-003", "Popular", 100, popularity=POPULARITY_FLOOR * 3),
]


class SuggestionsTest(unittest.TestCase):
    def test_the_most_popular_item_comes_first(self):
        self.assertEqual(["K-003", "K-002"], [item.sku for item in suggestions(ITEMS)])

    def test_an_unpopular_item_is_not_suggested(self):
        self.assertNotIn("K-001", [item.sku for item in suggestions(ITEMS)])

    def test_the_limit_is_respected(self):
        self.assertEqual(1, len(suggestions(ITEMS, limit=1)))
        self.assertEqual([], suggestions(ITEMS, limit=0))

    def test_the_reason_separates_a_strong_seller_from_a_steady_one(self):
        reasons = {item.sku: item.reason for item in suggestions(ITEMS)}

        self.assertEqual("sells well", reasons["K-003"])
        self.assertEqual("steady seller", reasons["K-002"])

    def test_a_negative_limit_is_rejected(self):
        with self.assertRaises(ValueError):
            suggestions(ITEMS, limit=-1)


if __name__ == "__main__":
    unittest.main()
