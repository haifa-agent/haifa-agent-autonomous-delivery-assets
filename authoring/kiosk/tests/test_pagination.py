import unittest

from kiosk.core.catalog import Item
from kiosk.core.errors import CursorError
from kiosk.core.ordering import sort_items
from kiosk.core.pagination import decode_cursor, encode_cursor, page

ITEMS = sort_items([Item(f"K-{index:03d}", f"Item {chr(65 + index)}", 100 + index) for index in range(7)])


def _walk(items, size, order="name"):
    """Page through the whole listing; a cursor that does not move forward must not hang the suite."""
    seen, cursor = [], None
    for _ in range(2 * len(items) + 2):
        window, cursor = page(items, size, cursor, order)
        seen.extend(item.sku for item in window)
        if cursor is None:
            return seen
    raise AssertionError(f"paging with size {size} never reached the end of the listing")


class CursorTest(unittest.TestCase):
    def test_a_cursor_round_trips(self):
        order, value, sku = decode_cursor(encode_cursor(ITEMS[0], "name"))

        self.assertEqual("name", order)
        self.assertEqual(ITEMS[0].sku, sku)
        self.assertTrue(value)

    def test_a_damaged_cursor_is_rejected(self):
        with self.assertRaises(CursorError):
            decode_cursor("not-a-cursor!!")

    def test_a_cursor_of_another_order_is_rejected(self):
        cursor = encode_cursor(ITEMS[0], "name")

        with self.assertRaises(CursorError):
            page(ITEMS, 2, cursor, "price")


class PageTest(unittest.TestCase):
    def test_the_first_page_starts_at_the_beginning(self):
        window, cursor = page(ITEMS, 3)

        self.assertEqual([item.sku for item in ITEMS[:3]], [item.sku for item in window])
        self.assertIsNotNone(cursor)

    def test_paging_visits_every_item_exactly_once(self):
        for size in (1, 2, 3, 7, 20):
            self.assertEqual([item.sku for item in ITEMS], _walk(ITEMS, size), f"size {size}")

    def test_the_last_page_has_no_next_cursor(self):
        _, cursor = page(ITEMS, len(ITEMS))

        self.assertIsNone(cursor)

    def test_an_empty_listing_is_one_empty_page(self):
        self.assertEqual(([], None), page([], 5))

    def test_a_size_below_one_is_rejected(self):
        with self.assertRaises(ValueError):
            page(ITEMS, 0)


if __name__ == "__main__":
    unittest.main()
