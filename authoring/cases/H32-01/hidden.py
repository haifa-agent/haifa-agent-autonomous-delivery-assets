import ast
import json
import os
import subprocess
import sys


def _service():
    from depot.adapter.config_loader import DepotConfig
    from depot.api.service import DepotService

    return DepotService.open(os.path.join(WORKSPACE, "data"), DepotConfig(region="CN"))


@check("functional.filterApplied")
def filter_applied():
    from depot.core.replenishment import suggestions

    service = _service()
    result = suggestions(service.inventory, service.suppliers, service.catalog, supplier="SUP-001")
    if not result:
        return False, "filtering to SUP-001 returned nothing"
    leaked = [entry.sku for entry in result if entry.supplier_id != "SUP-001"]
    if leaked:
        return False, f"the filter leaked other suppliers: {leaked}"
    return True


@check("functional.defaultApplied")
def default_applied():
    from depot.core.replenishment import suggestions

    service = _service()
    result = suggestions(service.inventory, service.suppliers, service.catalog)
    suppliers = {entry.supplier_id for entry in result}
    if "SUP-001" not in suppliers or len(suppliers) < 2:
        return False, f"the unfiltered suggestions only cover {sorted(suppliers)}"
    return True


@check("boundary.unknownSupplier")
def unknown_supplier():
    from depot.core.replenishment import suggestions

    service = _service()
    result = suggestions(service.inventory, service.suppliers, service.catalog, supplier="SUP-999")
    if result:
        return False, f"an unknown supplier returned {len(result)} suggestions"
    return True


@check("regression.registryCaller")
def registry_caller():
    from depot.api.commands import build_registry

    registry = build_registry(_service())
    payload = registry.dispatch("reorders", supplier="SUP-001")
    rows = payload.get("suggestions", [])
    if not rows:
        return False, "the handler registry returned nothing for a supplier filter"
    if any(row.get("supplierId") != "SUP-001" for row in rows):
        return False, "the handler registry did not pass the supplier filter through"
    return True


@check("regression.adapterCaller")
def adapter_caller():
    completed = subprocess.run(
        [sys.executable, "-m", "depot", "--json", "reorders", "--supplier", "SUP-001"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    if completed.returncode != 0:
        return False, f"reorders --supplier exited {completed.returncode}: {completed.stderr[:120]}"
    rows = json.loads(completed.stdout).get("suggestions", [])
    if not rows:
        return False, "the filtered command line returned nothing"
    if any(row.get("supplierId") != "SUP-001" for row in rows):
        return False, "the command line did not propagate the supplier filter"
    return True


@check("regression.otherCommandsUnchanged")
def other_commands_unchanged():
    completed = subprocess.run(
        [sys.executable, "-m", "depot", "--json", "summary"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    if completed.returncode != 0:
        return False, f"summary exited {completed.returncode}: {completed.stderr[:120]}"
    if json.loads(completed.stdout).get("orders") != 3:
        return False, "summary no longer reports the three orders"
    return True


@check("constraint.layerDirection")
def layer_direction():
    core = os.path.join(WORKSPACE, "depot", "core")
    for root, _dirs, files in os.walk(core):
        for name in files:
            if not name.endswith(".py"):
                continue
            with open(os.path.join(root, name), encoding="utf-8") as handle:
                tree = ast.parse(handle.read())
            for node in ast.walk(tree):
                module = None
                if isinstance(node, ast.ImportFrom):
                    module = node.module
                elif isinstance(node, ast.Import) and node.names:
                    module = node.names[0].name
                if module and module.startswith("depot") and not module.startswith("depot.core"):
                    return False, f"{name} imports {module}; the domain layer must not reach upward"
    return True
