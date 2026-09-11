import unittest

from report import Section, render


class ReportTest(unittest.TestCase):
    def test_rows_are_rendered(self):
        self.assertEqual(
            ["section: orders", "  id=1"],
            render([Section("orders", [{"key": "id", "value": 1}])]),
        )

    def test_empty_rows_use_the_existing_fallback(self):
        self.assertEqual(["section: orders", "  (no rows)"], render([Section("orders", [])]))

    def test_missing_rows_use_the_same_fallback(self):
        self.assertEqual(["section: orders", "  (no rows)"], render([Section("orders", None)]))

    def test_sections_are_rendered_in_order(self):
        self.assertEqual(
            ["section: a", "  (no rows)", "section: b", "  (no rows)"],
            render([Section("a", []), Section("b", None)]),
        )


if __name__ == "__main__":
    unittest.main()