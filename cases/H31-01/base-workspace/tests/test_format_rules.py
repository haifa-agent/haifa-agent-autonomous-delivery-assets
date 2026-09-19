import unittest

from kiosk.core.format_rules import MISSING, NAME_LIMIT, clip, iso_utc, present


class PresentTest(unittest.TestCase):
    def test_a_value_is_rendered_as_text(self):
        self.assertEqual("abc", present("abc"))
        self.assertEqual("7", present(7))

    def test_a_missing_or_blank_value_becomes_the_placeholder(self):
        self.assertEqual(MISSING, present(None))
        self.assertEqual(MISSING, present(""))
        self.assertEqual(MISSING, present("   "))


class ClipTest(unittest.TestCase):
    def test_a_short_text_is_untouched(self):
        self.assertEqual("short", clip("short"))

    def test_a_long_text_is_cut_and_marked(self):
        clipped = clip("x" * 60)

        self.assertEqual(NAME_LIMIT, len(clipped))
        self.assertTrue(clipped.endswith("..."))


class IsoUtcTest(unittest.TestCase):
    def test_epoch_millis_render_as_utc(self):
        self.assertEqual("1970-01-01T00:00:00Z", iso_utc(0))
        self.assertEqual("2026-09-15T00:00:00Z", iso_utc(1789430400000))


if __name__ == "__main__":
    unittest.main()
