"""Offline connectivity-manifest and probe-plan helpers.

This module is network-free (rule 18). The actual probing is performed by the
quarantined ``publishing_house.net.fetch`` module (invoked via ``fetch`` CLI
commands) and by the skill's one ``web_search`` attempt. Here we only:

* read the version-controlled source list (``research-sources.json``),
* print the ordered per-tier probe plan for the skill to execute,
* validate and atomically write the gitignored connectivity manifest
  (``research-connectivity.json``),
* read the manifest back (returning an ``unknown`` stub when absent).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .util import atomic_write_json, load_json, utc_now
from .validation import validate_data

_SOURCES = ".claude/config/research-sources.json"
_MANIFEST = ".claude/config/research-connectivity.json"
_MANIFEST_SCHEMA = "research-connectivity.schema.json"
_SOURCES_SCHEMA = "research-sources.schema.json"


def _sources_path(root: Path) -> Path:
    return root / _SOURCES


def _manifest_path(root: Path) -> Path:
    return root / _MANIFEST


def load_sources(root: Path) -> dict[str, Any]:
    data = load_json(_sources_path(root))
    errors = validate_data(root, data, _SOURCES_SCHEMA)
    if errors:
        raise ValueError(f"research-sources.json invalid: {'; '.join(errors)}")
    return data


def probe_plan(root: Path) -> dict[str, Any]:
    """Ordered plan the doctor skill executes: which source, which tiers, in order.

    Pure read; performs no network. Tiers within a source are already ordered
    cheapest-first in the config.
    """
    cfg = load_sources(root)
    plan: list[dict[str, Any]] = []
    for source in cfg.get("sources", []):
        plan.append({
            "id": source["id"],
            "host": source["host"],
            "tiers": source.get("tiers", []),
            "paywalled": bool(source.get("paywalled", False)),
            "topics": source.get("topics", []),
            "note": source.get("note", ""),
        })
    return {
        "schema_version": "1.0",
        "search": cfg.get("search", {}),
        "probe_order": ["cache", "web_search", "http", "browser", "assisted", "manual"],
        "sources": plan,
        "note": (
            "Execute tiers per source cheapest-first; stop at the first that returns "
            "usable content and record it as best_tier. 'assisted'/'manual' cannot be "
            "auto-verified. Write results with `connectivity write`."
        ),
    }


def write_manifest(root: Path, data: Any) -> dict[str, Any]:
    """Validate against schema and atomically write the connectivity manifest."""
    if not isinstance(data, dict):
        raise ValueError("connectivity manifest must be a JSON object")
    data.setdefault("schema_version", "1.0")
    data.setdefault("checked_at", utc_now())
    data.setdefault("web_search_available", "unknown")
    data.setdefault("http_fetch_available", "unknown")
    data.setdefault("browser_available", "unknown")
    data.setdefault("sources", [])
    errors = validate_data(root, data, _MANIFEST_SCHEMA)
    if errors:
        raise ValueError(f"connectivity manifest invalid: {'; '.join(errors)}")
    atomic_write_json(_manifest_path(root), data)
    return {"status": "written", "path": _MANIFEST, "sources": len(data.get("sources", [])),
            "web_search_available": data["web_search_available"],
            "http_fetch_available": data["http_fetch_available"],
            "browser_available": data["browser_available"]}


def show_manifest(root: Path) -> dict[str, Any]:
    path = _manifest_path(root)
    if not path.is_file():
        return {
            "schema_version": "1.0",
            "web_search_available": "unknown",
            "http_fetch_available": "unknown",
            "browser_available": "unknown",
            "sources": [],
            "note": "No connectivity manifest yet. Run /product-doctor to probe and record it.",
        }
    return load_json(path)
