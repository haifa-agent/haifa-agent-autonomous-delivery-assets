import io
import json
import unittest
from contextlib import redirect_stdout

import cli
from exporters import exporter_for


class ExportTest(unittest.TestCase):
    def test_json_export_is_unchanged(self):
        self.assertEqual(json.dumps(cli.SAMPLE_ROWS, sort_keys=True), cli.render("json"))

    def test_csv_export_has_header_and_rows(self):
        self.assertEqual(["sku,quantity", "a-1,2", "b-2,1"], cli.render("csv").splitlines())

    def test_unknown_format_is_rejected(self):
        with self.assertRaises(ValueError):
            exporter_for("xml")

    def test_cli_prints_the_selected_format(self):
        captured = io.StringIO()
        with redirect_stdout(captured):
            exit_code = cli.main(["--format", "csv"])

        self.assertEqual(0, exit_code)
        self.assertEqual(["sku,quantity", "a-1,2", "b-2,1"], captured.getvalue().splitlines())


if __name__ == "__main__":
    unittest.main()
