import unittest

from export import export_batch


class ExportTest(unittest.TestCase):
    def test_records_are_normalized_and_numbered(self):
        exported = export_batch([{"id": " A-1 ", "name": " first "}, {"id": "b-2", "name": "second"}])

        self.assertEqual(
            [
                {"id": "a-1", "name": "first", "position": 1},
                {"id": "b-2", "name": "second", "position": 2},
            ],
            exported,
        )

    def test_input_records_are_not_mutated(self):
        records = [{"id": " A-1 ", "name": "first"}]

        export_batch(records)

        self.assertEqual([{"id": " A-1 ", "name": "first"}], records)

    def test_duplicate_ids_are_exported_once(self):
        exported = export_batch([{"id": "A", "name": "first"}, {"id": "b", "name": "second"}, {"id": "a ", "name": "again"}])

        self.assertEqual(["a", "b"], [record["id"] for record in exported])
        self.assertEqual("first", exported[0]["name"])
        self.assertEqual([1, 2], [record["position"] for record in exported])


if __name__ == "__main__":
    unittest.main()
