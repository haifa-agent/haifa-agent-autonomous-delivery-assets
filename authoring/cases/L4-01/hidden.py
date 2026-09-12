import json
import os


def _api(path=None):
    from opsdesk.api.tasks import TaskApi
    from opsdesk.store.task_store import TaskStore

    return TaskApi(TaskStore(path))


@check("functional.schemaDeclaresPriority")
def schema_declares_priority():
    from opsdesk.api.tasks import TaskApi

    schema = TaskApi.schema()
    return schema.get("priority") == "integer" and schema.get("id") == "string", repr(schema)


@check("functional.roundTripThroughApi")
def round_trip():
    api = _api()
    created = api.create({"id": "t-1", "title": "first", "priority": 5})
    api.create({"id": "t-2", "title": "second", "priority": 1})
    listed = {task["id"]: task.get("priority") for task in api.list()}
    return (
        created.get("priority") == 5 and api.read("t-1").get("priority") == 5 and listed == {"t-1": 5, "t-2": 1},
        f"created={created} listed={listed}",
    )


@check("boundary.defaultPriority")
def default_priority():
    api = _api()
    created = api.create({"id": "t-3", "title": "third"})
    return created.get("priority") == 3 and api.read("t-3").get("priority") == 3, repr(created)


@check("functional.persistsAcrossRestart")
def persists():
    path = os.path.join(SCRATCH, "tasks-restart.json")
    _api(path).create({"id": "t-4", "title": "fourth", "priority": 2, "done": True})
    reloaded = _api(path).read("t-4")
    return reloaded.get("priority") == 2 and reloaded.get("done") is True, repr(reloaded)


@check("regression.legacyStoreRows")
def legacy_rows():
    path = os.path.join(SCRATCH, "tasks-legacy.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"t-9": {"id": "t-9", "title": "old", "done": False}}, handle)
    api = _api(path)
    legacy = api.read("t-9")
    api.create({"id": "t-10", "title": "new", "priority": 4})
    reloaded = {task["id"]: task.get("priority") for task in _api(path).list()}
    return legacy.get("priority") == 3 and reloaded == {"t-9": 3, "t-10": 4}, f"legacy={legacy} reloaded={reloaded}"


@check("boundary.priorityRangeValidated")
def range_validated():
    api = _api()
    for invalid in (0, 6, -1, 42):
        try:
            api.create({"id": f"bad-{invalid}", "title": "bad", "priority": invalid})
            return False, f"priority {invalid} accepted"
        except ValueError:
            pass
        try:
            api.read(f"bad-{invalid}")
            return False, f"task with priority {invalid} was stored"
        except KeyError:
            pass
    return api.create({"id": "edge-1", "title": "e", "priority": 1})["priority"] == 1 and api.create(
        {"id": "edge-5", "title": "e", "priority": 5}
    )["priority"] == 5


@check("regression.existingBehaviour")
def existing_behaviour():
    api = _api()
    for payload in ({"id": "x"}, {"title": "x"}, {"id": "x", "title": "x", "colour": "red"}, {"id": "x", "title": " "}):
        try:
            api.create(payload)
            return False, f"{payload} accepted"
        except ValueError:
            pass
    created = api.create({"id": "t-5", "title": "fifth", "done": True})
    return created.get("id") == "t-5" and created.get("title") == "fifth" and created.get("done") is True, repr(created)
