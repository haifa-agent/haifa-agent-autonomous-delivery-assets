import json
import unittest
from pathlib import Path

from kiosk.app.exporters import available, export
from kiosk.app.exporters.json_export import FIELDS, row_of
from kiosk.app.repository import CatalogRepository
from kiosk.core.catalog import Item
from kiosk.core.errors import KioskError
from kiosk.core.format_rules import MISSING

CATALOG = Path(__file__).resolve().parents[1] / "data" / "catalog.json"


class RegistryTest(unittest.TestCase):
    def test_json_is_offered(self):
        self.assertIn("json", available())

    def test_an_unknown_format_is_rejected(self):
        with self.assertRaises(KioskError):
            export("wax-tablet", [])


class RowTest(unittest.TestCase):
    def test_every_field_is_rendered(self):
        row = row_of(Item("K-1", "Name", 1234, updated_at_millis=1789430400000, supplier="Nord"))

        self.assertEqual(set(FIELDS), set(row))
        self.assertEqual("12.34", row["price"])
        self.assertEqual("2026-09-15T00:00:00Z", row["updated"])

    def test_a_missing_supplier_and_timestamp_use_the_placeholder(self):
        row = row_of(Item("K-1", "Name", 100))

        self.assertEqual(MISSING, row["supplier"])
        self.assertEqual(MISSING, row["updated"])

    def test_a_long_name_is_clipped(self):
        row = row_of(Item("K-1", "N" * 80, 100))

        self.assertEqual(40, len(row["name"]))


class ExportTest(unittest.TestCase):
    def test_the_export_is_readable_json_in_field_order(self):
        items = CatalogRepository(CATALOG).items()

        payload = json.loads(export("json", items))

        self.assertEqual(list(FIELDS), payload["fields"])
        self.assertEqual(len(items), len(payload["items"]))


if __name__ == "__main__":
    unittest.main()
