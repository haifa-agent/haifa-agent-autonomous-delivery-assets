import unittest
from pathlib import Path

from opsdesk.config.settings import load_settings, load_settings_file

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "settings.ini"


class SettingsTest(unittest.TestCase):
    def test_placeholders_resolve_against_the_project(self):
        settings = load_settings("cache_dir = $PROJECT/cache\nreport_dir = ${PROJECT}/reports\n", "/srv/demo")

        self.assertEqual("/srv/demo/cache", settings["cache_dir"])
        self.assertEqual("/srv/demo/reports", settings["report_dir"])

    def test_defaults_apply_when_a_key_is_absent(self):
        settings = load_settings("", "/srv/demo")

        self.assertEqual("safe", settings["mode"])
        self.assertEqual(".cache", settings["cache_dir"])

    def test_comments_and_malformed_lines_are_skipped(self):
        settings = load_settings("# comment\n; comment\nnot a setting\nmode = fast\n", "/srv/demo")

        self.assertEqual("fast", settings["mode"])
        self.assertNotIn("not a setting", settings)

    def test_sample_file_loads(self):
        settings = load_settings_file(SAMPLE, "/opt/opsdesk")

        self.assertEqual("fast", settings["mode"])
        self.assertEqual("/opt/opsdesk/cache", settings["cache_dir"])
        self.assertEqual("/var/opsdesk/archive", settings["archive_dir"])


if __name__ == "__main__":
    unittest.main()
