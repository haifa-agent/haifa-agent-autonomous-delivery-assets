import unittest

from api.schema import TASK_FIELDS
from api.service import TaskApi
from store.task_store import TaskStore


class TaskApiTest(unittest.TestCase):
    def test_priority_is_declared_in_the_schema(self):
        self.assertIn("priority", TASK_FIELDS)

    def test_priority_round_trips_through_the_api(self):
        api = TaskApi(TaskStore())

        created = api.create({"id": "t-1", "title": "first", "priority": 5})

        self.assertEqual(5, created["priority"])
        self.assertEqual(5, api.read("t-1")["priority"])

    def test_default_priority_is_applied(self):
        api = TaskApi(TaskStore())

        created = api.create({"id": "t-2", "title": "second"})

        self.assertEqual(3, created["priority"])
        self.assertEqual(3, api.read("t-2")["priority"])

    def test_existing_fields_are_unchanged(self):
        api = TaskApi(TaskStore())

        created = api.create({"id": "t-3", "title": "third", "priority": 1})

        self.assertEqual("t-3", created["id"])
        self.assertEqual("third", created["title"])
        self.assertEqual({"id", "title", "priority"}, set(api.read("t-3")))


if __name__ == "__main__":
    unittest.main()