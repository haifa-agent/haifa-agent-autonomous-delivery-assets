import io
import json
import unittest
from contextlib import redirect_stdout

import cli
from config import Config


def run_main(arguments):
    captured = io.StringIO()
    with redirect_stdout(captured):
        exit_code = cli.main(arguments)
    return exit_code, captured.getvalue()


class CliTest(unittest.TestCase):
    def test_output_path_is_parsed(self):
        self.assertEqual("r.json", Config.from_arguments(["--output", "r.json"]).output_path)

    def test_report_is_printed_without_the_flag(self):
        exit_code, output = run_main(["--output", "r.json"])

        self.assertEqual(0, exit_code)
        self.assertEqual({"outputPath": "r.json", "sections": ["expenses", "categories"]}, json.loads(output))

    def test_verbose_emits_step_lines_before_the_report(self):
        exit_code, output = run_main(["--verbose", "--output", "r.json"])
        lines = output.splitlines()

        self.assertEqual(0, exit_code)
        self.assertEqual(["verbose: loading", "verbose: aggregating", "verbose: writing"], lines[:3])
        self.assertEqual("r.json", json.loads(lines[3])["outputPath"])


if __name__ == "__main__":
    unittest.main()
