import unittest

from depot.core.errors import ValidationError
from depot.core.ids import order_id, product_id, sequence_identifier
from depot.core.sku import Sku


class IdentifierTest(unittest.TestCase):
    def test_valid_and_invalid(self):
        self.assertEqual("P-1001", product_id("P-1001").value)
        self.assertEqual("O-000101", order_id("O-000101").value)
        with self.assertRaises(ValidationError):
            product_id("1001")
        with self.assertRaises(ValidationError):
            order_id("O-1")

    def test_sequence_identifier(self):
        self.assertEqual("P-0007", sequence_identifier("product", 7).value)
        self.assertEqual("SUP-012", sequence_identifier("supplier", 12).value)
        self.assertEqual("WH-004", sequence_identifier("warehouse", 4).value)


class SkuTest(unittest.TestCase):
    def test_normalisation(self):
        self.assertEqual("BEV-1001", Sku(" bev-1001 ").value)
        self.assertEqual("BEV", Sku("BEV-1001").prefix)
        self.assertEqual(1001, Sku("BEV-1001").serial)

    def test_rejects_bad_sku(self):
        for value in ("", "bev", "B-1", "BEV-1"):
            with self.assertRaises(ValidationError):
                Sku(value)


if __name__ == "__main__":
    unittest.main()
