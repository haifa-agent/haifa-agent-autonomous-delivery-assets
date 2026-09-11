import json
import unittest

from pipeline import run


class PipelineTest(unittest.TestCase):
    def test_existing_events_are_handled_and_projected(self):
        handled, lines = run([{"type": "JOB_SUBMITTED", "id": "j-1"}])

        self.assertEqual(["handled JOB_SUBMITTED"], handled)
        self.assertEqual([json.dumps({"type": "JOB_SUBMITTED", "id": "j-1"}, sort_keys=True)], lines)

    def test_retrying_event_is_dispatched(self):
        handled, _ = run([{"type": "JOB_RETRYING", "id": "j-2"}])

        self.assertEqual(["handled JOB_RETRYING"], handled)

    def test_retrying_event_is_projected(self):
        _, lines = run([{"type": "JOB_RETRYING", "id": "j-2"}])

        self.assertEqual([json.dumps({"type": "JOB_RETRYING", "id": "j-2"}, sort_keys=True)], lines)

    def test_unknown_events_are_rejected(self):
        with self.assertRaises(ValueError):
            run([{"type": "NOPE"}])


if __name__ == "__main__":
    unittest.main()