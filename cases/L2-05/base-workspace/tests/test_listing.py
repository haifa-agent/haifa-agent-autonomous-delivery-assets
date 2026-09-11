import unittest

from listing import list_records
from repository import all_records


class ListingTest(unittest.TestCase):
    def test_default_page_size_is_twenty(self):
        self.assertEqual(20, len(list_records()))

    def test_page_size_is_applied(self):
        self.assertEqual([f"record-{index:02d}" for index in range(1, 6)], list_records(5))

    def test_page_size_range_is_validated(self):
        for invalid in (0, 101):
            with self.assertRaises(ValueError):
                list_records(invalid)

    def test_default_order_is_unchanged(self):
        records = all_records()

        self.assertEqual(50, len(records))
        self.assertEqual("record-01", records[0])
        self.assertEqual("record-50", records[-1])


if __name__ == "__main__":
    unittest.main()