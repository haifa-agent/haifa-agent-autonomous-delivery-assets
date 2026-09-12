import unittest

from dashboard import dashboard_rows
from listing import list_records


class ListingTest(unittest.TestCase):
    def test_default_listing_has_twenty_records(self):
        self.assertEqual(20, len(list_records()))

    def test_page_size_is_applied(self):
        self.assertEqual(5, len(list_records(page_size=5)))

    def test_page_size_range_is_validated(self):
        for invalid in (0, 101):
            with self.assertRaises(ValueError):
                list_records(page_size=invalid)

    def test_dashboard_lists_the_default_listing(self):
        self.assertEqual(20, len(dashboard_rows()))


if __name__ == "__main__":
    unittest.main()
