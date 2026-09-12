import os
import shutil
import subprocess
import xml.etree.ElementTree as ElementTree
from pathlib import Path

EXPECTED = [f"rec-{index:02d}" for index in range(1, 13)]
CLASSES = Path(SCRATCH, "classes")
MARKER = CLASSES / ".compiled"


def _tool(name):
    found = shutil.which(name)
    if found is None:
        raise RuntimeError(f"{name} is required to run this case")
    return found


def _compile():
    if MARKER.exists():
        return True, ""
    sources = sorted(str(path) for path in Path(WORKSPACE, "src", "main", "java").rglob("*.java"))
    CLASSES.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [_tool("javac"), "--release", "17", "-encoding", "UTF-8", "-d", str(CLASSES), *sources],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if completed.returncode == 0:
        MARKER.write_text("ok", encoding="utf-8")
        return True, ""
    return False, (completed.stderr.strip().splitlines() or ["javac failed"])[0]


def _export(output, batches=4, interrupt=None):
    ok, detail = _compile()
    if not ok:
        raise RuntimeError("compilation failed: " + detail)
    command = [_tool("java"), "-cp", str(CLASSES), "io.haifa.batch.ExportMain", "--output", str(output), "--batches", str(batches)]
    if interrupt is not None:
        command += ["--interrupt-after-batch", str(interrupt)]
    return subprocess.run(command, capture_output=True, text=True, timeout=120).returncode


def _lines(output):
    if not output.exists():
        return []
    return [line for line in output.read_text(encoding="utf-8").splitlines() if line.strip()]


def _output(name):
    directory = Path(SCRATCH, "runs", name)
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "export.jsonl"


@check("functional.compilesWithJavac")
def compiles():
    return _compile()


@check("functional.interruptedRunExits75")
def interrupted_exits_75():
    output = _output("interrupted")
    code = _export(output, 4, 2)
    return code == 75 and _lines(output) == EXPECTED[:6], f"exit {code}, lines {_lines(output)}"


@check("functional.resumesWithoutLossOrDuplicates")
def resumes():
    output = _output("resume")
    first = _export(output, 4, 2)
    second = _export(output, 4)
    return first == 75 and second == 0 and _lines(output) == EXPECTED, f"exits {first}/{second}, lines {_lines(output)}"


@check("boundary.resumeFromFirstBatch")
def resume_first_batch():
    output = _output("first")
    first = _export(output, 4, 1)
    second = _export(output, 4)
    return first == 75 and second == 0 and _lines(output) == EXPECTED, f"exits {first}/{second}, lines {_lines(output)}"


@check("boundary.interruptAtLastBatch")
def interrupt_last_batch():
    output = _output("last")
    first = _export(output, 4, 4)
    second = _export(output, 4)
    return first == 75 and second == 0 and _lines(output) == EXPECTED, f"exits {first}/{second}, lines {_lines(output)}"


@check("boundary.repeatedInterruptions")
def repeated_interruptions():
    output = _output("repeated")
    codes = [_export(output, 4, 1), _export(output, 4, 3), _export(output, 4)]
    return codes == [75, 75, 0] and _lines(output) == EXPECTED, f"exits {codes}, lines {_lines(output)}"


@check("boundary.rerunAfterCompletionIsNoop")
def rerun_after_completion():
    output = _output("rerun")
    codes = [_export(output, 4), _export(output, 4)]
    return codes == [0, 0] and _lines(output) == EXPECTED, f"exits {codes}, lines {_lines(output)}"


@check("boundary.outputsAreIndependent")
def outputs_independent():
    first, second = _output("independent-a"), Path(SCRATCH, "runs", "independent-a", "other.jsonl")
    codes = [_export(first, 4, 2), _export(second, 4), _export(first, 4)]
    return codes == [75, 0, 0] and _lines(first) == EXPECTED and _lines(second) == EXPECTED, f"exits {codes}"


@check("regression.uninterruptedRunUnchanged")
def uninterrupted():
    output = _output("plain")
    code = _export(output, 4)
    single = _output("single")
    single_code = _export(single, 1)
    return code == 0 and _lines(output) == EXPECTED and single_code == 0 and _lines(single) == EXPECTED[:3]


@check("regression.pomJava17WithoutRuntimeDependencies")
def pom_java17():
    root = ElementTree.parse(os.path.join(WORKSPACE, "pom.xml")).getroot()

    def local(tag):
        return tag.rsplit("}", 1)[-1]

    release = None
    runtime_dependencies = []
    for element in root.iter():
        if local(element.tag) == "maven.compiler.release":
            release = (element.text or "").strip()
        if local(element.tag) == "dependency":
            scope = next((child.text for child in element if local(child.tag) == "scope"), "compile")
            if (scope or "compile").strip() not in ("test", "provided"):
                runtime_dependencies.append(next((child.text for child in element if local(child.tag) == "artifactId"), "?"))
    return release == "17" and not runtime_dependencies, f"release={release} runtime dependencies={runtime_dependencies}"
