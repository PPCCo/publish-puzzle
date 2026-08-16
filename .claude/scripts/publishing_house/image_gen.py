"""Image-generation orchestration — deterministic, network-free core.

This module NEVER performs network access or generates an image itself. Per
rule 18 the only sanctioned network module is ``net/fetch.py``; per
``EXTENSION_GUIDE.md`` §6 image generation is a *live connector* whose egress
lives in out-of-core MCP servers invoked from the skill/agent layer, not here.

What this module does is entirely offline:

* read the data-driven ``image_generation`` provider list from the tools config
  (``tools.default.json`` merged with an optional ``tools.local.json``);
* report provider status and each provider's ``commercial_rights_verified``
  flag + ``license_reference`` for a project (``image_gen_status``);
* regenerate a deterministic step-by-step manual generation guide from approved
  image-type illustration briefs (``build_guide``);
* ingest an already-produced image file (manual OR automated path) — hash it,
  register the artifact, and write a rights-ledger record whose
  ``commercial_use``/``clearance_status`` are driven by the NAMED provider's
  configured ``commercial_rights_verified`` flag (``ingest``).

Both the manual path and any future automated path converge on ``ingest`` for
identical provenance/rights guarantees.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .artifacts import active_hashes, list_artifacts, register_artifact
from .paths import ProjectPaths
from .rights import add_rights_record
from .util import (
    atomic_write_json,
    atomic_write_text,
    deep_merge,
    load_json,
    load_yaml,
    sha256_path,
    slugify,
    utc_now,
)

# Brief types this skill is responsible for. Programmatic diagrams/maps/charts
# stay on the existing book-generate-assets path unchanged.
IMAGE_BRIEF_TYPES = {"image", "illustration", "cover"}
ASSET_SUBDIR = "visuals/assets"


def load_tools_config(root: Path) -> dict[str, Any]:
    """Merge ``tools.default.json`` with an optional ``tools.local.json``.

    Mirrors :func:`util.load_company_config`. Offline read only.
    """
    default = load_json(root / ".claude" / "config" / "tools.default.json", {})
    local_path = root / ".claude" / "config" / "tools.local.json"
    if local_path.exists():
        return deep_merge(default, load_json(local_path, {}))
    return default


def image_generation_config(root: Path) -> dict[str, Any]:
    return load_tools_config(root).get("image_generation", {}) or {}


def provider_registry(root: Path) -> list[dict[str, Any]]:
    """Normalized provider list, sorted by name for deterministic output."""
    providers = image_generation_config(root).get("providers", []) or []
    normalized: list[dict[str, Any]] = []
    for entry in providers:
        normalized.append(
            {
                "name": entry.get("name"),
                "kind": entry.get("kind", "local"),
                "mcp_server": entry.get("mcp_server"),
                "model": entry.get("model"),
                "license_reference": entry.get("license_reference"),
                "commercial_rights_verified": bool(entry.get("commercial_rights_verified", False)),
                "credential_env": entry.get("credential_env"),
                "notes": entry.get("notes", ""),
            }
        )
    return sorted(normalized, key=lambda item: item.get("name") or "")


def get_provider(root: Path, name: str) -> dict[str, Any]:
    for provider in provider_registry(root):
        if provider["name"] == name:
            return provider
    known = ", ".join(p["name"] for p in provider_registry(root)) or "(none configured)"
    raise ValueError(f"Unknown image_generation provider: {name!r}. Configured providers: {known}")


def _load_briefs(paths: ProjectPaths, brief_id: str | None = None) -> list[dict[str, Any]]:
    briefs_dir = paths.directory / "visuals" / "briefs"
    if not briefs_dir.is_dir():
        return []
    briefs: list[dict[str, Any]] = []
    for path in sorted(briefs_dir.glob("*.json")):
        data = load_json(path, {})
        if not isinstance(data, dict) or "brief_id" not in data:
            continue
        if brief_id is not None and data.get("brief_id") != brief_id:
            continue
        briefs.append(data)
    return briefs


def _is_image_brief(brief: dict[str, Any]) -> bool:
    # A brief is image-generatable when it carries a generation_prompt.positive.
    # `type` is not a schema field on the brief today, so we key on the prompt
    # (and treat every brief that has one as in scope), matching what the guide
    # and ingest can actually act on.
    prompt = brief.get("generation_prompt") or {}
    return bool(prompt.get("positive"))


def _recommended_provider(root: Path, brief: dict[str, Any]) -> dict[str, Any]:
    """Pick a provider for a brief: the brief's preferred_provider if valid,
    else the configured default_provider, else the first verified provider.
    Deterministic and offline."""
    config = image_generation_config(root)
    preferred = brief.get("preferred_provider")
    registry = {p["name"]: p for p in provider_registry(root)}
    if preferred and preferred in registry:
        return registry[preferred]
    default = config.get("default_provider")
    if default and default in registry:
        return registry[default]
    verified = [p for p in provider_registry(root) if p["commercial_rights_verified"]]
    if verified:
        return verified[0]
    # No verified provider configured — return the first provider so the guide
    # still names something, but its verified flag will be False.
    any_provider = provider_registry(root)
    if any_provider:
        return any_provider[0]
    raise ValueError("No image_generation providers configured in tools config.")


def _guide_entry(root: Path, brief: dict[str, Any]) -> dict[str, Any]:
    prompt = brief.get("generation_prompt") or {}
    dims = brief.get("dimensions") or {}
    provider = _recommended_provider(root, brief)
    brief_id = brief["brief_id"]
    reason = (
        f"{provider['name']} ({provider['kind']}) — commercial_rights_verified="
        f"{provider['commercial_rights_verified']}; license: {provider['license_reference']}"
    )
    return {
        "brief_id": brief_id,
        "page_number": brief.get("page_number"),
        "location": brief.get("location"),
        "positive_prompt": prompt.get("positive", ""),
        "negative_prompt": prompt.get("negative", ""),
        "aspect_ratio": prompt.get("aspect_ratio"),
        "dimensions": {
            "width_px": dims.get("width_px"),
            "height_px": dims.get("height_px"),
            "dpi": dims.get("dpi"),
        },
        "style_references": list(prompt.get("style_references", []))
        or list(brief.get("continuity_references", [])),
        "recommended_provider": provider["name"],
        "recommended_provider_reason": reason,
        "commercial_rights_verified": provider["commercial_rights_verified"],
        "save_to": f"{ASSET_SUBDIR}/{brief_id}.png",
        "ingest_command": (
            f"python3 .claude/scripts/ph_cli.py image-gen ingest {brief['project_id']} "
            f"--brief-id {brief_id} --file {ASSET_SUBDIR}/{brief_id}.png "
            f"--provider {provider['name']}"
        ),
    }


def _sort_key(entry: dict[str, Any]) -> tuple[int, int, str]:
    page = entry.get("page_number")
    return (0 if isinstance(page, int) else 1, page if isinstance(page, int) else 0, entry["brief_id"])


def build_guide(root: Path, project_id: str, brief_id: str | None = None) -> dict[str, Any]:
    """Deterministically (re)generate the manual generation guide (.md + .json).

    Pure offline read/transform. Works with ``IMAGE_GEN_LIVE_ENABLED`` unset.
    """
    paths = ProjectPaths(root, project_id).require()
    briefs = [b for b in _load_briefs(paths, brief_id) if _is_image_brief(b)]
    entries = sorted((_guide_entry(root, b) for b in briefs), key=_sort_key)

    guide_dir = paths.directory / "visuals"
    json_path = guide_dir / "manual-generation-guide.json"
    md_path = guide_dir / "manual-generation-guide.md"

    guide_json = {
        "schema_version": "1.0",
        "project_id": project_id,
        "generated_at": utc_now(),
        "mode": image_generation_config(root).get("mode", "manual-only"),
        "live_enabled_env": image_generation_config(root).get("live_enabled_env"),
        "entries": entries,
    }
    atomic_write_json(json_path, guide_json)
    atomic_write_text(md_path, _render_guide_md(project_id, entries))

    return {
        "status": "pass",
        "project_id": project_id,
        "entry_count": len(entries),
        "guide_markdown": md_path.relative_to(paths.directory).as_posix(),
        "guide_json": json_path.relative_to(paths.directory).as_posix(),
        "briefs_without_prompt": [
            b["brief_id"] for b in _load_briefs(paths, brief_id) if not _is_image_brief(b)
        ],
    }


def _render_guide_md(project_id: str, entries: list[dict[str, Any]]) -> str:
    lines: list[str] = [
        f"# Manual image-generation guide — {project_id}",
        "",
        "Generate each image below on your chosen provider, save it to the exact path",
        "given, then run the ingest command so provenance and rights records are created.",
        "This guide is regenerated deterministically from approved briefs; do not hand-edit.",
        "",
    ]
    if not entries:
        lines.append("_No approved image briefs with a `generation_prompt.positive` were found._")
        lines.append("")
        return "\n".join(lines)
    for entry in entries:
        page = entry.get("page_number")
        page_label = f"page {page}" if isinstance(page, int) else (entry.get("location") or "unplaced")
        dims = entry.get("dimensions") or {}
        dim_str = ""
        if dims.get("width_px") and dims.get("height_px"):
            dim_str = f'{dims["width_px"]}×{dims["height_px"]}px'
            if dims.get("dpi"):
                dim_str += f' @ {dims["dpi"]}dpi'
        lines.extend(
            [
                f"## {entry['brief_id']} — {page_label}",
                "",
                f"- **Recommended provider:** {entry['recommended_provider_reason']}",
                f"- **Save to:** `{entry['save_to']}`",
            ]
        )
        if dim_str:
            lines.append(f"- **Dimensions:** {dim_str}")
        if entry.get("aspect_ratio"):
            lines.append(f"- **Aspect ratio:** {entry['aspect_ratio']}")
        if entry.get("style_references"):
            lines.append(f"- **Style / continuity references:** {', '.join(entry['style_references'])}")
        lines.extend(
            [
                "",
                "**Positive prompt**",
                "",
                "```",
                entry.get("positive_prompt", ""),
                "```",
                "",
            ]
        )
        if entry.get("negative_prompt"):
            lines.extend(["**Negative prompt**", "", "```", entry["negative_prompt"], "```", ""])
        lines.extend(["**After generating, run:**", "", "```", entry["ingest_command"], "```", ""])
    return "\n".join(lines)


def image_gen_status(root: Path, project_id: str) -> dict[str, Any]:
    """List configured providers (+ verified flags/licenses), mode, the live-enable
    env-var state (read from the environment, NOT a network probe), and which of
    the project's briefs are image-generatable / prompt-ready."""
    paths = ProjectPaths(root, project_id).require()
    config = image_generation_config(root)
    live_env = config.get("live_enabled_env") or "IMAGE_GEN_LIVE_ENABLED"

    all_briefs = _load_briefs(paths)
    ready = [b["brief_id"] for b in all_briefs if _is_image_brief(b)]
    missing_prompt = [b["brief_id"] for b in all_briefs if not _is_image_brief(b)]

    return {
        "status": "pass",
        "project_id": project_id,
        "mode": config.get("mode", "manual-only"),
        "default_provider": config.get("default_provider"),
        "live_enabled_env": live_env,
        "live_enabled": os.environ.get(live_env) == "1",
        "providers": provider_registry(root),
        "briefs_prompt_ready": sorted(ready),
        "briefs_missing_prompt": sorted(missing_prompt),
        "note": (
            "Provider reachability is not probed from this offline CLI. The automated "
            "path lives in out-of-core MCP servers (EXTENSION_GUIDE.md §6); this reports "
            "configuration and readiness only."
        ),
    }


