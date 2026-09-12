import unittest

from opsdesk.core.aggregation import nightly_totals, rows_for

TRANSACTIONS = [
    {"account": "a", "amount": 3, "booked_at": "2026-03-01 10:00:00"},
    {"account": "a", "amount": 4, "booked_at": "2026-03-01 11:30:00"},
    {"account": "b", "amount": 6, "booked_at": "2026-03-01 12:00:00"},
    {"account": "b", "amount": 9, "booked_at": "2026-03-02 12:00:00"},
]


class AggregationTest(unittest.TestCase):
    def test_amounts_are_summed_per_account(self):
        self.assertEqual({"a": 7, "b": 6}, nightly_totals(TRANSACTIONS, "2026-03-01"))

    def test_other_days_are_excluded(self):
        self.assertEqual({"b": 9}, nightly_totals(TRANSACTIONS, "2026-03-02"))

    def test_rows_of_an_account(self):
        self.assertEqual(
            [{"key": "10:00:00", "value": 3}, {"key": "11:30:00", "value": 4}],
            rows_for(TRANSACTIONS, "2026-03-01", "a"),
        )

    def test_account_without_activity_has_no_rows(self):
        self.assertIsNone(rows_for(TRANSACTIONS, "2026-03-02", "a"))


if __name__ == "__main__":
    unittest.main()
