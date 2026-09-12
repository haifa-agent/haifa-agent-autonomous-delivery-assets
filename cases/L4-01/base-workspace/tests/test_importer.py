import unittest
from pathlib import Path

from opsdesk.api.imports import import_file
from opsdesk.core.importer import import_rows
from opsdesk.store.record_store import RecordStore

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "rows.json"


class ImporterTest(unittest.TestCase):
    def test_known_ids_are_skipped(self):
        store = RecordStore([{"id": "a", "name": "first"}, {"id": "b", "name": "old"}])

        result = import_rows([{"id": "b", "name": "second"}, {"id": "c", "name": "third"}], store)

        self.assertEqual([{"id": "c", "name": "third"}], result.imported)
        self.assertEqual(["b"], result.skipped)
        self.assertEqual(["a", "b", "c"], [row["id"] for row in store.rows()])

    def test_duplicates_inside_the_input_are_skipped(self):
        result = import_rows([{"id": "x", "name": "1"}, {"id": "x", "name": "2"}], RecordStore())

        self.assertEqual([{"id": "x", "name": "1"}], result.imported)
        self.assertEqual(["x"], result.skipped)

    def test_store_rejects_duplicate_ids(self):
        store = RecordStore([{"id": "a", "name": "first"}])

        with self.assertRaises(ValueError):
            store.add({"id": "a", "name": "again"})

    def test_sample_file_import(self):
        result = import_file(SAMPLE)

        self.assertEqual(["n-1", "n-2", "n-3"], [row["id"] for row in result.imported])
        self.assertEqual(["n-1"], result.skipped)


if __name__ == "__main__":
    unittest.main()
