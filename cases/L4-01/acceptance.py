#!/usr/bin/env python3
"""Black-box acceptance for ladder case L3-01; prints one JSON line on stdout."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parent
BASELINE = CASE_ROOT / "base-workspace"
CASE_ID = "L4-01"
CASE_VERSION = "1.0.0"
ALLOWED_CHANGES = {"api/schema.py", "api/service.py", "core/task.py", "adapter/json_adapter.py", "store/task_store.py"}
MAX_CHANGED_FILES = 5
CHECK_NAMES = ("hygiene.testsUnchanged", "hygiene.scopeRespected", "hygiene.changeBudget", "functional.visibleTests", "functional.schemaDeclaresPriority", "functional.roundTripThroughApi", "boundary.defaultPriorityApplied", "regression.requiredFieldsEnforced", "regression.existingFieldsUntouched")
HIDDEN_SCRIPT = """import json, sys
sys.path.insert(0, sys.argv[1])
from adapter.json_adapter import from_json, to_json
from api.schema import TASK_FIELDS
from api.service import TaskApi
from core.task import Task
from store.task_store import TaskStore
api = TaskApi(TaskStore())
created = api.create({"id": "t-1", "title": "first", "priority": 5})
default_created = api.create({"id": "t-2", "title": "second"})
required_enforced = False
try:
    api.create({})
except ValueError:
    required_enforced = True
checks = {
    "functional.schemaDeclaresPriority": "priority" in TASK_FIELDS,
    "functional.roundTripThroughApi": created.get("priority") == 5 and api.read("t-1").get("priority") == 5,
    "boundary.defaultPriorityApplied": default_created.get("priority") == 3 and api.read("t-2").get("priority") == 3,
    "regression.requiredFieldsEnforced": required_enforced,
    "regression.existingFieldsUntouched": created.get("id") == "t-1" and created.get("title") == "first" and to_json(Task("x", "y", 4))["priority"] == 4 and from_json({"id": "z", "title": "w", "priority": 2}).priority == 2,
}
print(json.dumps(checks))"""


def digest_tree(root: Path) -> dict[str, str]:
    digests: dict[str, str] = {}
    if not root.is_dir():
        return digests
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        digests[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def changed_sources(workspace: Path) -> set[str]:
    baseline = {path: digest for path, digest in digest_tree(BASELINE).items() if not path.startswith("tests/")}
    candidate = {path: digest for path, digest in digest_tree(workspace).items() if not path.startswith("tests/")}
    return {path for path in set(baseline) | set(candidate) if baseline.get(path) != candidate.get(path)}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: acceptance.py <workspace>", file=sys.stderr)
        return 2
    workspace = Path(sys.argv[1]).resolve()
    started = time.monotonic()
    checks = {name: False for name in CHECK_NAMES}
    changed = changed_sources(workspace)

    checks["hygiene.testsUnchanged"] = digest_tree(workspace / "tests") == digest_tree(BASELINE / "tests")
    checks["hygiene.scopeRespected"] = changed <= ALLOWED_CHANGES
    checks["hygiene.changeBudget"] = 0 < len(changed) <= MAX_CHANGED_FILES

    visible = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=180,
    )
    checks["functional.visibleTests"] = visible.returncode == 0

    hidden = subprocess.run(
        [sys.executable, "-c", HIDDEN_SCRIPT, str(workspace)],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=180,
    )
    try:
        for name, value in json.loads(hidden.stdout).items():
            if name in checks:
                checks[name] = bool(value)
    except (json.JSONDecodeError, ValueError):
        pass

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
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())