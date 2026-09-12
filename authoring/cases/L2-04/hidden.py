import csv
import io
import json
import subprocess
import sys

TRICKY = [
    {"sku": "a,1", "name": 'say "hi"', "note": "line1\nline2", "quantity": 3},
    {"sku": "b-2", "name": "plain", "note": "", "quantity": 0},
]


def _cli(*arguments):
    return subprocess.run([sys.executable, "-m", "cli", *arguments], cwd=WORKSPACE, capture_output=True, text=True, timeout=60)


def _parse(text):
    return list(csv.reader(io.StringIO(text)))


@check("functional.csvRegistered")
def csv_registered():
    from exporters import exporter_for

    return callable(exporter_for("csv"))


@check("functional.headerAndRowOrder")
def header_and_rows():
    from exporters import exporter_for

    rows = [{"z": 1, "a": "x"}, {"z": 2, "a": "y"}, {"z": 3, "a": "w"}]
    text = exporter_for("csv")(rows)
    return text.rstrip("\n").split("\n") == ["z,a", "1,x", "2,y", "3,w"], repr(text)


@check("boundary.csvQuoting")
def csv_quoting():
    from exporters import exporter_for

    parsed = _parse(exporter_for("csv")(TRICKY))
    expected = [["sku", "name", "note", "quantity"], ["a,1", 'say "hi"', "line1\nline2", "3"], ["b-2", "plain", "", "0"]]
    return parsed == expected, repr(parsed)


@check("boundary.emptyRows")
def empty_rows():
    from exporters import exporter_for

    return exporter_for("csv")([]).strip() == ""


@check("functional.cliFormatFlag")
def cli_format_flag():
    completed = _cli("--format", "csv")
    return completed.returncode == 0 and completed.stdout.splitlines() == ["sku,quantity", "a-1,2", "b-2,1"], repr(completed.stdout)


@check("regression.jsonOutputByteIdentical")
def json_output():
    from exporters import exporter_for

    expected = json.dumps([{"sku": "a-1", "quantity": 2}, {"sku": "b-2", "quantity": 1}], sort_keys=True)
    default = _cli()
    explicit = _cli("--format", "json")
    return (
        default.stdout == expected + "\n"
        and explicit.stdout == expected + "\n"
        and exporter_for("json")(TRICKY) == json.dumps(TRICKY, sort_keys=True)
    ), repr(default.stdout)


@check("boundary.unknownFormatRejected")
def unknown_format():
    from exporters import exporter_for

    try:
        exporter_for("xml")
        return False, "exporter_for('xml') did not raise"
    except ValueError:
        pass
    completed = _cli("--format", "xml")
    return completed.returncode == 2 and completed.stderr.strip() != "" and completed.stdout.strip() == "", (
        f"exit {completed.returncode}, stderr {completed.stderr[-120:]!r}"
    )
