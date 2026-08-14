"""Catalogue maintenance: rebuild the denormalised product/series roll-ups and
verify their cross-links resolve both ways.

Both catalogs are derived, never a source of truth. ``rebuild_catalog`` regenerates
products.json AND series.json (each validated against its schema before write).
``verify_catalog`` is read-only referential-integrity: it never mutates or writes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .project import sync_catalog
from .series import sync_series_catalog
from .util import load_json


def rebuild_catalog(root: Path) -> dict[str, Any]:
    """Regenerate both catalogs so their cross-links stay consistent."""
    products = sync_catalog(root)
    series = sync_series_catalog(root)
    return {
        "products": products,
        "series": series,
        "products_count": len(products.get("products", [])),
        "series_count": len(series.get("series", [])),
    }


def verify_catalog(root: Path) -> dict[str, Any]:
    """Assert the two catalogs cross-link consistently (read-only).

    Checks:
      * every ``member_project_ids`` entry in series.json exists in products.json;
      * every product ``series.series_id`` in products.json exists in series.json;
      * positions are unique per series.

    Reads the on-disk catalogs as-is (does not rebuild), so it reports real drift
    rather than masking it. Returns ``status: pass|fail`` with an error list.
    """
    catalog_dir = root / "catalog"
    products_doc = load_json(catalog_dir / "products.json", {"products": []})
    series_doc = load_json(catalog_dir / "series.json", {"series": []})

    product_ids = {
        p["project_id"] for p in products_doc.get("products", []) if p.get("project_id")
    }
    series_ids = {
        s["series_id"] for s in series_doc.get("series", []) if s.get("series_id")
    }
    errors: list[str] = []

    # series -> products: every claimed member must exist as a product.
    for entry in series_doc.get("series", []):
        sid = entry.get("series_id", "<unknown>")
        for member in entry.get("member_project_ids", []):
            if member not in product_ids:
                errors.append(
                    f"series '{sid}' references member project '{member}' "
                    f"not present in products.json"
                )
        positions = [
            slot.get("position")
            for slot in entry.get("slots", [])
            if slot.get("position") is not None
        ]
        if len(positions) != len(set(positions)):
            errors.append(f"series '{sid}' has duplicate slot positions: {sorted(positions)}")

    # products -> series: every product's series back-ref must name a real series.
    for product in products_doc.get("products", []):
        link = product.get("series")
        if isinstance(link, dict) and link.get("series_id"):
            if link["series_id"] not in series_ids:
                errors.append(
                    f"product '{product.get('project_id')}' back-references series "
                    f"'{link['series_id']}' not present in series.json"
                )

    return {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "products_count": len(product_ids),
        "series_count": len(series_ids),
    }
