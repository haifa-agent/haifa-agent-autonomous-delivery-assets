import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from inventory import Inventory


class InventoryTest(unittest.TestCase):
    def test_save_and_load_round_trip(self):
        with TemporaryDirectory() as directory:
            store = Inventory(Path(directory) / "store.json")
            store.save({"a-1": {"sku": "a-1", "name": "item a", "quantity": 2}})

            self.assertEqual({"a-1": {"sku": "a-1", "name": "item a", "quantity": 2}}, store.items())

    def test_missing_store_is_empty(self):
        with TemporaryDirectory() as directory:
            self.assertEqual({}, Inventory(Path(directory) / "absent.json").items())


if __name__ == "__main__":
    unittest.main()