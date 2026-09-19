import unittest

from kiosk.core.text import contains_all, normalize, tokens


class NormalizeTest(unittest.TestCase):
    def test_case_and_whitespace_do_not_matter(self):
        self.assertEqual("cold brew", normalize("  Cold   BREW "))

    def test_accents_are_folded_away(self):
        self.assertEqual("cafe creme", normalize("Caf\u00e9 Cr\u00e8me"))

    def test_a_number_is_accepted(self):
        self.assertEqual("12", normalize(12))


class TokensTest(unittest.TestCase):
    def test_punctuation_separates_words(self):
        self.assertEqual(["barista", "special", "extra", "hot"], tokens("Barista Special, Extra Hot"))

    def test_an_empty_text_has_no_tokens(self):
        self.assertEqual([], tokens("   "))


class ContainsAllTest(unittest.TestCase):
    def test_every_needle_must_occur(self):
        self.assertTrue(contains_all("cold brew coffee", ["cold", "coffee"]))
        self.assertFalse(contains_all("cold brew coffee", ["cold", "tea"]))

    def test_no_needle_matches_everything(self):
        self.assertTrue(contains_all("anything", []))


if __name__ == "__main__":
    unittest.main()
