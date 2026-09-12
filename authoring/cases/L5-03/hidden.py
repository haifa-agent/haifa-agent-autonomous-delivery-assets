import ast
import os
import random
import warnings

FROZEN_CALLERS = {**"@@TREE_SHA256:checkout.py@@", **"@@TREE_SHA256:invoice.py@@"}


def _expected(total, discount):
    if discount < 0:
        raise ValueError
    return round(max(total - discount, 0.0), 2)


def _quiet(function, *arguments, **keywords):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return function(*arguments, **keywords)


@check("functional.calculateBehaviour")
def calculate_behaviour():
    import pricing

    rng = random.Random(20260911)
    for _ in range(300):
        total, discount = round(rng.uniform(0, 500), 2), round(rng.uniform(0, 600), 2)
        if pricing.calculate(total, discount) != _expected(total, discount):
            return False, f"calculate({total}, {discount}) returned {pricing.calculate(total, discount)}"
    try:
        pricing.calculate(total=1.0, discount=-0.5)
        return False, "negative discount accepted"
    except ValueError:
        pass
    return pricing.calculate(total=5.0, discount=7.0) == 0.0


@check("regression.calcPositionalAndKeyword")
def calc_compatible():
    import pricing

    return (
        _quiet(pricing.calc, 10.0, 2.5) == 7.5
        and _quiet(pricing.calc, x=10.0, y=2.5) == 7.5
        and _quiet(pricing.calc, 3.0, y=4.0) == 0.0
    )


@check("boundary.calcStillValidates")
def calc_validates():
    import pricing

    try:
        _quiet(pricing.calc, x=1.0, y=-2.0)
    except ValueError:
        return True
    return False, "calc accepted a negative discount"


@check("functional.deprecationWarning")
def deprecation_warning():
    import pricing

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        pricing.calc(2.0, 1.0)
    alias = [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]
    with warnings.catch_warnings(record=True) as caught_new:
        warnings.simplefilter("always")
        pricing.calculate(2.0, 1.0)
    return (
        len(alias) == 1 and "calculate" in str(alias[0].message) and not caught_new,
        f"calc warnings={[str(w.message) for w in caught]}, calculate warnings={[str(w.message) for w in caught_new]}",
    )


@check("regression.callersKeepWorking")
def callers_work():
    from checkout import checkout_total
    from invoice import invoice_amount

    return _quiet(checkout_total, 100.0, 10.0) == 90.0 and _quiet(invoice_amount, 24.99, 5.0) == 19.99


@check("constraint.singleImplementation")
def single_implementation():
    tree = ast.parse(open(os.path.join(WORKSPACE, "pricing.py"), encoding="utf-8").read())
    functions = {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    if "calculate" not in functions:
        return False, "calculate is not a module-level function"

    def computes(node):
        for child in ast.walk(node):
            if isinstance(child, ast.BinOp) and isinstance(child.op, ast.Sub):
                return True
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id in ("round", "max"):
                return True
        return False

    duplicates = [name for name, node in functions.items() if name != "calculate" and computes(node)]
    return computes(functions["calculate"]) and not duplicates, f"pricing rule duplicated in {duplicates}"


@check("constraint.callersUntouched")
def callers_untouched():
    problems = _frozen_changes(FROZEN_CALLERS)
    return not problems, "; ".join(problems)
