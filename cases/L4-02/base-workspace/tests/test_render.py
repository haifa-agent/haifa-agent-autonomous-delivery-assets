import unittest

from opsdesk.reporting.render import Section, render


class RenderTest(unittest.TestCase):
    def test_rows_are_rendered(self):
        self.assertEqual(
            ["section: orders", "  id=1"],
            render([Section("orders", [{"key": "id", "value": 1}])]),
        )

    def test_empty_rows_use_the_fallback(self):
        self.assertEqual(["section: orders", "  (no rows)"], render([Section("orders", [])]))

    def test_missing_rows_use_the_same_fallback(self):
        self.assertEqual(["section: orders", "  (no rows)"], render([Section("orders", None)]))

    def test_sections_keep_their_order(self):
        self.assertEqual(
            ["section: a", "  k=v", "section: b", "  (no rows)"],
            render([Section("a", [{"key": "k", "value": "v"}]), Section("b", [])]),
        )


if __name__ == "__main__":
    unittest.main()
