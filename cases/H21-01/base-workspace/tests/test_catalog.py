import unittest

from kiosk.core.catalog import Item, by_sku, item_from_row
from kiosk.core.errors import ValidationError

ROW = {"sku": "K-001", "name": "Almond Croissant", "price_cents": 3200}


class ItemFromRowTest(unittest.TestCase):
    def test_a_minimal_row_becomes_an_item(self):
        item = item_from_row(ROW)

        self.assertEqual("K-001", item.sku)
        self.assertEqual(0, item.popularity)
        self.assertIsNone(item.supplier)
        self.assertEqual((), item.tags)

    def test_optional_fields_are_read(self):
        item = item_from_row({**ROW, "popularity": 40, "supplier": "Nord", "tags": ["bakery"]})

        self.assertEqual(40, item.popularity)
        self.assertEqual("Nord", item.supplier)
        self.assertEqual(("bakery",), item.tags)

    def test_a_missing_required_field_is_rejected(self):
        for name in ("sku", "name", "price_cents"):
            row = {key: value for key, value in ROW.items() if key != name}
            with self.assertRaises(ValidationError):
                item_from_row(row)

    def test_blank_and_negative_values_are_rejected(self):
        for row in ({**ROW, "sku": "  "}, {**ROW, "name": ""}, {**ROW, "price_cents": -1}):
            with self.assertRaises(ValidationError):
                item_from_row(row)

    def test_a_price_that_is_not_a_number_is_rejected(self):
        with self.assertRaises(ValidationError):
            item_from_row({**ROW, "price_cents": "free"})


class BySkuTest(unittest.TestCase):
    def test_the_first_item_of_a_sku_wins(self):
        first = Item("K-1", "First", 100)
        index = by_sku([first, Item("K-1", "Second", 200)])

        self.assertEqual(first, index["K-1"])


if __name__ == "__main__":
    unittest.main()
