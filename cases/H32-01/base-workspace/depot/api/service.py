"""The application service that wires stores, adapters and the domain together."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from depot.adapter.config_loader import DepotConfig
from depot.core.allocation import Allocation, allocate
from depot.core.catalog import Catalog
from depot.core.inventory import Inventory
from depot.core.orders import Order
from depot.core.packing import Parcel, pack
from depot.core.picking import PickList, build_pick_list
from depot.core.pricing import OrderPricing, price_order
from depot.core.replenishment import ReorderSuggestion, suggestions
from depot.core.shipping import Carrier, CarrierBoard
from depot.core.supplier import SupplierDirectory
from depot.core.tax import TaxTable
from depot.core.units import Weight
from depot.store.carrier_store import load_carriers
from depot.store.catalog_store import load_catalog
from depot.store.inventory_store import load_inventory
from depot.store.locations_store import load_locations
from depot.store.order_store import load_orders
from depot.store.paths import DataPaths, data_paths
from depot.store.supplier_store import load_suppliers
from depot.store.tax_store import load_tax_table


@dataclass(frozen=True)
class DiscountSpec:
    name: str
    kind: str
    scope: str = "order"
    priority: int = 0
    threshold: str = "0.00"
    percent: int = 0
    category: str = ""
    code: str = ""
    amount: str = "0.00"


class DepotService:
    """One process, one data directory."""

    def __init__(self, paths: DataPaths, config: DepotConfig) -> None:
        self.paths = paths
        self.config = config
        self._cache: dict[str, object] = {}

    @classmethod
    def open(cls, data_dir: str | Path, config: DepotConfig) -> DepotService:
        return cls(data_paths(data_dir), config)

    # -- loading ---------------------------------------------------------------
    def _cached(self, key: str, loader):
        if key not in self._cache:
            self._cache[key] = loader()
        return self._cache[key]

    def reload(self) -> None:
        self._cache.clear()

    @property
    def catalog(self) -> Catalog:
        return self._cached("catalog", lambda: load_catalog(self.paths.catalog))

    @property
    def inventory(self) -> Inventory:
        return self._cached("inventory", lambda: load_inventory(self.paths.inventory))

    @property
    def suppliers(self) -> SupplierDirectory:
        return self._cached("suppliers", lambda: load_suppliers(self.paths.suppliers))

    @property
    def orders(self) -> list[Order]:
        return self._cached("orders", lambda: load_orders(self.paths.orders))

    @property
    def carriers(self) -> CarrierBoard:
        return self._cached("carriers", lambda: load_carriers(self.paths.carriers))

    @property
    def taxes(self) -> TaxTable:
        return self._cached("taxes", lambda: load_tax_table(self.paths.tax))

    @property
    def locations(self) -> dict[str, str]:
        return self._cached("locations", lambda: load_locations(self.paths.locations))

    def find_order(self, order_ref: str) -> Order:
        wanted = order_ref.strip().upper()
        for order in self.orders:
            if order.identifier.value == wanted:
                return order
        from depot.core.errors import NotFoundError

        raise NotFoundError(f"unknown order: {order_ref}", order=order_ref)

    # -- operations ------------------------------------------------------------
    def pricing(self, order: Order, rules=None, region: str | None = None) -> OrderPricing:
        return price_order(order, self.catalog, self.taxes, rules, region=region or self.config.region)

    def pick_list(self, order: Order) -> PickList:
        return build_pick_list(order, self.locations)

    def parcels(self, order: Order) -> list[Parcel]:
        return pack(order, self.catalog, Weight(self.config.max_parcel_weight_grams))

    def select_carrier(self, order: Order) -> Carrier:
        parcels = self.parcels(order)
        total = Weight(sum(self._parcel_weight(parcel).grams for parcel in parcels))
        return self.carriers.select(total, self.config.region)

    def _parcel_weight(self, parcel: Parcel) -> Weight:
        total = 0
        for sku, quantity in parcel.units.items():
            product = self.catalog.find(sku)
            if product is not None:
                total += product.weight.grams * quantity
        return Weight(total)

    def allocate(self, order: Order, *, allow_partial: bool = False) -> Allocation:
        return allocate(order, self.inventory, allow_partial=allow_partial)

    def reorder_suggestions(self) -> list[ReorderSuggestion]:
        return suggestions(self.inventory, self.suppliers, self.catalog)
