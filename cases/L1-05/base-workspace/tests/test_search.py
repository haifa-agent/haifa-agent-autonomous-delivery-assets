import unittest

from search import matches


class SearchTest(unittest.TestCase):
    def test_uppercase_records_match_lowercase_query(self):
        records = ["Alpha report", "beta report"]

        self.assertEqual(["Alpha report"], matches("alpha", records))

    def test_query_case_is_ignored(self):
        records = ["Quarterly PLAN", "notes"]

        self.assertEqual(["Quarterly PLAN"], matches("Plan", records))

    def test_empty_query_returns_nothing(self):
        self.assertEqual([], matches("", ["anything"]))

    def test_order_is_preserved(self):
        records = ["b-1", "B-2", "c"]

        self.assertEqual(["b-1", "B-2"], matches("b", records))


if __name__ == "__main__":
    unittest.main()