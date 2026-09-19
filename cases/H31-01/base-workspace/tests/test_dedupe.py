import unittest

from kiosk.core.dedupe import drop_duplicates


class DropDuplicatesTest(unittest.TestCase):
    def test_the_first_row_of_a_key_wins(self):
        rows = [{"sku": "A", "n": 1}, {"sku": "A", "n": 2}, {"sku": "B", "n": 3}]

        self.assertEqual([{"sku": "A", "n": 1}, {"sku": "B", "n": 3}], drop_duplicates(rows))

    def test_keys_are_compared_after_normalization(self):
        rows = [{"sku": "A"}, {"sku": " a "}]

        self.assertEqual(1, len(drop_duplicates(rows)))

    def test_a_row_without_the_key_is_kept(self):
        rows = [{"other": 1}, {"other": 2}]

        self.assertEqual(2, len(drop_duplicates(rows)))

    def test_an_empty_batch_stays_empty(self):
        self.assertEqual([], drop_duplicates([]))


if __name__ == "__main__":
    unittest.main()
