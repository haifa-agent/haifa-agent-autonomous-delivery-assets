import random


def _runner(handler, max_attempts=3):
    from kiosk.core.batch import BatchRunner

    return BatchRunner(handler, max_attempts)


def _rows(count, prefix="K"):
    return [{"sku": f"{prefix}-{index:04d}", "name": f"Item {index}", "price_cents": 100 + index} for index in range(count)]


@check("functional.everyRowReachesAVerdict")
def every_row_reaches_a_verdict():
    from kiosk.core.batch import OK, RETRY

    rows = _rows(12)
    doomed = {rows[3]["sku"], rows[7]["sku"]}
    result = _runner(lambda row, attempt: RETRY if row["sku"] in doomed else OK).run(rows)
    if result.handled != len(rows):
        return False, f"{len(rows)} rows in, {len(result.processed)} processed and {len(result.rejected)} rejected"
    return True


@check("functional.exhaustedRowIsRejectedWithAReason")
def exhausted_row_is_rejected_with_a_reason():
    from kiosk.core.batch import OK, RETRY

    rows = _rows(4)
    doomed = rows[2]["sku"]
    result = _runner(lambda row, attempt: RETRY if row["sku"] == doomed else OK).run(rows)
    rejected = {row["sku"]: reason for row, reason in result.rejected}
    if doomed not in rejected:
        return False, f"the row that never succeeded is not among the rejected rows: {sorted(rejected)}"
    if not str(rejected[doomed]).strip():
        return False, "the rejected row carries no reason"
    return True


@check("boundary.everyRowExhausts")
def every_row_exhausts():
    from kiosk.core.batch import RETRY

    rows = _rows(6)
    result = _runner(lambda row, attempt: RETRY).run(rows)
    if result.processed:
        return False, f"{len(result.processed)} rows were reported as processed"
    if len(result.rejected) != len(rows):
        return False, f"{len(rows)} rows in, {len(result.rejected)} rejected"
    return True


@check("boundary.mixedOutcomesAlwaysAddUp")
def mixed_outcomes_always_add_up():
    from kiosk.core.batch import OK, RETRY

    rng = random.Random(20260916)
    for round_number in range(80):
        rows = _rows(rng.randint(0, 25), prefix=f"R{round_number}")
        plan = {row["sku"]: rng.choice(["ok", "reject", "retry-1", "retry-2", "never"]) for row in rows}

        def handler(row, attempt, plan=plan):
            outcome = plan[row["sku"]]
            if outcome == "ok":
                return OK
            if outcome == "reject":
                return "not sellable"
            if outcome == "never":
                return RETRY
            return OK if attempt > int(outcome[-1]) else RETRY

        result = _runner(handler).run(rows)
        if result.handled != len(rows):
            return False, f"round {round_number}: {len(rows)} rows in, {result.handled} reached a verdict"
        seen = [row["sku"] for row in result.processed] + [row["sku"] for row, _ in result.rejected]
        if sorted(seen) != sorted(plan):
            return False, f"round {round_number}: the verdicts do not cover every row exactly once"
    return True


@check("boundary.singleAttemptBudget")
def single_attempt_budget():
    from kiosk.core.batch import RETRY

    rows = _rows(3)
    result = _runner(lambda row, attempt: RETRY, max_attempts=1).run(rows)
    if len(result.rejected) != len(rows):
        return False, f"with one attempt allowed, {len(result.rejected)} of {len(rows)} rows were rejected"
    if result.attempts != len(rows):
        return False, f"expected one attempt per row, got {result.attempts}"
    return True


@check("regression.attemptsAreStillCounted")
def attempts_are_still_counted():
    from kiosk.core.batch import OK, RETRY

    rows = _rows(4)
    clean = _runner(lambda row, attempt: OK).run(rows)
    retried = _runner(lambda row, attempt: OK if attempt > 1 else RETRY).run(rows)
    if clean.attempts != 4:
        return False, f"a clean batch of 4 took {clean.attempts} attempts"
    if retried.attempts != 8:
        return False, f"a batch of 4 retried once took {retried.attempts} attempts"
    return True


@check("regression.duplicatesAreStillDropped")
def duplicates_are_still_dropped():
    from kiosk.core.dedupe import drop_duplicates

    rows = [{"sku": "A", "n": 1}, {"sku": " a ", "n": 2}, {"sku": "B", "n": 3}, {"sku": "A", "n": 4}]
    kept = drop_duplicates(rows)
    if [row["n"] for row in kept] != [1, 3]:
        return False, f"drop_duplicates kept {[row['n'] for row in kept]}"
    return True


@check("regression.transientSinkFailureIsStillRetried")
def transient_sink_failure_is_still_retried():
    from kiosk.app.ingest import ingest

    rows = [{"sku": "K-1", "name": "One", "price_cents": 100}, {"sku": "K-2", "name": "Two", "price_cents": 200}]
    state = {"calls": 0}
    stored = []

    def sink(row):
        state["calls"] += 1
        if state["calls"] == 1:
            raise OSError("feed still being written")
        stored.append(row)

    report = ingest(rows, sink)
    if report.accepted != 2 or len(stored) != 2:
        return False, f"accepted {report.accepted}, stored {len(stored)}"
    return True
