import unittest

from depot.core.money import Money
from depot.core.tax import TaxTable


class TaxTest(unittest.TestCase):
    def test_rate_lookup_is_case_insensitive(self):
        table = TaxTable(rates={"CN": 600})
        self.assertEqual(600, table.rate_for("cn"))
        self.assertEqual(0, table.rate_for("US"))

    def test_tax_is_integer(self):
        table = TaxTable(rates={"CN": 600}, default_basis_points=1000)
        self.assertEqual(Money.parse("6.00"), table.tax_for(Money.parse("100.00"), "CN"))

    def test_default_rate(self):
        table = TaxTable(rates={"CN": 600}, default_basis_points=500)
        self.assertEqual(Money.parse("2.50"), table.tax_for(Money.parse("50.00"), "ZZ"))


if __name__ == "__main__":
    unittest.main()
