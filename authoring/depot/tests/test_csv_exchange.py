import unittest

from depot.adapter.csv_exchange import export_rows, parse_rows
from depot.core.errors import FormatError

FIELDS = ["sku", "name", "price"]


class CsvExchangeTest(unittest.TestCase):
    def test_round_trip(self):
        rows = [{"sku": "BEV-1001", "name": "Coffee, Beans", "price": "12.50"}]
        text = export_rows(rows, FIELDS)
        self.assertEqual("sku,name,price\n", text.split("\n")[0] + "\n")
        self.assertEqual(rows, parse_rows(text, FIELDS))

    def test_quotes_survive(self):
        rows = [{"sku": "A-1001", "name": 'Say "hi"', "price": "1.00"}]
        self.assertEqual(rows, parse_rows(export_rows(rows, FIELDS), FIELDS))

    def test_bad_header_is_rejected(self):
        with self.assertRaises(FormatError):
            parse_rows("a,b\n1,2\n", FIELDS)


if __name__ == "__main__":
    unittest.main()
