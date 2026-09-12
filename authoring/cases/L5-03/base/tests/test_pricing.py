import unittest
import warnings

import pricing
from checkout import checkout_total
from invoice import invoice_amount


class PricingTest(unittest.TestCase):
    def test_calculate_returns_the_discounted_total(self):
        self.assertEqual(7.5, pricing.calculate(10.0, 2.5))
        self.assertEqual(0.0, pricing.calculate(total=5.0, discount=7.0))

    def test_calc_keeps_working(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            self.assertEqual(7.5, pricing.calc(10.0, 2.5))

    def test_negative_discount_is_rejected(self):
        with self.assertRaises(ValueError):
            pricing.calculate(10.0, -1.0)

    def test_existing_callers(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            self.assertEqual(90.0, checkout_total(100.0, 10.0))
            self.assertEqual(19.99, invoice_amount(24.99, 5.0))


if __name__ == "__main__":
    unittest.main()
