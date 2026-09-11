import unittest

from aggregate import nightly_totals


class AggregateTest(unittest.TestCase):
    def test_daytime_transactions_are_summed(self):
        transactions = [
            {"account": "a", "amount": 3, "booked_at": "2026-02-10 12:00:00"},
            {"account": "a", "amount": 4, "booked_at": "2026-02-10 23:59:59"},
        ]

        self.assertEqual({"a": 7}, nightly_totals(transactions, "2026-02-10"))

    def test_midnight_transaction_belongs_to_the_next_night_only(self):
        transactions = [{"account": "a", "amount": 5, "booked_at": "2026-02-11 00:00:00"}]

        self.assertEqual({}, nightly_totals(transactions, "2026-02-10"))
        self.assertEqual({"a": 5}, nightly_totals(transactions, "2026-02-11"))

    def test_multiple_accounts_are_aggregated(self):
        transactions = [
            {"account": "a", "amount": 2, "booked_at": "2026-02-10 08:00:00"},
            {"account": "b", "amount": 6, "booked_at": "2026-02-10 09:00:00"},
        ]

        self.assertEqual({"a": 2, "b": 6}, nightly_totals(transactions, "2026-02-10"))


if __name__ == "__main__":
    unittest.main()