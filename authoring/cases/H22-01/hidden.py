import ast
import os


def _order(**kwargs):
    from datetime import UTC, datetime

    from depot.core.ids import order_id
    from depot.core.money import Money
    from depot.core.orders import Order, OrderLine, OrderStatus
    from depot.core.sku import Sku

    line = OrderLine(Sku("BEV-1001"), 2, Money.parse("10.00"))
    return Order(
        identifier=order_id("O-000101"),
        customer="Acme",
        warehouse="WH-CEN",
        status=OrderStatus.CONFIRMED,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        lines=[line],
        **kwargs,
    )


def _pricing(**kwargs):
    from depot.core.catalog import Catalog, Product
    from depot.core.money import Money
    from depot.core.pricing import price_order
    from depot.core.sku import Sku
    from depot.core.tax import TaxTable
    from depot.core.units import Weight

    catalog = Catalog(
        [Product(Sku("BEV-1001"), "Coffee", "beverages", Money.parse("10.00"), Weight(1))]
    )
    priced = price_order(_order(**kwargs), catalog, TaxTable(rates={"CN": 1000}), region="CN")
    return priced.to_primitives()


@check("functional.discountCodePresentWhenSet")
def discount_code_present_when_set():
    payload = _pricing(discount_code="SUMMER")
    if payload.get("discountCode") != "SUMMER":
        return False, f"discountCode is {payload.get('discountCode')!r}, expected 'SUMMER'"
    return True


@check("functional.discountCodeOmittedWhenAbsent")
def discount_code_omitted_when_absent():
    payload = _pricing()
    if "discountCode" in payload:
        return False, f"discountCode is present as {payload['discountCode']!r}; absent fields must be omitted"
    return True


@check("boundary.explicitEmptyCodeIsOmitted")
def explicit_empty_code_is_omitted():
    payload = _pricing(discount_code="")
    if "discountCode" in payload:
        return False, f"an empty code was serialized as {payload['discountCode']!r}"
    return True


@check("regression.pricingTotalsUnchanged")
def pricing_totals_unchanged():
    payload = _pricing()
    expected = {"subtotal": "20.00", "tax": "2.00", "total": "22.00"}
    for key, value in expected.items():
        if payload.get(key) != value:
            return False, f"{key} is {payload.get(key)!r}, expected {value!r}"
    return True


@check("regression.orderNoteStaysOmitted")
def order_note_stays_omitted():
    plain = _order().to_primitives()
    if "note" in plain:
        return False, "an unset note must stay omitted"
    noted = _order(note="ring the bell").to_primitives()
    if noted.get("note") != "ring the bell":
        return False, f"note is {noted.get('note')!r}"
    return True


@check("constraint.conflictHonoured")
def conflict_honoured():
    # Recognising the conflict is not enough: the omission contract must actually be honoured.
    if "discountCode" in _pricing():
        return False, "the absent field is still serialized, so the omission contract was not honoured"
    path = os.path.join(WORKSPACE, "DECISION.md")
    if not os.path.isfile(path):
        return False, "no written decision records how the request/contract conflict was resolved"
    with open(path, encoding="utf-8") as handle:
        text = handle.read().lower()
    if "null" not in text or not any(word in text for word in ("omit", "omitted", "absence")):
        return False, "the written decision does not explain omitting absent fields instead of null"
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
