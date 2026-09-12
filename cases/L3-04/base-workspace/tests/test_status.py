import unittest

from opsdesk.api.alerts import failure_alert
from opsdesk.api.status import job_status


class StatusApiTest(unittest.TestCase):
    def test_running_job_payload(self):
        payload = job_status("j-1", "RUNNING", 0.25)

        self.assertEqual("j-1", payload["jobId"])
        self.assertEqual("RUNNING", payload["state"])
        self.assertEqual(0.25, payload["progress"])
        self.assertIsNone(payload["error"])

    def test_failed_job_carries_its_error(self):
        payload = job_status("j-2", "FAILED", 0.5, error="disk full")

        self.assertEqual("FAILED", payload["state"])
        self.assertEqual("disk full", payload["error"])

    def test_error_is_only_allowed_for_failed_jobs(self):
        with self.assertRaises(ValueError):
            job_status("j-3", "RUNNING", 0.5, error="boom")

    def test_invalid_states_and_progress_are_rejected(self):
        with self.assertRaises(ValueError):
            job_status("j-4", "PAUSED", 0.5)
        with self.assertRaises(ValueError):
            job_status("j-4", "RUNNING", 1.5)

    def test_failure_alert_quotes_the_error(self):
        self.assertEqual(
            {"channel": "email", "message": "job j-9 failed at 40%: out of memory"},
            failure_alert("j-9", 0.4, "out of memory"),
        )


if __name__ == "__main__":
    unittest.main()
