import tempfile
import unittest
from pathlib import Path

from opsdesk.api.tasks import TaskApi
from opsdesk.store.task_store import TaskStore


class TaskApiTest(unittest.TestCase):
    def test_created_task_can_be_read_and_listed(self):
        api = TaskApi(TaskStore())

        created = api.create({"id": "t-1", "title": "first"})

        self.assertEqual("t-1", created["id"])
        self.assertEqual("first", created["title"])
        self.assertFalse(created["done"])
        self.assertEqual(created, api.read("t-1"))
        self.assertEqual([created], api.list())

    def test_required_fields_are_enforced(self):
        with self.assertRaises(ValueError):
            TaskApi(TaskStore()).create({"id": "t-1"})

    def test_unknown_fields_are_rejected(self):
        with self.assertRaises(ValueError):
            TaskApi(TaskStore()).create({"id": "t-1", "title": "x", "colour": "red"})

    def test_blank_title_is_rejected(self):
        with self.assertRaises(ValueError):
            TaskApi(TaskStore()).create({"id": "t-1", "title": "  "})

    def test_tasks_survive_a_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.json"
            TaskApi(TaskStore(path)).create({"id": "t-1", "title": "first", "done": True})

            reloaded = TaskApi(TaskStore(path)).read("t-1")

        self.assertTrue(reloaded["done"])

    def test_schema_lists_the_public_fields(self):
        schema = TaskApi.schema()

        self.assertEqual("string", schema["id"])
        self.assertEqual("boolean", schema["done"])


if __name__ == "__main__":
    unittest.main()
