import unittest
from datetime import datetime

from opsdesk.util.timewindow import day_window, in_window, parse_timestamp


class TimeWindowTest(unittest.TestCase):
    def test_timestamps_are_parsed(self):
        self.assertEqual(datetime(2026, 2, 10, 9, 15), parse_timestamp("2026-02-10 09:15:00"))

    def test_day_window_starts_at_midnight(self):
        start, end = day_window("2026-02-10")

        self.assertEqual(datetime(2026, 2, 10), start)
        self.assertEqual(datetime(2026, 2, 11), end)

    def test_moments_during_the_day_are_inside(self):
        start, end = day_window("2026-02-10")

        self.assertTrue(in_window(start, start, end))
        self.assertTrue(in_window(datetime(2026, 2, 10, 12), start, end))

    def test_the_previous_day_is_outside(self):
        start, end = day_window("2026-02-10")

        self.assertFalse(in_window(datetime(2026, 2, 9, 23, 59, 59), start, end))


if __name__ == "__main__":
    unittest.main()
