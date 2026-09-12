import calendar
import random

RNG_SEED = 20260911


@check("functional.centuryRule")
def century_rule():
    from dates import is_leap_year

    leap = all(is_leap_year(year) for year in (1600, 2000, 2400))
    common = not any(is_leap_year(year) for year in (1700, 1800, 1900, 2100, 2200, 2300))
    return leap and common


@check("boundary.randomizedYears")
def randomized_years():
    from dates import is_leap_year

    rng = random.Random(RNG_SEED)
    for year in [rng.randint(1, 9999) for _ in range(2000)] + list(range(1896, 1905)):
        if bool(is_leap_year(year)) != calendar.isleap(year):
            return False, f"is_leap_year({year}) returned {is_leap_year(year)}"
    return True


@check("functional.februaryLengths")
def february_lengths():
    from dates import days_in_month

    rng = random.Random(RNG_SEED + 1)
    for year in [rng.randint(1, 9999) for _ in range(500)] + [1900, 2000, 2100]:
        if days_in_month(year, 2) != calendar.monthrange(year, 2)[1]:
            return False, f"days_in_month({year}, 2) returned {days_in_month(year, 2)}"
    return True


@check("regression.otherMonthsUnchanged")
def other_months():
    from dates import days_in_month

    rng = random.Random(RNG_SEED + 2)
    for year in [rng.randint(1, 9999) for _ in range(100)]:
        for month in (1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12):
            if days_in_month(year, month) != calendar.monthrange(year, month)[1]:
                return False, f"days_in_month({year}, {month}) returned {days_in_month(year, month)}"
    return True


@check("regression.monthRangeValidation")
def month_range():
    from dates import days_in_month

    for month in (0, 13, -1):
        try:
            days_in_month(2023, month)
        except ValueError:
            continue
        return False, f"days_in_month(2023, {month}) did not raise ValueError"
    return True
