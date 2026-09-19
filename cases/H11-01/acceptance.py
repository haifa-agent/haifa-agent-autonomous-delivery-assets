#!/usr/bin/env python3
"""Black-box acceptance for ladder case H11-01; prints one JSON line on stdout.

Every hidden check runs in its own interpreter so that one crashing or hanging check cannot
zero the others. Hygiene only guards what the case promises: existing tests and protected
files stay byte-identical, changed source files stay inside the editable scope and the change
budget. New test files and tool caches (``.pytest_cache``, ``__pycache__``...) are allowed.
The final stderr line is ``DIAGNOSTICS {...}`` with the reason of every failed check.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import secrets
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parent
BASELINE = CASE_ROOT / "base-workspace"
CASE_ID = "H11-01"
CASE_VERSION = "1.0.0"
TEST_ROOTS = ('tests',)
SOURCE_SUFFIXES = ('.py',)
EDITABLE = ('kiosk/*', 'var/*')
PROTECTED = ()
CHANGE_BUDGET = (1, 2)
VISIBLE_TESTS = ('-m', 'unittest', 'discover', '-s', 'tests')
VISIBLE_TIMEOUT_SECONDS = 180
CHECK_TIMEOUT_SECONDS = 60
HIDDEN_CHECKS = (
    "functional.everyRowReachesAVerdict",
    "functional.exhaustedRowIsRejectedWithAReason",
    "boundary.everyRowExhausts",
    "boundary.mixedOutcomesAlwaysAddUp",
    "boundary.singleAttemptBudget",
    "regression.attemptsAreStillCounted",
    "regression.duplicatesAreStillDropped",
    "regression.transientSinkFailureIsStillRetried",
)
IGNORED_DIRS = frozenset(
    {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".hypothesis",
        ".tox",
        ".nox",
        ".git",
        ".hg",
        ".svn",
        ".idea",
        ".vscode",
        ".venv",
        "venv",
        "node_modules",
        "target",
        "build",
        "dist",
    }
)
IGNORED_SUFFIXES = (".pyc", ".pyo", ".class")
TEST_FILE_PATTERNS = ("test_*.py", "*_test.py", "conftest.py", "*Test.java", "*Tests.java")

HIDDEN_SCRIPT = r'''
import json
import os
import sys

WORKSPACE = os.path.abspath(sys.argv[1])
CHECK_NAME = sys.argv[2]
NONCE = sys.argv[3]
SCRATCH = sys.argv[4]
sys.path.insert(0, WORKSPACE)
CHECKS = {}


def check(name):
    def register(function):
        CHECKS[name] = function
        return function

    return register

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


def _main():
    try:
        outcome = CHECKS[CHECK_NAME]()
        if isinstance(outcome, tuple):
            ok, detail = bool(outcome[0]), str(outcome[1])
        else:
            ok, detail = outcome is True, "" if outcome is True else "returned " + repr(outcome)
    except BaseException as error:  # candidate code may raise anything, including SystemExit
        ok, detail = False, type(error).__name__ + ": " + str(error)
    sys.stdout.flush()
    print(NONCE + json.dumps({"ok": ok, "detail": detail[:300]}), flush=True)


_main()
'''


def child_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONHASHSEED"] = "0"
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop("PYTHONPATH", None)
    return env


def digest_tree(root: Path) -> dict[str, str]:
    digests: dict[str, str] = {}
    if not root.is_dir():
        return digests
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in IGNORED_DIRS and not name.endswith(".egg-info"))
        for filename in sorted(filenames):
            if filename.endswith(IGNORED_SUFFIXES):
                continue
            path = Path(directory, filename)
            digests[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def is_test_path(relative: str) -> bool:
    if any(relative == root or relative.startswith(root + "/") for root in TEST_ROOTS):
        return True
    return any(fnmatch.fnmatchcase(relative.rsplit("/", 1)[-1], pattern) for pattern in TEST_FILE_PATTERNS)


def is_source(relative: str) -> bool:
    return relative.endswith(SOURCE_SUFFIXES) and not is_test_path(relative)


def is_editable(relative: str) -> bool:
    if any(fnmatch.fnmatchcase(relative, pattern) for pattern in PROTECTED):
        return False
    return any(fnmatch.fnmatchcase(relative, pattern) for pattern in EDITABLE)


def hygiene(workspace: Path) -> tuple[dict[str, bool], dict[str, str], list[str]]:
    baseline = digest_tree(BASELINE)
    candidate = digest_tree(workspace)
    checks: dict[str, bool] = {}
    details: dict[str, str] = {}

    changed_tests = sorted(path for path, digest in baseline.items() if is_test_path(path) and candidate.get(path) != digest)
    checks["hygiene.existingTestsUnchanged"] = not changed_tests
    if changed_tests:
        details["hygiene.existingTestsUnchanged"] = "modified or deleted: " + ", ".join(changed_tests[:5])

    changed_protected = sorted(
        path
        for path, digest in baseline.items()
        if not is_test_path(path) and not is_editable(path) and candidate.get(path) != digest
    )
    checks["hygiene.protectedFilesUnchanged"] = not changed_protected
    if changed_protected:
        details["hygiene.protectedFilesUnchanged"] = "modified or deleted: " + ", ".join(changed_protected[:5])

    changed_sources = sorted(
        path
        for path in set(baseline) | set(candidate)
        if is_source(path) and baseline.get(path) != candidate.get(path)
    )
    outside = [path for path in changed_sources if not is_editable(path)]
    checks["hygiene.scopeRespected"] = not outside
    if outside:
        details["hygiene.scopeRespected"] = "outside the editable scope: " + ", ".join(outside[:5])

    low, high = CHANGE_BUDGET
    checks["hygiene.changeBudget"] = low <= len(changed_sources) <= high
    if not checks["hygiene.changeBudget"]:
        details["hygiene.changeBudget"] = f"{len(changed_sources)} source files changed, budget {low}..{high}"
    return checks, details, changed_sources


def visible_tests(workspace: Path) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            [sys.executable, *VISIBLE_TESTS],
            cwd=workspace,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=VISIBLE_TIMEOUT_SECONDS,
            env=child_env(),
        )
    except subprocess.TimeoutExpired:
        return False, f"visible suite timed out after {VISIBLE_TIMEOUT_SECONDS}s"
    if completed.returncode == 0:
        return True, ""
    tail = [line for line in completed.stderr.splitlines() if line.strip()][-1:]
    return False, "visible suite red: " + (tail[0] if tail else f"exit {completed.returncode}")


def hidden_checks(workspace: Path) -> tuple[dict[str, bool], dict[str, str]]:
    results: dict[str, bool] = {}
    details: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="ladder-acceptance-", ignore_cleanup_errors=True) as directory:
        script = Path(directory, "hidden_checks.py")
        script.write_text(HIDDEN_SCRIPT, encoding="utf-8")
        scratch = Path(directory, "scratch")
        scratch.mkdir()
        for name in HIDDEN_CHECKS:
            nonce = "HIDDEN-" + secrets.token_hex(8) + " "
            try:
                completed = subprocess.run(
                    [sys.executable, str(script), str(workspace), name, nonce, str(scratch)],
                    cwd=workspace,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=CHECK_TIMEOUT_SECONDS,
                    env=child_env(),
                )
            except subprocess.TimeoutExpired:
                results[name] = False
                details[name] = f"timed out after {CHECK_TIMEOUT_SECONDS}s"
                continue
            payload = None
            for line in completed.stdout.splitlines():
                if line.startswith(nonce):
                    payload = json.loads(line[len(nonce):])
            if payload is None:
                tail = [line for line in completed.stderr.splitlines() if line.strip()][-1:]
                results[name] = False
                details[name] = f"no result (exit {completed.returncode}) " + (tail[0] if tail else "")
                continue
            results[name] = bool(payload.get("ok"))
            if not results[name]:
                details[name] = str(payload.get("detail", ""))
    return results, details


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: acceptance.py <workspace>", file=sys.stderr)
        return 2
    workspace = Path(sys.argv[1]).resolve()
    started = time.monotonic()

    checks, details, changed_sources = hygiene(workspace)
    if VISIBLE_TESTS is not None:
        checks["functional.visibleTests"], visible_detail = visible_tests(workspace)
        if visible_detail:
            details["functional.visibleTests"] = visible_detail
    hidden_results, hidden_details = hidden_checks(workspace)
    checks.update(hidden_results)
    details.update(hidden_details)

    failures = [name for name, passed in checks.items() if not passed]
    payload = {
        "schemaVersion": 1,
        "caseId": CASE_ID,
        "caseVersion": CASE_VERSION,
        "status": "PASSED" if not failures else "FAILED",
        "passed": not failures,
        "checks": checks,
        "failures": failures,
        "durationMillis": int((time.monotonic() - started) * 1000),
    }
    workspace_text = str(workspace)
    diagnostics = {
        "changedSources": changed_sources,
        "details": {name: text.replace(workspace_text, "<workspace>")[:300] for name, text in details.items()},
    }
    print("DIAGNOSTICS " + json.dumps(diagnostics, ensure_ascii=True, sort_keys=True), file=sys.stderr)
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
