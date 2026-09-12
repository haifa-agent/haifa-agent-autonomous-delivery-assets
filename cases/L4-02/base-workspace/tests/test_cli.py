import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def opsdesk(*arguments):
    return subprocess.run(
        [sys.executable, "-m", "opsdesk", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )


class CommandLineTest(unittest.TestCase):
    def test_settings_command(self):
        completed = opsdesk("settings", "/srv/demo")

        self.assertEqual(0, completed.returncode, completed.stderr)
        settings = json.loads(completed.stdout)
        self.assertEqual("/srv/demo/cache", settings["cache_dir"])
        self.assertEqual("info", settings["log_level"])

    def test_nightly_command(self):
        completed = opsdesk("nightly", "2026-02-10")

        self.assertEqual(0, completed.returncode, completed.stderr)
        lines = completed.stdout.splitlines()
        self.assertEqual("nightly report 2026-02-10", lines[0])
        self.assertEqual(["section: a", "section: b", "section: c"], [line for line in lines if line.startswith("section:")])

    def test_import_command(self):
        completed = opsdesk("import", str(ROOT / "data" / "rows.json"))

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("imported=3 skipped=1", completed.stdout.strip())


if __name__ == "__main__":
    unittest.main()
