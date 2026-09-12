import random
import subprocess
import sys
from datetime import datetime, timedelta


def _tx(account, amount, when):
    return {"account": account, "amount": amount, "booked_at": when}


@check("functional.midnightBelongsToNextDay")
def midnight_next_day():
    from opsdesk.core.aggregation import nightly_totals, rows_for

    transactions = [_tx("a", 5, "2026-02-11 00:00:00")]
    return (
        nightly_totals(transactions, "2026-02-10") == {}
        and nightly_totals(transactions, "2026-02-11") == {"a": 5}
        and rows_for(transactions, "2026-02-10", "a") is None
    )


@check("boundary.lastSecondOfDayCounted")
def last_second():
    from opsdesk.core.aggregation import nightly_totals

    transactions = [_tx("z", 2, "2026-02-10 23:59:59"), _tx("z", 3, "2026-02-10 00:00:00")]
    return nightly_totals(transactions, "2026-02-10") == {"z": 5} and nightly_totals(transactions, "2026-02-09") == {}


@check("boundary.randomizedDayPartition")
def randomized_partition():
    from opsdesk.core.aggregation import nightly_totals

    rng = random.Random(20260911)
    first_day = datetime(2026, 2, 27)
    transactions = []
    for index in range(600):
        moment = first_day + timedelta(days=rng.randint(0, 5))
        if index % 3:
            moment += timedelta(seconds=rng.randint(0, 86399))
        transactions.append(_tx(rng.choice("abc"), rng.randint(1, 50), moment.strftime("%Y-%m-%d %H:%M:%S")))
    grand = {}
    for transaction in transactions:
        grand[transaction["account"]] = grand.get(transaction["account"], 0) + transaction["amount"]
    summed = {}
    for offset in range(6):
        day = (first_day + timedelta(days=offset)).strftime("%Y-%m-%d")
        for account, amount in nightly_totals(transactions, day).items():
            summed[account] = summed.get(account, 0) + amount
    return summed == grand, f"per-day sum {summed} != total {grand}"


@check("functional.cliNightlyTotals")
def cli_totals():
    def run(day):
        completed = subprocess.run(
            [sys.executable, "-m", "opsdesk", "nightly", day],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return completed.stdout.splitlines()

    first, second, third = run("2026-02-10"), run("2026-02-11"), run("2026-02-12")
    return (
        first[-1:] == ["total=7"] and second[-1:] == ["total=13"] and third[-1:] == ["total=7"]
        and "  00:00:00=5" not in first,
        f"totals {first[-1:]} {second[-1:]} {third[-1:]}",
    )


@check("regression.dayWindowContract")
def day_window_contract():
    from opsdesk.util.timewindow import day_window, parse_timestamp

    start, end = day_window("2026-02-28")
    return (
        start == datetime(2026, 2, 28)
        and end == datetime(2026, 3, 1)
        and parse_timestamp("2026-02-28 13:14:15") == datetime(2026, 2, 28, 13, 14, 15)
    )
