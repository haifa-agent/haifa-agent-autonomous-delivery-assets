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

    def test_verbose_flag_is_parsed(self):
        self.assertTrue(Config.from_arguments(["--verbose"]).verbose)

    def test_verbose_emits_step_lines(self):
        _, output = run_main(["--verbose", "--output", "r.json"])

        for step in ("loading", "aggregating", "writing"):
            self.assertIn(f"verbose: {step}", output)


if __name__ == "__main__":
    unittest.main()