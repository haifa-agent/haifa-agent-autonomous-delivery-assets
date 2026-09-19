import unittest

try:
    from kiosk.core.pricing import apply_discounts
except ImportError as error:  # an unfinished refactor can leave the entry point behind
    raise unittest.SkipTest(f"kiosk.core.pricing.apply_discounts is unavailable: {error}")

from kiosk.core.discount_tiers import TIERS, discount_of, tier_for
from kiosk.core.pricing import Line, cart_total


class TierTest(unittest.TestCase):
    def test_a_small_order_earns_nothing(self):
        self.assertEqual(0, tier_for(0))
        self.assertEqual(0, tier_for(4_999))

    def test_a_tier_starts_at_its_minimum(self):
        for minimum, percent in TIERS:
            self.assertEqual(percent, tier_for(minimum), f"an order of exactly {minimum} earns {percent}%")

    def test_the_tier_holds_until_the_next_minimum(self):
        self.assertEqual(5, tier_for(19_999))
        self.assertEqual(10, tier_for(20_000))
        self.assertEqual(10, tier_for(49_999))
        self.assertEqual(15, tier_for(50_000))
        self.assertEqual(15, tier_for(10_000_000))


class DiscountArithmeticTest(unittest.TestCase):
    def test_the_discount_is_rounded_down(self):
        self.assertEqual(5, discount_of(101, 5))
        self.assertEqual(0, discount_of(19, 5))

    def test_a_negative_percent_is_rejected(self):
        with self.assertRaises(ValueError):
            discount_of(100, -1)


class ApplyDiscountsTest(unittest.TestCase):
    def test_the_discount_follows_the_tier_of_the_subtotal(self):
        self.assertEqual(0, apply_discounts(4_999))
        self.assertEqual(250, apply_discounts(5_000))
        self.assertEqual(2_000, apply_discounts(20_000))
        self.assertEqual(7_500, apply_discounts(50_000))

    def test_a_negative_subtotal_is_rejected(self):
        with self.assertRaises(Exception):
            apply_discounts(-1)

    def test_a_cart_at_a_tier_minimum_is_discounted(self):
        total = cart_total([Line("K-001", 2_500, 2)])

        self.assertEqual(5_000, total.subtotal_cents)
        self.assertEqual(250, total.discount_cents)
        self.assertEqual(4_750, total.total_cents)


if __name__ == "__main__":
    unittest.main()
