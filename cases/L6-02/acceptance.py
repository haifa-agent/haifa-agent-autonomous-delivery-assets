#!/usr/bin/env python3
"""Black-box acceptance for ladder case L6-02; prints one JSON line on stdout.

Compiles the bundled Java project with javac and drives the export CLI twice to verify
that an interrupted run is resumable. Maven itself is exercised only when a `mvn`
executable is available; the POM is always checked structurally.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parent
BASELINE = CASE_ROOT / "base-workspace"
CASE_ID = "L6-02"
CASE_VERSION = "1.0.0"
ALLOWED_CHANGES = {
    "src/main/java/io/haifa/batch/ExportMain.java",
    "src/main/java/io/haifa/batch/ExportState.java",
}
MAX_CHANGED_FILES = 2
CHECK_NAMES = (
    "hygiene.testsUnchanged",
    "hygiene.scopeRespected",
    "hygiene.changeBudget",
    "functional.compilesWithJavac",
    "functional.interruptedRunExits75",
    "functional.resumesWithoutLossOrDuplicates",
    "boundary.resumeFromFirstBatch",
    "regression.completedRunHasAllRecords",
    "regression.pomDeclaresJava17",
    "functional.mavenBuilds",
)
EXPECTED = [f"rec-{index:02d}" for index in range(1, 13)]


def digest_tree(root: Path) -> dict[str, str]:
    digests: dict[str, str] = {}
    if not root.is_dir():
        return digests
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        digests[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def changed_sources(workspace: Path) -> set[str]:
    baseline = digest_tree(BASELINE)
    candidate = digest_tree(workspace)
    baseline = {p: d for p, d in baseline.items() if not p.startswith(("tests/", "src/test/", "target/"))}
    candidate = {p: d for p, d in candidate.items() if not p.startswith(("tests/", "src/test/", "target/"))}
    return {path for path in set(baseline) | set(candidate) if baseline.get(path) != candidate.get(path)}


def java_sources(workspace: Path) -> list[str]:
    root = workspace / "src" / "main" / "java"
    return [str(path) for path in sorted(root.rglob("*.java"))]


def compile_workspace(workspace: Path, classes: Path) -> subprocess.CompletedProcess[str]:
    javac = shutil.which("javac")
    if javac is None:
        raise RuntimeError("javac is required to run this case")
    classes.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        [javac, "-d", str(classes), *java_sources(workspace)],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=300,
    )


def run_export(classes: Path, output: Path, batches: int, interrupt_after: int | None = None) -> subprocess.CompletedProcess[str]:
    java = shutil.which("java")
    if java is None:
        raise RuntimeError("java is required to run this case")
    command = [
        java,
        "-cp",
        str(classes),
        "io.haifa.batch.ExportMain",
        "--output",
        str(output),
        "--batches",
        str(batches),
    ]
    if interrupt_after is not None:
        command += ["--interrupt-after-batch", str(interrupt_after)]
    return subprocess.run(command, capture_output=True, text=True, timeout=300)


def exported_lines(output: Path) -> list[str]:
    if not output.exists():
        return []
    return [line for line in output.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: acceptance.py <workspace>", file=sys.stderr)
        return 2
    workspace = Path(sys.argv[1]).resolve()
    started = time.monotonic()
    checks = {name: False for name in CHECK_NAMES}
    changed = changed_sources(workspace)

    checks["hygiene.testsUnchanged"] = digest_tree(workspace / "tests") == digest_tree(BASELINE / "tests") and digest_tree(
        workspace / "src" / "test" / "java"
    ) == digest_tree(BASELINE / "src" / "test" / "java")
    checks["hygiene.scopeRespected"] = changed <= ALLOWED_CHANGES
    checks["hygiene.changeBudget"] = 0 < len(changed) <= MAX_CHANGED_FILES

    with tempfile.TemporaryDirectory() as directory:
        scratch = Path(directory)
        classes = scratch / "classes"
        compiled = compile_workspace(workspace, classes)
        checks["functional.compilesWithJavac"] = compiled.returncode == 0

        resumed = scratch / "resumed.jsonl"
        interrupted = run_export(classes, resumed, 4, 2)
        checks["functional.interruptedRunExits75"] = interrupted.returncode == 75
        resumed_again = run_export(classes, resumed, 4)
        checks["functional.resumesWithoutLossOrDuplicates"] = (
            resumed_again.returncode == 0 and exported_lines(resumed) == EXPECTED
        )

        first_batch = scratch / "first-batch.jsonl"
        run_export(classes, first_batch, 4, 1)
        run_export(classes, first_batch, 4)
        checks["boundary.resumeFromFirstBatch"] = exported_lines(first_batch) == EXPECTED

        complete = scratch / "complete.jsonl"
        completed = run_export(classes, complete, 4)
        checks["regression.completedRunHasAllRecords"] = completed.returncode == 0 and exported_lines(complete) == EXPECTED

    pom = ET.parse(workspace / "pom.xml").getroot()
    release = None
    for properties in pom.iter():
        if properties.tag.rsplit("}", 1)[-1] == "properties":
            for child in properties:
                if child.tag.rsplit("}", 1)[-1] == "maven.compiler.release":
                    release = (child.text or "").strip()
    checks["regression.pomDeclaresJava17"] = release == "17"

    maven = shutil.which("mvn")
    if maven is None:
        checks["functional.mavenBuilds"] = checks["regression.pomDeclaresJava17"]
    else:
        built = subprocess.run(
            [maven, "-q", "-DskipTests", "package"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=600,
        )
        checks["functional.mavenBuilds"] = built.returncode == 0

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