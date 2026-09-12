import random


@check("functional.ratioRounded")
def ratio_rounded():
    from metrics import conversion_rate

    return conversion_rate(2, 3) == 0.67 and conversion_rate(1, 3) == 0.33 and conversion_rate(5, 7) == 0.71


@check("boundary.randomizedRatios")
def randomized_ratios():
    from metrics import conversion_rate

    rng = random.Random(20260911)
    for _ in range(1000):
        visits = rng.randint(1, 5000)
        clicks = rng.randint(0, visits)
        got = conversion_rate(clicks, visits)
        # Any correct two-decimal rounding is accepted (ties may round either way).
        two_decimals = isinstance(got, float) and abs(got * 100 - round(got * 100)) < 1e-6
        if not two_decimals or abs(got - clicks / visits) > 0.005 + 1e-9:
            return False, f"conversion_rate({clicks}, {visits}) returned {got!r}"
    return True


@check("boundary.wholeAndZeroRates")
def whole_and_zero():
    from metrics import conversion_rate

    return conversion_rate(5, 5) == 1.0 and conversion_rate(0, 7) == 0.0


@check("regression.rendererKeepsWorking")
def renderer():
    from report import format_rate

    return format_rate(2, 3) == "67%" and format_rate(1, 2) == "50%" and format_rate(0, 4) == "0%"


@check("regression.invalidVisitsRejected")
def invalid_visits():
    from metrics import conversion_rate

    for visits in (0, -3):
        try:
            conversion_rate(1, visits)
        except ValueError:
            continue
        return False, f"conversion_rate(1, {visits}) did not raise ValueError"
    return True
