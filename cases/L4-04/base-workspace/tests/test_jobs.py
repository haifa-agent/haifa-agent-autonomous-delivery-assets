import json
import unittest

from opsdesk.api.jobs import JobPipeline


class JobPipelineTest(unittest.TestCase):
    def test_events_are_dispatched_and_projected(self):
        pipeline = JobPipeline()

        handled, lines = pipeline.run([{"type": "JOB_SUBMITTED", "id": "j-1"}, {"type": "JOB_COMPLETED", "id": "j-1"}])

        self.assertEqual(["handled JOB_SUBMITTED", "handled JOB_COMPLETED"], handled)
        self.assertEqual(json.dumps({"id": "j-1", "type": "JOB_SUBMITTED"}, sort_keys=True), lines[0])
        self.assertEqual(lines, pipeline.log.lines())

    def test_heartbeats_are_dispatched_but_not_projected(self):
        handled, lines = JobPipeline().run([{"type": "JOB_HEARTBEAT", "id": "j-1"}])

        self.assertEqual(["handled JOB_HEARTBEAT"], handled)
        self.assertEqual([], lines)

    def test_summary_counts_job_events(self):
        summary = JobPipeline().summary(
            [{"type": "JOB_SUBMITTED"}, {"type": "JOB_FAILED"}, {"type": "JOB_HEARTBEAT"}, {"type": "JOB_SUBMITTED"}]
        )

        self.assertEqual(2, summary["submitted"])
        self.assertEqual(0, summary["running"])
        self.assertEqual(0, summary["completed"])
        self.assertEqual(1, summary["failed"])

    def test_unknown_event_types_are_rejected(self):
        with self.assertRaises(ValueError):
            JobPipeline().run([{"type": "JOB_EXPLODED"}])


if __name__ == "__main__":
    unittest.main()
