#!/usr/bin/env python3
"""Black-box acceptance for ladder case L4-01; prints one JSON line on stdout.

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
CASE_ID = "L4-01"
CASE_VERSION = "2.0.0"
TEST_ROOTS = ('tests',)
SOURCE_SUFFIXES = ('.py',)
EDITABLE = ('opsdesk/*',)
PROTECTED = ()
CHANGE_BUDGET = (4, 7)
VISIBLE_TESTS = ('-m', 'unittest', 'discover', '-s', 'tests')
VISIBLE_TIMEOUT_SECONDS = 180
CHECK_TIMEOUT_SECONDS = 60
HIDDEN_CHECKS = (
    "functional.schemaDeclaresPriority",
    "functional.roundTripThroughApi",
    "boundary.defaultPriority",
    "functional.persistsAcrossRestart",
    "regression.legacyStoreRows",
    "boundary.priorityRangeValidated",
    "regression.existingBehaviour",
    "constraint.layerDirection",
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

import ast as _ast
from pathlib import Path as _Path

_LAYERS = {
    "util": set(),
    "core": {"util"},
    "config": {"util"},
    "adapter": {"core", "util"},
    "store": {"core", "util"},
    "reporting": {"core", "util"},
    "api": {"adapter", "config", "core", "reporting", "store", "util"},
}


def _layer_violations():
    package_root = _Path(WORKSPACE, "opsdesk")
    violations = []
    for path in sorted(package_root.rglob("*.py")):
        relative = path.relative_to(package_root)
        if len(relative.parts) < 2:
            continue
        layer = relative.parts[0]
        if layer not in _LAYERS:
            violations.append(f"{relative.as_posix()}: unknown layer opsdesk.{layer}")
            continue
        package = ["opsdesk", *relative.parts[:-1]]
        for node in _ast.walk(_ast.parse(path.read_text(encoding="utf-8"))):
            modules = []
            if isinstance(node, _ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, _ast.ImportFrom):
                base = package[: len(package) - node.level + 1] if node.level else []
                module = ".".join(base + ([node.module] if node.module else []))
                modules = [module] + [f"{module}.{alias.name}" for alias in node.names]
            for module in modules:
                parts = module.split(".")
                if parts[0] != "opsdesk" or len(parts) < 2:
                    continue
                target = parts[1]
                if target == "__main__" or (target in _LAYERS and target != layer and target not in _LAYERS[layer]):
                    violations.append(f"{relative.as_posix()} imports {module}")
    return sorted(set(violations))


@check("constraint.layerDirection")
def layer_direction():
    violations = _layer_violations()
    return not violations, "; ".join(violations[:3])


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
