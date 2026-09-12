import subprocess
import sys

TRANSACTIONS = [
    {"account": "x", "amount": 5, "booked_at": "2026-04-02 08:00:00"},
    {"account": "z", "amount": 1, "booked_at": "2026-04-02 09:30:00"},
    {"account": "y", "amount": 9, "booked_at": "2026-04-03 08:00:00"},
]


@check("functional.missingRowsFallback")
def missing_rows():
    from opsdesk.reporting.render import Section, render

    return render([Section("orders", None)]) == ["section: orders", "  (no rows)"]


@check("regression.emptyRowsFallback")
def empty_rows():
    from opsdesk.reporting.render import Section, render

    return render([Section("orders", [])]) == ["section: orders", "  (no rows)"]


@check("regression.rowsRendered")
def rows_rendered():
    from opsdesk.reporting.render import Section, render

    lines = render([Section("a", None), Section("b", [{"key": "k", "value": 7}]), Section("c", [])])
    return lines == ["section: a", "  (no rows)", "section: b", "  k=7", "section: c", "  (no rows)"], repr(lines)


@check("functional.everyAccountReported")
def every_account():
    from opsdesk.reporting.nightly import build_nightly_report

    lines = build_nightly_report(TRANSACTIONS, "2026-04-02", ["x", "y", "z"])
    expected = [
        "nightly report 2026-04-02",
        "section: x",
        "  08:00:00=5",
        "section: y",
        "  (no rows)",
        "section: z",
        "  09:30:00=1",
        "total=6",
    ]
    return lines == expected, repr(lines)


@check("functional.cliNightlyReport")
def cli_nightly():
    completed = subprocess.run(
        [sys.executable, "-m", "opsdesk", "nightly", "2026-02-10"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        timeout=60,
    )
    expected = [
        "nightly report 2026-02-10",
        "section: a",
        "  09:15:00=3",
        "  23:59:59=4",
        "section: b",
        "  (no rows)",
        "section: c",
        "  (no rows)",
        "total=7",
    ]
    return completed.returncode == 0 and completed.stdout.splitlines() == expected, repr(completed.stdout[-200:])


@check("regression.accountOrderKept")
def account_order():
    from opsdesk.reporting.nightly import build_nightly_report

    lines = build_nightly_report(TRANSACTIONS, "2026-04-03", ["z", "y", "x"])
    sections = [line for line in lines if line.startswith("section: ")]
    return sections == ["section: z", "section: y", "section: x"] and lines[-1] == "total=9", repr(lines)
