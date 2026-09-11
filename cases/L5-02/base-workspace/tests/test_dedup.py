import time
import unittest

from dedup import deduplicate


class DedupTest(unittest.TestCase):
    def test_first_seen_order_is_preserved(self):
        self.assertEqual(["b", "a", "c"], deduplicate(["b", "a", "b", "c", "a"]))

    def test_empty_input(self):
        self.assertEqual([], deduplicate([]))

    def test_large_input_finishes_quickly(self):
        records = [f"r-{index % 4000}" for index in range(8000)]

        started = time.monotonic()
        unique = deduplicate(records)
        elapsed = time.monotonic() - started

        self.assertEqual(4000, len(unique))
        self.assertEqual("r-0", unique[0])
        self.assertEqual("r-3999", unique[-1])
        self.assertLess(elapsed, 1.0)


if __name__ == "__main__":
    unittest.main()