import unittest

from metrics import conversion_rate
from report import format_rate


class MetricsTest(unittest.TestCase):
    def test_two_of_three(self):
        self.assertAlmostEqual(0.67, conversion_rate(2, 3), places=2)

    def test_half(self):
        self.assertAlmostEqual(0.5, conversion_rate(1, 2), places=2)

    def test_renderer_uses_the_ratio(self):
        self.assertEqual("50%", format_rate(1, 2))

    def test_invalid_visits(self):
        with self.assertRaises(ValueError):
            conversion_rate(1, 0)


if __name__ == "__main__":
    unittest.main()