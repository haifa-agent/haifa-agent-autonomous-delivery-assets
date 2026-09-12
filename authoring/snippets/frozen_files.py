import hashlib as _hashlib
import sys as _sys
import ast as _frozen_ast
from pathlib import Path as _FrozenPath

_IGNORED_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache"}


def _frozen_changes(expected, directory=None):
    """Return the files that differ from ``expected`` ({path: sha256}); ``directory`` also flags added files."""
    workspace = _FrozenPath(WORKSPACE)
    problems = []
    for relative, digest in expected.items():
        path = workspace / relative
        if not path.is_file():
            problems.append(f"{relative} deleted")
        elif _hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            problems.append(f"{relative} modified")
    if directory is not None:
        for path in sorted((workspace / directory).rglob("*")):
            relative = path.relative_to(workspace).as_posix()
            if path.is_file() and not _IGNORED_PARTS & set(path.parts) and path.suffix != ".pyc" and relative not in expected:
                problems.append(f"{relative} added")
    return problems


def _third_party_imports(exclude_prefixes=("tests/",)):
    """Return 'file: module' for every import that is neither stdlib nor a workspace module."""
    workspace = _FrozenPath(WORKSPACE)
    local = {path.stem for path in workspace.glob("*.py")} | {path.name for path in workspace.iterdir() if path.is_dir()}
    found = []
    for path in sorted(workspace.rglob("*.py")):
        relative = path.relative_to(workspace).as_posix()
        if relative.startswith(exclude_prefixes) or _IGNORED_PARTS & set(path.parts):
            continue
        for node in _frozen_ast.walk(_frozen_ast.parse(path.read_text(encoding="utf-8"))):
            modules = []
            if isinstance(node, _frozen_ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, _frozen_ast.ImportFrom) and node.module and not node.level:
                modules = [node.module]
            for module in modules:
                top = module.split(".")[0]
                if top not in _sys.stdlib_module_names and top not in local and top != "__future__":
                    found.append(f"{relative}: {module}")
    return found
