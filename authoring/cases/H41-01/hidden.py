import subprocess
import sys

CUSTOM_TIERS = ((0, 0), (1_000, 50))


def _repository():
    from kiosk.app.repository import CatalogRepository

    return CatalogRepository()


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


@check("functional.theDiscountEntryPointIsBack")
def the_discount_entry_point_is_back():
    try:
        from kiosk.core.pricing import apply_discounts
    except ImportError as error:
        return False, f"kiosk.core.pricing.apply_discounts is still missing: {error}"
    if apply_discounts(0) != 0:
        return False, "an empty order earns a discount"
    if apply_discounts(100_000) <= 0:
        return False, "a large order earns no discount"
    return True


@check("functional.aTierStartsAtItsMinimum")
def a_tier_starts_at_its_minimum():
    from kiosk.core.discount_tiers import TIERS, tier_for

    for minimum, percent in TIERS:
        got = tier_for(minimum)
        if got != percent:
            return False, f"an order of exactly {minimum} earns {got}% instead of {percent}%"
    return True


@check("boundary.everyTierMinimumAndTheCentBelowIt")
def every_tier_minimum_and_the_cent_below_it():
    from kiosk.core.discount_tiers import TIERS, tier_for

    previous = 0
    for minimum, percent in TIERS:
        if minimum > 0:
            below = tier_for(minimum - 1)
            if below != previous:
                return False, f"one cent below {minimum} earns {below}% instead of {previous}%"
        if tier_for(minimum + 1) != percent:
            return False, f"one cent above {minimum} earns {tier_for(minimum + 1)}% instead of {percent}%"
        previous = percent
    if tier_for(TIERS[-1][0] * 100) != TIERS[-1][1]:
        return False, "the top tier does not hold for a very large order"
    return True


@check("boundary.theDiscountIsRoundedDown")
def the_discount_is_rounded_down():
    from kiosk.core.discount_tiers import discount_of

    if discount_of(101, 5) != 5:
        return False, f"5% of 101 cents came out as {discount_of(101, 5)}"
    if discount_of(19, 5) != 0:
        return False, f"5% of 19 cents came out as {discount_of(19, 5)}"
    try:
        discount_of(100, -1)
    except ValueError:
        return True
    return False, "a negative percent was accepted"


@check("regression.theCartBreakdownAddsUp")
def the_cart_breakdown_adds_up():
    from kiosk.core.pricing import Line, cart_total

    for quantity in range(0, 25):
        total = cart_total([Line("K-001", 2_500, quantity)])
        if total.subtotal_cents != 2_500 * quantity:
            return False, f"{quantity} units subtotalled {total.subtotal_cents}"
        if total.total_cents != total.subtotal_cents - total.discount_cents:
            return False, f"{quantity} units: the breakdown does not add up"
        if total.discount_cents < 0:
            return False, f"{quantity} units produced a negative discount"
    exact = cart_total([Line("K-001", 2_500, 2)])
    if (exact.subtotal_cents, exact.discount_cents, exact.total_cents) != (5_000, 250, 4_750):
        return False, f"a cart of exactly 5000 cents came out as {exact}"
    return True


@check("regression.theRestOfTheProductStillWorks")
def the_rest_of_the_product_still_works():
    from kiosk.app.cache import FileCache
    from kiosk.app.exporters import export
    from kiosk.app.listing import ordered_items
    from kiosk.app.session import Session

    items = ordered_items(_repository(), FileCache(None))
    if len(items) != len(_repository().items()):
        return False, "the listing no longer covers the catalogue"
    if not export("json", items).strip().startswith("{"):
        return False, "the json export is no longer json"
    session = Session(_repository())
    session.add("K-001", 2)
    if session.checkout().total.subtotal_cents != 6_400:
        return False, "a session no longer prices its selection"
    code, out, err = _cli("cart", "K-001=2")
    if code != 0 or "total" not in out:
        return False, f"the command line cart exited {code}: {err.strip()[:120]}"
    return True


@check("constraint.aCustomTierTableIsHonoured")
def a_custom_tier_table_is_honoured():
    from kiosk.core.discount_tiers import tier_for
    from kiosk.core.pricing import Line, cart_total

    if tier_for(10_000, CUSTOM_TIERS) != 50:
        return False, f"a custom tier table gave {tier_for(10_000, CUSTOM_TIERS)}% instead of 50%"
    total = cart_total([Line("K-001", 10_000, 1)], CUSTOM_TIERS)
    if total.discount_cents != 5_000:
        return False, f"a cart priced against a custom tier table discounted {total.discount_cents} instead of 5000"
    return True
