# Responses recorded from the previous API version, replayed the way third-party clients call it.
RECORDED_V1 = [
    (("j-1", "QUEUED", 0), {}, {"jobId": "j-1", "state": "QUEUED", "progress": 0.0, "error": None}),
    (("j-2", "RUNNING", 0.25), {}, {"jobId": "j-2", "state": "RUNNING", "progress": 0.25, "error": None}),
    (("j-3", "FAILED", 0.5, "disk full"), {}, {"jobId": "j-3", "state": "FAILED", "progress": 0.5, "error": "disk full"}),
    (("j-4", "FAILED", 1.0), {"error": "timeout after 30s"}, {"jobId": "j-4", "state": "FAILED", "progress": 1.0, "error": "timeout after 30s"}),
    ((), {"job_id": "j-5", "state": "COMPLETED", "progress": 1}, {"jobId": "j-5", "state": "COMPLETED", "progress": 1.0, "error": None}),
]


def _status(*arguments, **keywords):
    from opsdesk.api.status import job_status

    return job_status(*arguments, **keywords)


@check("functional.reasonCodeExposed")
def reason_code_exposed():
    with_error = _status("j-6", "FAILED", 0.5, error="took too long", reason_code="TIMEOUT")
    without_error = _status("j-7", "FAILED", 0.9, reason_code="OUT_OF_MEMORY")
    return (
        with_error.get("reasonCode") == "TIMEOUT"
        and with_error.get("error") == "took too long"
        and without_error.get("reasonCode") == "OUT_OF_MEMORY",
        repr(with_error),
    )


@check("functional.nonFailedStatusesExposeNull")
def non_failed_null():
    for state in ("QUEUED", "RUNNING", "COMPLETED"):
        payload = _status("j-8", state, 0.5)
        if "reasonCode" not in payload or payload["reasonCode"] is not None:
            return False, repr(payload)
    failed = _status("j-9", "FAILED", 0.5, error="boom")
    return "reasonCode" in failed and failed["reasonCode"] is None, repr(failed)


@check("boundary.reasonCodeValidation")
def reason_code_validation():
    for state, code in (("RUNNING", "TIMEOUT"), ("COMPLETED", "OK"), ("FAILED", "timeout"), ("FAILED", ""), ("FAILED", "TIME OUT")):
        try:
            _status("j-10", state, 0.5, reason_code=code)
            return False, f"state={state} reason_code={code!r} accepted"
        except ValueError:
            pass
    return True


@check("regression.recordedV1Contract")
def recorded_v1():
    for arguments, keywords, recorded in RECORDED_V1:
        payload = _status(*arguments, **keywords)
        for key, value in recorded.items():
            if key not in payload or payload[key] != value or type(payload[key]) is not type(value):
                return False, f"call {arguments or keywords}: {key}={payload.get(key)!r}, recorded {value!r}"
    return True


@check("regression.alertsUnchanged")
def alerts_unchanged():
    from opsdesk.api.alerts import failure_alert

    return failure_alert("j-9", 0.4, "out of memory") == {
        "channel": "email",
        "message": "job j-9 failed at 40%: out of memory",
    }
