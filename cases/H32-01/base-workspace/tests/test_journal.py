import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from depot.store.journal import append_event, read_events, verify


class JournalTest(unittest.TestCase):
    def test_append_and_read(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "journal.jsonl"
            append_event(path, {"id": "O-000101", "event": "created"})
            append_event(path, {"id": "O-000102", "event": "cancelled"})
            events = read_events(path)
            self.assertEqual(2, len(events))
            self.assertEqual("O-000101", events[0]["id"])
            self.assertEqual([], verify(path))

    def test_tampering_is_detected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "journal.jsonl"
            append_event(path, {"id": "O-000101", "event": "created"})
            text = path.read_text(encoding="utf-8").replace("created", "shipped")
            path.write_text(text, encoding="utf-8")
            self.assertEqual(["O-000101"], verify(path))


if __name__ == "__main__":
    unittest.main()
