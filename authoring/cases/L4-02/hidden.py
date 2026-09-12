import json

RETRY = {"type": "JOB_RETRYING", "id": "j-7", "attempt": 2}


def _pipeline():
    from opsdesk.api.jobs import JobPipeline

    return JobPipeline()


@check("functional.retryingDispatched")
def retrying_dispatched():
    handled, _ = _pipeline().run([dict(RETRY)])
    return handled == ["handled JOB_RETRYING"], repr(handled)


@check("functional.retryingProjected")
def retrying_projected():
    pipeline = _pipeline()
    events = [{"type": "JOB_SUBMITTED", "id": "j-7"}, dict(RETRY), {"type": "JOB_HEARTBEAT", "id": "j-7"}]
    _, lines = pipeline.run(events)
    expected = [json.dumps(events[0], sort_keys=True), json.dumps(RETRY, sort_keys=True)]
    return lines == expected and pipeline.log.lines() == expected, repr(lines)


@check("functional.summaryCountsRetrying")
def summary_counts():
    summary = _pipeline().summary([dict(RETRY), dict(RETRY), {"type": "JOB_FAILED"}, {"type": "JOB_HEARTBEAT"}])
    return (
        summary.get("retrying") == 2 and summary.get("failed") == 1 and summary.get("submitted") == 0,
        repr(summary),
    )


@check("regression.existingEvents")
def existing_events():
    pipeline = _pipeline()
    events = [
        {"type": "JOB_SUBMITTED", "id": "a"},
        {"type": "JOB_RUNNING", "id": "a"},
        {"type": "JOB_HEARTBEAT", "id": "a"},
        {"type": "JOB_FAILED", "id": "a"},
        {"type": "JOB_COMPLETED", "id": "b"},
    ]
    handled, lines = pipeline.run(events)
    summary = pipeline.summary(events)
    return (
        handled == [f"handled {event['type']}" for event in events]
        and lines == [json.dumps(event, sort_keys=True) for event in events if event["type"] != "JOB_HEARTBEAT"]
        and {key: summary.get(key) for key in ("submitted", "running", "completed", "failed")}
        == {"submitted": 1, "running": 1, "completed": 1, "failed": 1},
        f"handled={handled} summary={summary}",
    )


@check("boundary.unknownTypesRejected")
def unknown_types():
    for event_type in ("JOB_EXPLODED", "job_retrying", "RETRYING"):
        try:
            _pipeline().run([{"type": event_type}])
            return False, f"{event_type} accepted by run"
        except ValueError:
            pass
        try:
            _pipeline().summary([{"type": event_type}])
            return False, f"{event_type} accepted by summary"
        except ValueError:
            pass
    return True
