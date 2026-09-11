import unittest

from pagination import PageWindow, page_count


class PaginationTest(unittest.TestCase):
    def test_full_pages_are_sliced_without_overlap(self):
        items = [str(index) for index in range(6)]

        self.assertEqual(["0", "1", "2"], PageWindow.slice(items, 1, 3))
        self.assertEqual(["3", "4", "5"], PageWindow.slice(items, 2, 3))

    def test_last_page_is_partially_filled(self):
        items = [str(index) for index in range(7)]

        self.assertEqual(["6"], PageWindow.slice(items, 3, 3))

    def test_page_beyond_the_end_is_empty(self):
        items = [str(index) for index in range(3)]

        self.assertEqual([], PageWindow.slice(items, 4, 3))

    def test_page_count(self):
        self.assertEqual(0, page_count(0, 3))
        self.assertEqual(1, page_count(1, 3))
        self.assertEqual(3, page_count(7, 3))


if __name__ == "__main__":
    unittest.main()