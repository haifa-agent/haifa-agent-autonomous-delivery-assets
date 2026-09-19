import unittest

from kiosk.core.batch import OK, RETRY, BatchRunner

ROWS = [{"sku": "A"}, {"sku": "B"}, {"sku": "C"}]


class BatchRunnerTest(unittest.TestCase):
    def test_every_row_of_a_clean_batch_is_processed(self):
        result = BatchRunner(lambda row, attempt: OK).run(ROWS)

        self.assertEqual(ROWS, result.processed)
        self.assertEqual([], result.rejected)
        self.assertEqual(3, result.attempts)

    def test_a_rejected_row_keeps_its_reason(self):
        result = BatchRunner(lambda row, attempt: "bad row").run(ROWS)

        self.assertEqual([], result.processed)
        self.assertEqual([(row, "bad row") for row in ROWS], result.rejected)

    def test_a_transient_failure_is_retried_until_it_succeeds(self):
        seen: dict[str, int] = {}

        def handler(row, attempt):
            seen[row["sku"]] = attempt
            return OK if attempt > 1 else RETRY

        result = BatchRunner(handler, max_attempts=3).run(ROWS)

        self.assertEqual(3, len(result.processed))
        self.assertEqual({"A": 2, "B": 2, "C": 2}, seen)
        self.assertEqual(6, result.attempts)

    def test_an_empty_batch_produces_an_empty_result(self):
        result = BatchRunner(lambda row, attempt: OK).run([])

        self.assertEqual(0, result.handled)
        self.assertEqual(0, result.attempts)

    def test_max_attempts_must_be_positive(self):
        with self.assertRaises(ValueError):
            BatchRunner(lambda row, attempt: OK, max_attempts=0)


if __name__ == "__main__":
    unittest.main()
