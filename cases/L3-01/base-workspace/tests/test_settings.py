import unittest

from settings import load_settings


class SettingsTest(unittest.TestCase):
    def test_posix_project_path_is_resolved(self):
        self.assertEqual({"data": "/srv/demo/data"}, load_settings("data=$PROJECT/data\n", "/srv/demo"))

    def test_windows_project_path_is_resolved(self):
        self.assertEqual({"data": "D:\\repos\\demo/cache"}, load_settings("data=$PROJECT/cache\n", "D:\\repos\\demo"))

    def test_plain_values_are_kept(self):
        self.assertEqual({"mode": "fast"}, load_settings("mode = fast\n", "D:\\repos\\demo"))

    def test_comments_and_blank_lines_are_skipped(self):
        self.assertEqual({"a": "1"}, load_settings("# note\n\na=1\n", "/srv/demo"))


if __name__ == "__main__":
    unittest.main()