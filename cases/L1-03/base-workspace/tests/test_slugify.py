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


if __name__ == "__main__":
    unittest.main()