def ingest(
    root: Path,
    project_id: str,
    brief_id: str,
    file: str,
    provider: str,
    seed: int | None = None,
    license_note: str | None = None,
    actor: str = "image-gen-ingest",
) -> dict[str, Any]:
    """Register an already-produced image (manual or automated) and write its
    rights record, driven by the NAMED provider's configured verified flag.

    Offline: hashing + registry + ledger writes only. No network.
    """
    paths = ProjectPaths(root, project_id).require()
    provider_entry = get_provider(root, provider)

    absolute = paths.resolve_inside(file)  # enforces inside-project path
    if not absolute.exists():
        raise FileNotFoundError(f"Image file not found: {file}")

    briefs = _load_briefs(paths, brief_id)
    brief = briefs[0] if briefs else None
    if brief is None:
        raise ValueError(f"No brief found with brief_id={brief_id!r} under visuals/briefs/")

    digest, _size = sha256_path(absolute)

    # Provenance file next to the asset (producible output; deterministic content
    # apart from the acquired-at stamp, which belongs on a ledger record).
    project = load_yaml(paths.config, {})
    territories = (project.get("rights") or {}).get("territories") or ["WORLD"]
    formats = project.get("formats") or ["epub"]

    provenance = {
        "brief_id": brief_id,
        "provider": provider,
        "provider_kind": provider_entry["kind"],
        "model_or_tool": provider_entry.get("model") or provider,
        "creation_method": "ai-generated",
        "positive_prompt": (brief.get("generation_prompt") or {}).get("positive"),
        "negative_prompt": (brief.get("generation_prompt") or {}).get("negative"),
        "seed": seed,
        "license_reference": provider_entry.get("license_reference"),
        "commercial_rights_verified": provider_entry["commercial_rights_verified"],
        "ingested_at": utc_now(),
    }
    provenance_rel = f"{ASSET_SUBDIR}/{brief_id}.provenance.json"
    atomic_write_json(paths.resolve_inside(provenance_rel), provenance)

    artifact = register_artifact(
        root,
        project_id,
        absolute,
        "illustration",
        "VISUAL_DEVELOPMENT",
        actor,
        rights_status="pending" if not provider_entry["commercial_rights_verified"] else "cleared",
        validation_status="not-run",
        source_artifact_ids=[],
        provenance=provenance,
        active=True,
    )

    verified = provider_entry["commercial_rights_verified"]
    license_ref = provider_entry.get("license_reference")
    if license_note:
        license_ref = f"{license_ref}; {license_note}" if license_ref else license_note

    rights_record = {
        "rights_id": f"rgt-img-{slugify(brief_id, 30)}-{digest.split(':')[1][:8]}",
        "asset_path": relative_asset_path(paths, absolute),
        "asset_hash": digest,
        "asset_type": "illustration",
        "creator_or_provider": provider,
        "source": f"AI generation via {provider} ({provider_entry['kind']})",
        "acquired_at": utc_now(),
        "creation_method": "ai-generated",
        "model_or_tool": provider_entry.get("model") or provider,
        "human_contribution": "Prompt authored from an approved illustration brief; asset produced under the named provider's terms.",
        "license_or_contract": license_ref,
        "commercial_use": verified,
        "modification_allowed": None,
        "attribution": None,
        "territories": territories,
        "formats": formats,
        "term_end": None,
        "consent_evidence": None,
        "disclosure_obligations": ["Disclose AI-generated images per current channel policy (e.g. KDP AI-content question)."],
        "evidence_paths": [provenance_rel],
        "clearance_status": "cleared" if verified else "pending",
        "notes": (
            f"clearance driven by provider commercial_rights_verified={verified}. "
            "An unverified provider yields a `pending` record that blocks the rights gate "
            "until a human reviews the provider's terms."
        ),
    }
    add_rights_record(root, project_id, rights_record)

    return {
        "status": "pass",
        "project_id": project_id,
        "brief_id": brief_id,
        "provider": provider,
        "commercial_rights_verified": verified,
        "artifact_id": artifact["artifact_id"],
        "asset_hash": digest,
        "rights_id": rights_record["rights_id"],
        "clearance_status": rights_record["clearance_status"],
        "provenance_path": provenance_rel,
        "next_action": "Queue /book-visual-review for the ingested asset; do not treat ingestion as review-complete.",
    }


