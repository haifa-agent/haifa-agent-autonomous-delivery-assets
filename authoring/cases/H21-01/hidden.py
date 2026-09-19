import csv
import io as _io
import json
import subprocess
import sys


def _catalogue():
    from kiosk.app.repository import CatalogRepository

    return CatalogRepository().items()


def _csv_text():
    from kiosk.app.exporters import export

    return export("csv", _catalogue())


def _parsed():
    """Return (header, {sku: row}) of the CSV export, read back through a CSV reader."""
    rows = list(csv.reader(_io.StringIO(_csv_text(), newline="")))
    rows = [row for row in rows if row]
    header = rows[0]
    return header, {row[0]: dict(zip(header, row)) for row in rows[1:]}


def _json_rows():
    from kiosk.app.exporters.json_export import export_json

    payload = json.loads(export_json(_catalogue()))
    return {row["sku"]: row for row in payload["items"]}


def _cli(*arguments):
    completed = subprocess.run(
        [sys.executable, "-m", "kiosk", *arguments],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return completed.returncode, completed.stdout, completed.stderr


@check("functional.csvFormatIsOffered")
def csv_format_is_offered():
    from kiosk.app.exporters import available

    if "csv" not in available():
        return False, f"the offered formats are {available()}"
    code, out, err = _cli("formats")
    if code != 0 or "csv" not in out.split():
        return False, f"formats exited {code} and printed {out.strip()!r}"
    code, out, err = _cli("export", "--format", "csv")
    if code != 0 or not out.strip():
        return False, f"export --format csv exited {code}: {err.strip()[:120]}"
    return True


@check("functional.headerIsThePublishedFieldOrder")
def header_is_the_published_field_order():
    from kiosk.app.exporters.json_export import FIELDS

    header, _ = _parsed()
    if header != list(FIELDS):
        return False, f"header is {header}, the published field order is {list(FIELDS)}"
    return True


@check("functional.oneLinePerCatalogueItem")
def one_line_per_catalogue_item():
    code, csv_out, err = _cli("export", "--format", "csv")
    if code != 0:
        return False, f"export --format csv exited {code}: {err.strip()[:120]}"
    rows = [row for row in csv.reader(_io.StringIO(csv_out, newline="")) if row]
    _, json_out, _ = _cli("export", "--format", "json")
    expected = [row["sku"] for row in json.loads(json_out)["items"]]
    got = [row[0] for row in rows[1:]]
    if got != expected:
        return False, f"the csv export lists {got[:4]}..., the json export lists {expected[:4]}..."
    if len(got) != len(_catalogue()):
        return False, f"{len(got)} lines for {len(_catalogue())} catalogue items"
    return True


@check("boundary.missingValuesUseThePlaceholder")
def missing_values_use_the_placeholder():
    from kiosk.core.format_rules import MISSING

    _, rows = _parsed()
    expected = _json_rows()
    blank = [
        (sku, field)
        for sku, row in expected.items()
        for field, value in row.items()
        if value == MISSING
    ]
    if not blank:
        return False, "the fixture catalogue no longer carries a missing value"
    for sku, field in blank:
        if rows[sku][field] != MISSING:
            return False, f"{sku}.{field} is {rows[sku][field]!r}, the product renders a missing value as {MISSING!r}"
    return True


@check("boundary.longNamesAreClipped")
def long_names_are_clipped():
    from kiosk.core.format_rules import NAME_LIMIT

    _, rows = _parsed()
    expected = _json_rows()
    clipped = [sku for sku, row in expected.items() if len(row["name"]) == NAME_LIMIT and row["name"].endswith("...")]
    if not clipped:
        return False, "the fixture catalogue no longer carries an over-long name"
    for sku in clipped:
        if rows[sku]["name"] != expected[sku]["name"]:
            return False, f"{sku} exported the name {rows[sku]['name']!r} instead of {expected[sku]['name']!r}"
    return True


@check("boundary.timestampsAreUtc")
def timestamps_are_utc():
    _, rows = _parsed()
    expected = _json_rows()
    stamped = [sku for sku, row in expected.items() if row["updated"].endswith("Z")]
    if not stamped:
        return False, "the fixture catalogue no longer carries a timestamp"
    for sku in stamped:
        if rows[sku]["updated"] != expected[sku]["updated"]:
            return False, f"{sku} exported {rows[sku]['updated']!r} instead of {expected[sku]['updated']!r}"
    return True


@check("boundary.separatorsAndQuotesSurviveARoundTrip")
def separators_and_quotes_survive_a_round_trip():
    _, rows = _parsed()
    expected = _json_rows()
    tricky = [sku for sku, row in expected.items() if "," in row["name"] or '"' in row["name"]]
    if len(tricky) < 2:
        return False, "the fixture catalogue no longer carries a separator and a quote in a name"
    for sku in tricky:
        if rows[sku]["name"] != expected[sku]["name"]:
            return False, f"{sku} read back as {rows[sku]['name']!r} instead of {expected[sku]['name']!r}"
    return True


@check("regression.jsonExportIsUnchanged")
def json_export_is_unchanged():
    from kiosk.app.exporters import export
    from kiosk.app.exporters.json_export import FIELDS

    payload = json.loads(export("json", _catalogue()))
    if payload.get("fields") != list(FIELDS):
        return False, f"the JSON export now publishes {payload.get('fields')}"
    if len(payload.get("items", [])) != len(_catalogue()):
        return False, "the JSON export no longer covers the whole catalogue"
    code, out, _ = _cli("export", "--format", "json")
    if code != 0 or json.loads(out).get("fields") != list(FIELDS):
        return False, f"export --format json exited {code}"
    return True
