import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

import cli


def run(*arguments):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.main(list(arguments))
    return code, out.getvalue(), err.getvalue()


class CliTest(unittest.TestCase):
    def test_add_then_list(self):
        with TemporaryDirectory() as directory:
            store = str(Path(directory) / "store.json")

            self.assertEqual((0, "added b-2\n", ""), run("add", "--store", store, "b-2", "item b", "1"))
            self.assertEqual((0, "added a-1\n", ""), run("add", "--store", store, "a-1", "item a", "5"))
            self.assertEqual((0, "a-1 5 item a\nb-2 1 item b\n", ""), run("list", "--store", store))

    def test_add_rejects_invalid_quantity(self):
        with TemporaryDirectory() as directory:
            code, out, err = run("add", "--store", str(Path(directory) / "s.json"), "a-1", "item a", "-3")

        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertIn("quantity", err)


if __name__ == "__main__":
    unittest.main()