def relative_asset_path(paths: ProjectPaths, absolute: Path) -> str:
    return absolute.resolve().relative_to(paths.directory.resolve()).as_posix()


def ai_content_disclosure(root: Path, project_id: str) -> dict[str, bool]:
    """Derive KDP AI-content disclosure booleans from ACTIVE artifacts' rights
    records. `images` is true if any active image-type artifact was produced by
    an ai-generated/ai-assisted method; `text` mirrors the manuscript. Offline."""
    paths = ProjectPaths(root, project_id).require()
    state = load_json(paths.state, {})
    current = active_hashes(state)
    ledger = load_json(paths.rights_ledger, {"records": []})
    by_hash: dict[str, dict[str, Any]] = {}
    for record in ledger.get("records", []):
        by_hash.setdefault(record.get("asset_hash", ""), record)

    image_types = {"image", "illustration", "diagram", "map", "cover"}
    ai_methods = {"ai-generated", "ai-assisted", "mixed"}
    images = False
    text = False
    for artifact in list_artifacts(root, project_id):
        if current and artifact.get("sha256") not in current:
            continue
        record = by_hash.get(artifact.get("sha256", ""))
        if not record:
            continue
        method = record.get("creation_method")
        if artifact.get("type") in image_types and method in ai_methods:
            images = True
        if artifact.get("type") == "manuscript" and method in ai_methods:
            text = True
    return {"images": images, "text": text}
