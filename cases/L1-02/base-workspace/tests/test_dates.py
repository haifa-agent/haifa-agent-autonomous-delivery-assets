import unittest

from dates import days_in_month, is_leap_year


class DatesTest(unittest.TestCase):
    def test_leap_years(self):
        self.assertTrue(is_leap_year(2000))
        self.assertTrue(is_leap_year(2024))

    def test_century_years_are_not_leap(self):
        self.assertFalse(is_leap_year(1900))

    def test_february_length(self):
        self.assertEqual(29, days_in_month(2000, 2))
        self.assertEqual(28, days_in_month(1900, 2))

    def test_other_months(self):
        self.assertEqual(30, days_in_month(2023, 4))
        self.assertEqual(31, days_in_month(2023, 1))


if __name__ == "__main__":
    unittest.main()