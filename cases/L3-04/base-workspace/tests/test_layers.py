import ast
import unittest
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "opsdesk"
ALLOWED = {
    "util": set(),
    "core": {"util"},
    "config": {"util"},
    "adapter": {"core", "util"},
    "store": {"core", "util"},
    "reporting": {"core", "util"},
    "api": {"adapter", "config", "core", "reporting", "store", "util"},
}


def imported_modules(path, tree):
    package = ["opsdesk", *path.relative_to(PACKAGE_ROOT).parts[:-1]]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package[: len(package) - node.level + 1]
            else:
                base = []
            module = ".".join(base + ([node.module] if node.module else []))
            yield module
            for alias in node.names:
                yield f"{module}.{alias.name}"


def layer_violations():
    violations = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        relative = path.relative_to(PACKAGE_ROOT)
        if len(relative.parts) < 2:
            continue
        layer = relative.parts[0]
        if layer not in ALLOWED:
            violations.append(f"{relative.as_posix()}: opsdesk.{layer} is not a known layer")
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for module in imported_modules(path, tree):
            parts = module.split(".")
            if parts[0] != "opsdesk" or len(parts) < 2:
                continue
            target = parts[1]
            if target in ALLOWED and target != layer and target not in ALLOWED[layer]:
                violations.append(f"{relative.as_posix()}: opsdesk.{layer} must not import {module}")
            if target in ("__main__",):
                violations.append(f"{relative.as_posix()}: must not import the command line module")
    return sorted(set(violations))


class LayerTest(unittest.TestCase):
    def test_dependency_direction_is_respected(self):
        self.assertEqual([], layer_violations())


if __name__ == "__main__":
    unittest.main()
