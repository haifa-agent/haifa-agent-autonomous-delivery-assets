import contextlib
import io
import json
import unittest

from depot.api.cli import main


class CliTest(unittest.TestCase):
    def run_cli(self, *arguments):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(arguments))
        return code, out.getvalue(), err.getvalue()

    def test_summary(self):
        code, out, _ = self.run_cli("--json", "summary")
        self.assertEqual(0, code)
        payload = json.loads(out)
        self.assertEqual(3, payload["orders"])
        self.assertIn("inventoryValue", payload)

    def test_price_of_an_order(self):
        code, out, _ = self.run_cli("--json", "price", "--order", "O-000101")
        self.assertEqual(0, code)
        self.assertEqual("604.20", json.loads(out)["total"])

    def test_region_override_changes_tax(self):
        code, out, _ = self.run_cli("--json", "--region", "SG", "price", "--order", "O-000101")
        self.assertEqual(0, code)
        self.assertEqual("51.30", json.loads(out)["tax"])

    def test_unknown_order_reports_an_error(self):
        code, _, err = self.run_cli("price", "--order", "O-999999")
        self.assertEqual(1, code)
        self.assertIn("NOT_FOUND", err)

    def test_products(self):
        code, out, _ = self.run_cli("--json", "products")
        self.assertEqual(0, code)
        self.assertEqual(9, len(json.loads(out)["products"]))


if __name__ == "__main__":
    unittest.main()
