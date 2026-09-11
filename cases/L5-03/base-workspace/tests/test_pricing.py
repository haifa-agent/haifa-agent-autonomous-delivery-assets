import inspect
import unittest

import pricing
from pricing import calc, calculate


class PricingTest(unittest.TestCase):
    def test_calculate_returns_the_discounted_total(self):
        self.assertEqual(7.5, calculate(10.0, 2.5))

    def test_calc_returns_the_same_result(self):
        self.assertEqual(7.5, calc(10.0, 2.5))

    def test_calc_delegates_to_calculate(self):
        source = inspect.getsource(pricing.calc)

        self.assertIn("calculate(", source)
        self.assertNotIn("round(", source)


if __name__ == "__main__":
    unittest.main()