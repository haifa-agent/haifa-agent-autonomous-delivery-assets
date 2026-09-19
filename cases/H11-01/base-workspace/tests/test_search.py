import unittest

from kiosk.core.catalog import Item
from kiosk.core.errors import ValidationError
from kiosk.core.search import Query, filter_items, matches

ITEMS = [
    Item("K-001", "Cold Brew", 3900, supplier="Roasters Union", tags=("coffee", "cold")),
    Item("K-002", "Earl Grey Tea", 2500, supplier="Leaf and Co", tags=("tea",)),
    Item("K-003", "Lavender Shortbread", 2200, supplier="Boulangerie Nord", tags=("bakery",)),
]


class MatchesTest(unittest.TestCase):
    def test_text_matches_name_sku_supplier_and_tags(self):
        self.assertTrue(matches(ITEMS[0], Query(text="cold")))
        self.assertTrue(matches(ITEMS[0], Query(text="K-001")))
        self.assertTrue(matches(ITEMS[1], Query(text="leaf")))
        self.assertTrue(matches(ITEMS[2], Query(text="bakery")))

    def test_every_word_of_the_text_must_match(self):
        self.assertTrue(matches(ITEMS[0], Query(text="cold brew")))
        self.assertFalse(matches(ITEMS[0], Query(text="cold tea")))

    def test_a_tag_is_compared_after_normalization(self):
        self.assertTrue(matches(ITEMS[1], Query(tag="TEA")))
        self.assertFalse(matches(ITEMS[1], Query(tag="coffee")))

    def test_the_price_ceiling_is_inclusive(self):
        self.assertTrue(matches(ITEMS[2], Query(max_price_cents=2200)))
        self.assertFalse(matches(ITEMS[2], Query(max_price_cents=2199)))


class FilterItemsTest(unittest.TestCase):
    def test_an_empty_query_keeps_everything_in_order(self):
        self.assertEqual(ITEMS, filter_items(ITEMS, Query()))

    def test_parts_of_a_query_are_combined(self):
        found = filter_items(ITEMS, Query(text="e", max_price_cents=2500))

        self.assertEqual(["K-002", "K-003"], [item.sku for item in found])

    def test_a_negative_ceiling_is_rejected(self):
        with self.assertRaises(ValidationError):
            filter_items(ITEMS, Query(max_price_cents=-1))


if __name__ == "__main__":
    unittest.main()
