import unittest

from slugify import slugify


class SlugifyTest(unittest.TestCase):
    def test_words_are_joined_with_hyphens(self):
        self.assertEqual("hello-world", slugify("Hello World"))

    def test_edge_separators_are_removed(self):
        self.assertEqual("edge-cases", slugify("--Edge--Cases--"))

    def test_runs_of_separators_collapse(self):
        self.assertEqual("multi-underscore-run", slugify("multi___underscore   run"))

    def test_symbols_are_dropped(self):
        self.assertEqual("release-notes-v20", slugify("Release  Notes (v2.0)!!"))

    def test_symbols_between_words_leave_a_single_hyphen(self):
        self.assertEqual("rock-roll", slugify("rock & roll"))

    def test_only_symbols_give_an_empty_slug(self):
        self.assertEqual("", slugify("!!!"))


if __name__ == "__main__":
    unittest.main()
