#!/usr/bin/env python3
"""Black-box acceptance for ladder case L1-02; prints one JSON line on stdout."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parent
BASELINE = CASE_ROOT / "base-workspace"
CASE_ID = "L1-02"
CASE_VERSION = "1.0.0"
ALLOWED_CHANGES = {"dates.py"}
CHECK_NAMES = (
    "hygiene.testsUnchanged",
    "hygiene.scopeRespected",
    "functional.visibleTests",
    "functional.leapYears",
    "boundary.centuryRule",
    "boundary.commonYears",
    "functional.monthLengths",
    "boundary.monthRange",
)
HIDDEN_SCRIPT = """
import json, sys
sys.path.insert(0, sys.argv[1])
from dates import days_in_month, is_leap_year
checks = {
    "functional.leapYears": is_leap_year(2000) and is_leap_year(2024) and is_leap_year(1600) and is_leap_year(2400),
    "boundary.centuryRule": not is_leap_year(1900) and not is_leap_year(2100) and not is_leap_year(1700),
    "boundary.commonYears": not is_leap_year(2023) and not is_leap_year(2025),
    "functional.monthLengths": days_in_month(2024, 2) == 29 and days_in_month(1900, 2) == 28 and days_in_month(2023, 4) == 30,
}
try:
    days_in_month(2023, 13)
    checks["boundary.monthRange"] = False
except ValueError:
    checks["boundary.monthRange"] = True
print(json.dumps(checks))
"""


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
        timeout=120,
    )
    checks["functional.visibleTests"] = visible.returncode == 0

    hidden = subprocess.run(
        [sys.executable, "-c", HIDDEN_SCRIPT, str(workspace)],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=120,
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