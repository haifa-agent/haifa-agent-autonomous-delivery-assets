import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from kiosk.__main__ import main

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "catalog.json"


def run(*arguments, cache=None):
    out, err = io.StringIO(), io.StringIO()
    argv = ["--catalog", str(CATALOG), "--cache", str(cache or ROOT / "var" / "list_cache.json"), *arguments]
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class CliTest(unittest.TestCase):
    def test_list_prints_a_page_and_a_cursor(self):
        code, out, _ = run("list", "--size", "3")

        self.assertEqual(0, code)
        self.assertEqual(4, len(out.strip().splitlines()))
        self.assertIn("next-cursor:", out)

    def test_list_without_a_next_page_prints_no_cursor(self):
        code, out, _ = run("list", "--size", "50")

        self.assertEqual(0, code)
        self.assertNotIn("next-cursor:", out)

    def test_formats_lists_the_export_formats(self):
        code, out, _ = run("formats")

        self.assertEqual(0, code)
        self.assertIn("json", out.split())

    def test_export_writes_the_whole_catalogue(self):
        code, out, _ = run("export", "--format", "json")

        self.assertEqual(0, code)
        self.assertEqual(12, len(json.loads(out)["items"]))

    def test_an_unknown_export_format_fails_without_a_traceback(self):
        code, _, err = run("export", "--format", "wax-tablet")

        self.assertEqual(1, code)
        self.assertTrue(err.startswith("error: "))

    def test_list_can_be_narrowed_by_a_query(self):
        code, out, _ = run("list", "--query", "roasters", "--size", "50")

        self.assertEqual(0, code)
        self.assertEqual(4, len(out.strip().splitlines()))

    def test_list_can_be_narrowed_by_a_tag_and_a_price_ceiling(self):
        code, out, _ = run("list", "--tag", "tea", "--max-price", "3300", "--size", "50")

        self.assertEqual(0, code)
        self.assertEqual(2, len(out.strip().splitlines()))

    def test_restock_prints_the_popular_items_first(self):
        code, out, _ = run("restock", "--limit", "3")

        self.assertEqual(0, code)
        lines = out.strip().splitlines()
        self.assertEqual(3, len(lines))
        self.assertTrue(lines[0].startswith("K-002"))

    def test_cart_prints_a_receipt(self):
        code, out, _ = run("cart", "K-001=2")

        self.assertEqual(0, code)
        self.assertIn("total", out)

    def test_a_malformed_selection_is_rejected(self):
        code, _, err = run("cart", "K-001")

        self.assertEqual(2, code)
        self.assertIn("not a quantity", err)


if __name__ == "__main__":
    unittest.main()
