#!/usr/bin/env python3
"""Black-box acceptance for ladder case L2-02; prints one JSON line on stdout."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parent
BASELINE = CASE_ROOT / "base-workspace"
CASE_ID = "L2-02"
CASE_VERSION = "1.0.0"
ALLOWED_CHANGES = {"models.py", "state_machine.py", "views.py"}
CHECK_NAMES = ("hygiene.testsUnchanged", "hygiene.scopeRespected", "functional.visibleTests", "functional.cancelledReachable", "boundary.finishedCannotCancel", "boundary.cancelledIsTerminal", "regression.existingTransitions", "functional.cancelledRendering", "boundary.cancelledValue")
HIDDEN_SCRIPT = """import json, sys
sys.path.insert(0, sys.argv[1])
from models import OrderStatus
from state_machine import can_transition
from views import render
checks = {
    "functional.cancelledReachable": can_transition(OrderStatus.NEW, OrderStatus.CANCELLED) and can_transition(OrderStatus.PAID, OrderStatus.CANCELLED),
    "boundary.finishedCannotCancel": not can_transition(OrderStatus.FINISHED, OrderStatus.CANCELLED),
    "boundary.cancelledIsTerminal": not can_transition(OrderStatus.CANCELLED, OrderStatus.PAID) and not can_transition(OrderStatus.CANCELLED, OrderStatus.NEW),
    "regression.existingTransitions": can_transition(OrderStatus.NEW, OrderStatus.PAID) and can_transition(OrderStatus.PAID, OrderStatus.SHIPPED) and can_transition(OrderStatus.SHIPPED, OrderStatus.FINISHED) and not can_transition(OrderStatus.NEW, OrderStatus.SHIPPED),
    "functional.cancelledRendering": render(OrderStatus.CANCELLED) == "Cancelled" and render(OrderStatus.NEW) == "New order",
    "boundary.cancelledValue": OrderStatus.CANCELLED.value == "CANCELLED",
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

    checks["hygiene.testsUnchanged"] = digest_tree(workspace / "tests") == digest_tree(BASELINE / "tests")
    checks["hygiene.scopeRespected"] = changed_sources(workspace) <= ALLOWED_CHANGES

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