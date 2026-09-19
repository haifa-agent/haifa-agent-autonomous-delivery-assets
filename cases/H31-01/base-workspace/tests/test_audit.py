import json
import tempfile
import unittest
from pathlib import Path

from kiosk.app.audit import MAX_ENTRIES, AuditTrail


class AuditTrailTest(unittest.TestCase):
    def test_entries_are_kept_in_order(self):
        trail = AuditTrail()
        trail.record("add", "K-001", "2")
        trail.record("checkout", "-")

        self.assertEqual(["add", "checkout"], [entry.action for entry in trail.entries()])

    def test_the_trail_keeps_only_the_most_recent_entries(self):
        trail = AuditTrail()
        for index in range(MAX_ENTRIES + 10):
            trail.record("add", f"K-{index}")

        entries = trail.entries()

        self.assertEqual(MAX_ENTRIES, len(entries))
        self.assertEqual("K-10", entries[0].subject)

    def test_a_file_backed_trail_writes_one_line_per_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "trail", "audit.jsonl")
            trail = AuditTrail(path)
            trail.record("add", "K-001", "2")

            lines = path.read_text(encoding="utf-8").strip().splitlines()

            self.assertEqual(1, len(lines))
            self.assertEqual("K-001", json.loads(lines[0])["subject"])


if __name__ == "__main__":
    unittest.main()
