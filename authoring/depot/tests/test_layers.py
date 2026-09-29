import ast
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "depot"
ALLOWED = {
    "depot.core": {"depot.core"},
    "depot.store": {"depot.core", "depot.store"},
    "depot.adapter": {"depot.core", "depot.store", "depot.adapter"},
    "depot.api": {"depot.core", "depot.store", "depot.adapter", "depot.api"},
}


def _imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            yield node.module


def _layer_of(path):
    relative = path.relative_to(PACKAGE.parent).as_posix()
    parts = relative.split("/")
    return ".".join(parts[:2]) if len(parts) > 2 else None


class LayerTest(unittest.TestCase):
    def test_every_module_imports_only_downward(self):
        for path in sorted(PACKAGE.rglob("*.py")):
            layer = _layer_of(path)
            if layer not in ALLOWED:
                continue
            allowed = ALLOWED[layer]
            for module in _imports(path):
                if not module.startswith("depot"):
                    continue
                owner = ".".join(module.split(".")[:2])
                self.assertIn(owner, allowed, f"{path.name} ({layer}) must not import {module}")

    def test_core_is_pure(self):
        for path in sorted((PACKAGE / "core").rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("open(", source, f"{path.name} must not read or write files")
            self.assertNotIn("pathlib", source, f"{path.name} must not use pathlib")
            self.assertNotIn("os.path", source, f"{path.name} must not use os.path")


if __name__ == "__main__":
    unittest.main()
