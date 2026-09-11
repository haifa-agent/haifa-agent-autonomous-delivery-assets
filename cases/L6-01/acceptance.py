#!/usr/bin/env python3
"""Black-box acceptance for ladder case L6-01; prints one JSON line on stdout."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parent
BASELINE = CASE_ROOT / "base-workspace"
CASE_ID = "L6-01"
CASE_VERSION = "1.0.0"
ALLOWED_CHANGES = {"cli.py", "inventory.py", "importer.py", "csv_import.py", "csv_importer.py"}
MAX_CHANGED_FILES = 5
HIDDEN_SCRIPT = """import json, subprocess, sys, tempfile
from pathlib import Path
workspace = sys.argv[1]
NEWLINE = chr(10)
def run(arguments):
    return subprocess.run([sys.executable, "-m", "cli", *arguments], cwd=workspace, capture_output=True, text=True, timeout=180)
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    good = root / "good.csv"
    good.write_text(NEWLINE.join(["sku,name,quantity", "a-1,item a,2", "b-2,item b,1"]) + NEWLINE, encoding="utf-8")
    mixed = root / "mixed.csv"
    mixed.write_text(NEWLINE.join(["sku,name,quantity", "a-1,item a,2", ",missing sku,1", "c-3,item c,not-a-number", "b-2,item b,1"]) + NEWLINE, encoding="utf-8")
    bad_header = root / "bad.csv"
    bad_header.write_text(NEWLINE.join(["sku,name", "x,item"]) + NEWLINE, encoding="utf-8")
    store = root / "store.json"
    partial_store = root / "partial.json"
    ok = run(["import", "--store", str(store), str(good)])
    items = json.loads(store.read_text(encoding="utf-8")) if store.exists() else {}
    partial = run(["import", "--store", str(partial_store), str(mixed)])
    partial_items = json.loads(partial_store.read_text(encoding="utf-8")) if partial_store.exists() else {}
    missing = run(["import", "--store", str(root / "s2.json"), str(root / "absent.csv")])
    header = run(["import", "--store", str(root / "s3.json"), str(bad_header)])
checks = {
    "functional.importsRowsAndPersists": ok.returncode == 0 and "imported=2 failed=0" in ok.stdout and sorted(items) == ["a-1", "b-2"] and int(str(items["a-1"]["quantity"])) == 2,
    "functional.perRowSummary": ok.stdout.count("ok a-1") == 1 and ok.stdout.count("ok b-2") == 1,
    "boundary.partialFailureExitsNonZero": partial.returncode != 0 and "imported=2 failed=2" in partial.stdout and sorted(partial_items) == ["a-1", "b-2"] and partial.stdout.count("error ") == 2,
    "regression.missingFileReported": missing.returncode != 0 and missing.stderr.strip() != "",
    "regression.wrongHeaderRejected": header.returncode != 0 and header.stderr.strip() != "",
}
print(json.dumps(checks))"""

CHECK_NAMES = (
    "hygiene.testsUnchanged",
    "hygiene.scopeRespected",
    "hygiene.changeBudget",
    "functional.visibleTests",
    "functional.importsRowsAndPersists",
    "functional.perRowSummary",
    "boundary.partialFailureExitsNonZero",
    "regression.missingFileReported",
    "regression.wrongHeaderRejected",
)


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
        timeout=600,
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