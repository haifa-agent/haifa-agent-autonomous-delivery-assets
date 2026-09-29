import ast
import hashlib
import json
import os
import subprocess
import sys


def _priced(discount_percent):
    from datetime import UTC, datetime

    from depot.core.catalog import Catalog, Product
    from depot.core.discounts import ThresholdDiscount
    from depot.core.ids import order_id
    from depot.core.money import Money
    from depot.core.orders import Order, OrderLine, OrderStatus
    from depot.core.pricing import price_order
    from depot.core.sku import Sku
    from depot.core.tax import TaxTable
    from depot.core.units import Weight

    catalog = Catalog(
        [Product(Sku("BEV-1001"), "Coffee", "beverages", Money.parse("10.00"), Weight(100))]
    )
    order = Order(
        identifier=order_id("O-000101"),
        customer="Acme",
        warehouse="WH-CEN",
        status=OrderStatus.CONFIRMED,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        lines=[OrderLine(Sku("BEV-1001"), 2, Money.parse("10.00"))],
    )
    rules = []
    if discount_percent:
        rules = [ThresholdDiscount("t", threshold=Money.parse("10.00"), percent=discount_percent)]
    return price_order(order, catalog, TaxTable(rates={"CN": 1000}), rules, region="CN")


@check("functional.discountIsTaxedOnTheDiscountedBase")
def discount_is_taxed_on_the_discounted_base():
    pricing = _priced(10)
    got = (
        pricing.discount.as_decimal(),
        pricing.taxable.as_decimal(),
        pricing.tax.as_decimal(),
        pricing.total.as_decimal(),
    )
    if got != ("2.00", "18.00", "1.80", "19.80"):
        return False, f"discount/taxable/tax/total = {got}, expected ('2.00', '18.00', '1.80', '19.80')"
    return True


@check("functional.shippingCostRoundsUp")
def shipping_cost_rounds_up():
    from depot.core.money import Money
    from depot.core.shipping import Carrier
    from depot.core.units import Weight

    carrier = Carrier("FAST", "Fast", Money.parse("8.00"), Money.parse("2.00"), 1, Weight(30000), ("CN",))
    if carrier.cost(Weight(1500)).as_decimal() != "12.00":
        return False, f"a 1.5 kg parcel costs {carrier.cost(Weight(1500)).as_decimal()}, expected 12.00"
    return True


@check("boundary.noDiscountKeepsTheSubtotalBase")
def no_discount_keeps_the_subtotal_base():
    pricing = _priced(0)
    got = (pricing.taxable.as_decimal(), pricing.tax.as_decimal(), pricing.total.as_decimal())
    if got != ("20.00", "2.00", "22.00"):
        return False, f"taxable/tax/total = {got}, expected ('20.00', '2.00', '22.00')"
    return True


@check("boundary.exactKilogramIsOneUnit")
def exact_kilogram_is_one_unit():
    from depot.core.money import Money
    from depot.core.shipping import Carrier
    from depot.core.units import Weight

    carrier = Carrier("FAST", "Fast", Money.parse("8.00"), Money.parse("2.00"), 1, Weight(30000), ("CN",))
    if carrier.cost(Weight(1000)).as_decimal() != "10.00":
        return False, f"a 1.0 kg parcel costs {carrier.cost(Weight(1000)).as_decimal()}, expected 10.00"
    return True


@check("regression.pickAndPackUnchanged")
def pick_and_pack_unchanged():
    completed = subprocess.run(
        [sys.executable, "-m", "depot", "--json", "pack", "--order", "O-000103"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    if completed.returncode != 0:
        return False, f"pack exited {completed.returncode}: {completed.stderr[:120]}"
    if not json.loads(completed.stdout).get("parcels"):
        return False, "packing produced no parcels"
    return True


@check("constraint.layerDirection")
def layer_direction():
    core = os.path.join(WORKSPACE, "depot", "core")
    for root, _dirs, files in os.walk(core):
        for name in files:
            if not name.endswith(".py"):
                continue
            with open(os.path.join(root, name), encoding="utf-8") as handle:
                tree = ast.parse(handle.read())
            for node in ast.walk(tree):
                module = None
                if isinstance(node, ast.ImportFrom):
                    module = node.module
                elif isinstance(node, ast.Import) and node.names:
                    module = node.names[0].name
                if module and module.startswith("depot") and not module.startswith("depot.core"):
                    return False, f"{name} imports {module}; the domain layer must not reach upward"
    return True


@check("constraint.testsUntouched")
def tests_untouched():
    expected = "@@TREE_SHA256:tests@@"
    for relative, digest in expected.items():
        path = os.path.join(WORKSPACE, relative)
        if not os.path.isfile(path):
            return False, f"{relative} is missing"
        with open(path, "rb") as handle:
            actual = hashlib.sha256(handle.read()).hexdigest()
        if actual != digest:
            return False, f"{relative} was changed instead of the source"
    return True
