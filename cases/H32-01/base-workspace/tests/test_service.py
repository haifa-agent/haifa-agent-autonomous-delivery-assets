import unittest
from pathlib import Path

from depot.adapter.config_loader import DepotConfig
from depot.api.service import DepotService
from depot.store.migrations import SCHEMA_VERSION, ensure_schema, read_schema
from depot.store.paths import data_paths

DATA = Path(__file__).resolve().parents[1] / "data"


class StoreAndServiceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = DepotService.open(DATA, DepotConfig(region="CN"))

    def test_schema_file(self):
        self.assertEqual(SCHEMA_VERSION, read_schema(data_paths(DATA).schema))
        self.assertEqual(SCHEMA_VERSION, ensure_schema(data_paths(DATA).schema))

    def test_data_loads(self):
        self.assertEqual(9, len(self.service.catalog.all()))
        self.assertEqual(3, len(self.service.orders))
        self.assertEqual(3, len(self.service.carriers.all()))
        self.assertEqual("A-01", self.service.locations["BEV-1001"])

    def test_pricing_of_a_known_order(self):
        order = self.service.find_order("O-000101")
        pricing = self.service.pricing(order)
        self.assertEqual("570.00", pricing.subtotal.as_decimal())
        self.assertEqual("34.20", pricing.tax.as_decimal())

    def test_pick_list_is_walk_ordered(self):
        order = self.service.find_order("O-000101")
        pick = self.service.pick_list(order)
        locations = [entry.location for entry in pick.entries]
        self.assertEqual(sorted(locations), locations)
        self.assertEqual(84, pick.units)

    def test_parcels_and_carrier(self):
        order = self.service.find_order("O-000103")
        parcels = self.service.parcels(order)
        self.assertTrue(parcels)
        self.assertEqual("ECON", self.service.select_carrier(order).code)

    def test_reorder_suggestions(self):
        suggestions = self.service.reorder_suggestions()
        self.assertTrue(suggestions)
        self.assertIn("BEV-1002", [s.sku for s in suggestions])


if __name__ == "__main__":
    unittest.main()
