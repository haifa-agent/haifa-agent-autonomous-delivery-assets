import time
import unittest

from importer import import_rows


class ImporterTest(unittest.TestCase):
    def test_small_import_skips_duplicates(self):
        rows = [{"id": "b", "name": "second"}, {"id": "c", "name": "third"}]
        existing = [{"id": "a", "name": "first"}, {"id": "b", "name": "old"}]

        imported, skipped = import_rows(rows, existing)

        self.assertEqual([{"id": "c", "name": "third"}], imported)
        self.assertEqual(["b"], skipped)

    def test_same_input_twice_is_skipped(self):
        imported, skipped = import_rows([{"id": "x", "name": "x"}, {"id": "x", "name": "x"}], [])

        self.assertEqual(1, len(imported))
        self.assertEqual(["x"], skipped)

    def test_empty_inputs(self):
        self.assertEqual(([], []), import_rows([], []))

    def test_large_import_finishes_quickly(self):
        existing = [{"id": f"e-{index}", "name": "existing"} for index in range(2000)]
        rows = [{"id": f"n-{index}", "name": "new"} for index in range(8000)]

        started = time.monotonic()
        imported, skipped = import_rows(rows, existing)
        elapsed = time.monotonic() - started

        self.assertEqual(8000, len(imported))
        self.assertEqual([], skipped)
        self.assertLess(elapsed, 1.0)


if __name__ == "__main__":
    unittest.main()