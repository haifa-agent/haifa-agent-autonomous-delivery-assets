import ast as _ast
from pathlib import Path as _Path

_LAYERS = {
    "util": set(),
    "core": {"util"},
    "config": {"util"},
    "adapter": {"core", "util"},
    "store": {"core", "util"},
    "reporting": {"core", "util"},
    "api": {"adapter", "config", "core", "reporting", "store", "util"},
}


def _layer_violations():
    package_root = _Path(WORKSPACE, "opsdesk")
    violations = []
    for path in sorted(package_root.rglob("*.py")):
        relative = path.relative_to(package_root)
        if len(relative.parts) < 2:
            continue
        layer = relative.parts[0]
        if layer not in _LAYERS:
            violations.append(f"{relative.as_posix()}: unknown layer opsdesk.{layer}")
            continue
        package = ["opsdesk", *relative.parts[:-1]]
        for node in _ast.walk(_ast.parse(path.read_text(encoding="utf-8"))):
            modules = []
            if isinstance(node, _ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, _ast.ImportFrom):
                base = package[: len(package) - node.level + 1] if node.level else []
                module = ".".join(base + ([node.module] if node.module else []))
                modules = [module] + [f"{module}.{alias.name}" for alias in node.names]
            for module in modules:
                parts = module.split(".")
                if parts[0] != "opsdesk" or len(parts) < 2:
                    continue
                target = parts[1]
                if target == "__main__" or (target in _LAYERS and target != layer and target not in _LAYERS[layer]):
                    violations.append(f"{relative.as_posix()} imports {module}")
    return sorted(set(violations))


@check("constraint.layerDirection")
def layer_direction():
    violations = _layer_violations()
    return not violations, "; ".join(violations[:3])
