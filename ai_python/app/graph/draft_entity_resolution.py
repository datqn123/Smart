"""Facade entry point for pre-draft resolution.
Exposes required APIs to graph nodes and unit tests while delegating logic to specialized submodules.
"""

from __future__ import annotations

# Re-export common helpers for unit tests
from app.graph.draft_entity_resolution_common import (
    search_products,
    search_suppliers,
    search_categories,
    pack_clarify_state,
)

# Re-export inventory checks
from app.graph.draft_inventory_resolution import (
    resolve_inventory_before_generate,
)

# Re-export catalog checks
from app.graph.draft_catalog_resolution import (
    resolve_catalog_before_generate,
    get_products_with_prices,
)
