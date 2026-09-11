import json
import unittest
from pathlib import Path

from status_api import job_status


class StatusApiTest(unittest.TestCase):
    def test_reason_code_is_exposed(self):
        self.assertEqual("TIMEOUT", job_status("FAILED", 1.0, reason_code="TIMEOUT")["reasonCode"])

    def test_reason_code_defaults_to_null(self):
        self.assertIsNone(job_status("RUNNING", 0.5)["reasonCode"])

    def test_recorded_consumers_still_read_the_same_values(self):
        recorded = json.loads(Path("contract/recorded-v1.json").read_text(encoding="utf-8"))

        for entry in recorded:
            payload = job_status(entry["status"], entry["progress"])
            for key, value in entry.items():
                self.assertEqual(value, payload[key])


if __name__ == "__main__":
    unittest.main()