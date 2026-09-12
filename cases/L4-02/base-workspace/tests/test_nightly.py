import unittest

from opsdesk.reporting.nightly import build_nightly_report

TRANSACTIONS = [
    {"account": "a", "amount": 3, "booked_at": "2026-03-01 10:00:00"},
    {"account": "a", "amount": 4, "booked_at": "2026-03-01 11:30:00"},
    {"account": "b", "amount": 9, "booked_at": "2026-03-02 12:00:00"},
]


class NightlyReportTest(unittest.TestCase):
    def test_every_account_gets_a_section(self):
        self.assertEqual(
            [
                "nightly report 2026-03-01",
                "section: a",
                "  10:00:00=3",
                "  11:30:00=4",
                "section: b",
                "  (no rows)",
                "total=7",
            ],
            build_nightly_report(TRANSACTIONS, "2026-03-01", ["a", "b"]),
        )


if __name__ == "__main__":
    unittest.main()
