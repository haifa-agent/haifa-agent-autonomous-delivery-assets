import unittest

from kiosk.app.ingest import ingest
from kiosk.core.errors import KioskError

ROWS = [
    {"sku": "K-001", "name": "One", "price_cents": 100},
    {"sku": "K-002", "name": "Two", "price_cents": 200},
]


class IngestTest(unittest.TestCase):
    def test_good_rows_reach_the_sink(self):
        stored = []
        report = ingest(ROWS, stored.append)

        self.assertEqual(2, report.accepted)
        self.assertEqual(ROWS, stored)
        self.assertEqual([], report.rejected)

    def test_a_repeated_sku_is_dropped_before_the_sink(self):
        stored = []
        report = ingest([*ROWS, {"sku": "K-001", "name": "One again", "price_cents": 100}], stored.append)

        self.assertEqual(1, report.duplicates_dropped)
        self.assertEqual(2, len(stored))

    def test_a_row_that_breaks_the_contract_is_rejected(self):
        stored = []
        report = ingest([*ROWS, {"sku": "", "name": "No sku", "price_cents": 1}], stored.append)

        self.assertEqual(2, report.accepted)
        self.assertEqual(1, len(report.rejected))
        self.assertEqual("empty sku", report.rejected[0][1])

    def test_a_sink_that_refuses_a_row_rejects_it(self):
        def sink(row):
            raise KioskError("sink is full")

        report = ingest(ROWS, sink)

        self.assertEqual(0, report.accepted)
        self.assertEqual(2, len(report.rejected))

    def test_a_transient_sink_failure_is_retried(self):
        attempts = {"count": 0}
        stored = []

        def sink(row):
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise OSError("feed still being written")
            stored.append(row)

        report = ingest(ROWS, sink)

        self.assertEqual(2, report.accepted)
        self.assertEqual(3, report.attempts)


if __name__ == "__main__":
    unittest.main()
