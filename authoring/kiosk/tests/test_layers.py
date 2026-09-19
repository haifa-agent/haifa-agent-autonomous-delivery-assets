import ast
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "kiosk"
ALLOWED = {
    "kiosk.core": set(),
    "kiosk.app": {"kiosk.core", "kiosk.app"},
}


def _imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            yield node.module


def _package_of(path):
    relative = path.relative_to(PACKAGE.parent).as_posix()
    parts = relative.split("/")
    return ".".join(parts[:2]) if len(parts) > 2 else None


class LayerTest(unittest.TestCase):
    def test_every_module_stays_inside_its_layer(self):
        for path in sorted(PACKAGE.rglob("*.py")):
            package = _package_of(path)
            if package not in ALLOWED:
                continue
            allowed = ALLOWED[package] | {package}
            for module in _imports(path):
                if not module.startswith("kiosk"):
                    continue
                owner = ".".join(module.split(".")[:2])
                self.assertIn(
                    owner,
                    allowed,
                    f"{path.name} ({package}) must not import {module}",
                )

    def test_core_touches_no_file(self):
        for path in sorted((PACKAGE / "core").rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("open(", source, f"{path.name} must not read or write files")
            self.assertNotIn("pathlib", source, f"{path.name} must not use pathlib")


if __name__ == "__main__":
    unittest.main()
