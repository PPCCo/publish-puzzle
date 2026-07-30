"""Offline marketing / listing preparation.

All three builders are OFFLINE: they prepare copy, keywords, categories, and
per-platform launch guidance from the project's own metadata and channel
profiles. They perform NO external writes or logins --- every claim in the listing
copy is derived from recorded project facts, and platform steps are guidance for
a human to execute manually. Outputs land under ``marketing/`` and are advisory,
not gated evidence.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .paths import ProjectPaths
from .util import atomic_write_json, load_json, load_yaml, utc_now

_CHANNEL_STEPS = {
    "kdp": [
        "Recheck current KDP format, trim, bleed, and cover specifications.",
        "Create the title; enter metadata from listing.json; set categories/keywords.",
        "Upload interior and cover; inspect in the current previewer.",
        "Order a physical proof before publishing.",
        "Set territories, pricing, and complete AI-content disclosure.",
        "Publish only after recording a valid release authorization.",
    ],
    "etsy": [
        "Create a digital listing; upload preview images and the print-ready files.",
        "Enter title, description, and tags from the listing kit.",
        "Set the digital-download delivery and commercial-use terms.",
        "Confirm shop policies, pricing, and file formats.",
        "Publish only after recording a valid release authorization.",
    ],
    "gumroad": [
        "Create a product; upload the printable bundle.",
        "Enter name, description, and pricing from the listing kit.",
        "Set the license terms and any variant tiers.",
        "Publish only after recording a valid release authorization.",
    ],
    "generic": [
        "Prepare listing copy and files from the marketing kit.",
        "Follow the target platform's current upload and disclosure requirements.",
        "Publish only after recording a valid release authorization.",
    ],
}


def _metadata(paths: ProjectPaths) -> dict[str, Any]:
    target = paths.directory / "metadata" / "book.json"
    if target.exists():
        try:
            return load_json(target)
        except Exception:  # noqa: BLE001
            return {}
    return {}


def build_launch_guide(root: Path, project_id: str) -> dict[str, Any]:
    paths = ProjectPaths(root, project_id).require()
    project = load_yaml(paths.config)
    channels = project.get("sales_channels", [])
    guides = {channel: _CHANNEL_STEPS.get(channel, _CHANNEL_STEPS["generic"]) for channel in channels}
    result = {
        "schema_version": "1.0",
        "project_id": project_id,
        "generated_at": utc_now(),
        "external_write_performed": False,
        "channels": channels,
        "per_channel_steps": guides,
        "note": "Offline guidance only. No external logins or writes are performed by the framework.",
    }
    atomic_write_json(paths.directory / "marketing" / "launch-guide.json", result)
    return result


def build_listing_kit(root: Path, project_id: str) -> dict[str, Any]:
    paths = ProjectPaths(root, project_id).require()
    project = load_yaml(paths.config)
    metadata = _metadata(paths)
    title = metadata.get("title") or project.get("working_title") or project.get("topic")
    family = project.get("book_type") or project.get("product_type") or "puzzle-book"
    audience = project.get("audience", "adult-general")
    # Keywords are derived from recorded facts (topic, family, audience), never invented claims.
    derived_keywords = list(
        dict.fromkeys(
            [
                str(project.get("topic", "")).strip(),
                family.replace("-", " "),
                audience.replace("-", " "),
                *(metadata.get("keywords") or []),
            ]
        )
    )
    derived_keywords = [k for k in derived_keywords if k]
    result = {
        "schema_version": "1.0",
        "project_id": project_id,
        "generated_at": utc_now(),
        "title": title,
        "subtitle": metadata.get("subtitle"),
        "description": metadata.get("description") or f"An original {family.replace('-', ' ')} for {audience.replace('-', ' ')} readers.",
        "keywords": derived_keywords[:7],
        "categories": metadata.get("subjects", []),
        "claims_are_derived_from_recorded_facts": True,
        "note": "Every listing claim traces to project config or recorded metadata; verify against live platform limits before upload.",
    }
    atomic_write_json(paths.directory / "marketing" / "listing-kit.json", result)
    return result


def build_marketing_kit(root: Path, project_id: str) -> dict[str, Any]:
    guide = build_launch_guide(root, project_id)
    listing = build_listing_kit(root, project_id)
    paths = ProjectPaths(root, project_id).require()
    result = {
        "schema_version": "1.0",
        "project_id": project_id,
        "generated_at": utc_now(),
        "launch_guide": guide,
        "listing_kit": listing,
        "external_write_performed": False,
    }
    atomic_write_json(paths.directory / "marketing" / "marketing-kit.json", result)
    return result
