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
CASE_ID = "L4-04"
CASE_VERSION = "1.0.0"
ALLOWED_CHANGES = {"status_service.py", "adapter_dto.py", "status_api.py"}
MAX_CHANGED_FILES = 3
CHECK_NAMES = ("hygiene.testsUnchanged", "hygiene.scopeRespected", "hygiene.changeBudget", "functional.visibleTests", "functional.reasonCodeExposed", "boundary.reasonCodeDefaultsToNull", "regression.recordedV1Compatible", "regression.existingKeysPreserved", "functional.wireMappingStable")
HIDDEN_SCRIPT = """import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from adapter_dto import to_wire
from status_api import job_status
from status_service import describe
recorded = json.loads(Path(sys.argv[1], "contract", "recorded-v1.json").read_text(encoding="utf-8"))
compatible = True
for entry in recorded:
    payload = job_status(entry["status"], entry["progress"])
    if not set(entry) <= set(payload):
        compatible = False
    for key, value in entry.items():
        if payload.get(key) != value or type(payload.get(key)) is not type(value):
            compatible = False
checks = {
    "functional.reasonCodeExposed": job_status("FAILED", 1.0, reason_code="TIMEOUT").get("reasonCode") == "TIMEOUT",
    "boundary.reasonCodeDefaultsToNull": job_status("RUNNING", 0.5).get("reasonCode", "missing") is None,
    "regression.recordedV1Compatible": compatible,
    "regression.existingKeysPreserved": job_status("RUNNING", 0.5)["status"] == "RUNNING" and job_status("RUNNING", 0.5)["progress"] == 0.5,
    "functional.wireMappingStable": to_wire(describe("COMPLETED", 1.0, "OK")) == {"status": "COMPLETED", "progress": 1.0, "reasonCode": "OK"},
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