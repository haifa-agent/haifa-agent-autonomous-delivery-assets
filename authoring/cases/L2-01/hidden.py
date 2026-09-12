import json
import subprocess
import sys

STEP_LINES = ["verbose: loading", "verbose: aggregating", "verbose: writing"]


def _cli(*arguments):
    return subprocess.run(
        [sys.executable, "-m", "cli", *arguments],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _report(path):
    return json.dumps({"outputPath": path, "sections": ["expenses", "categories"]}, sort_keys=True)


@check("functional.verboseStepLines")
def verbose_step_lines():
    completed = _cli("--output", "r.json", "--verbose")
    lines = completed.stdout.splitlines()
    return completed.returncode == 0 and lines == STEP_LINES + [_report("r.json")], repr(completed.stdout[:200])


@check("regression.quietOutputByteIdentical")
def quiet_output():
    first = _cli("--output", "r.json")
    default = _cli()
    return (
        first.returncode == 0
        and first.stdout == _report("r.json") + "\n"
        and default.stdout == _report("report.json") + "\n",
        repr(first.stdout[:200]),
    )


@check("boundary.flagPositionIndependent")
def flag_position():
    expected = STEP_LINES + [_report("x.json")]
    for arguments in (("--verbose", "--output", "x.json"), ("--output", "x.json", "--verbose"), ("--extra", "--verbose", "--output", "x.json")):
        completed = _cli(*arguments)
        if completed.returncode != 0 or completed.stdout.splitlines() != expected:
            return False, f"{arguments}: {completed.stdout[:200]!r}"
    return True


@check("regression.unknownArgumentsIgnored")
def unknown_arguments():
    completed = _cli("--whatever", "--output", "a.json", "positional")
    return completed.returncode == 0 and completed.stdout == _report("a.json") + "\n", repr(completed.stdout[:200])
