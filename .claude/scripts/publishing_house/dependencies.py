"""License-checked dependency registry + selection-time clearance.

Deterministic, network-free. This module generalizes the "shift-left" of any
license-checked dependency (fonts first) so a dependency clears AT SELECTION
TIME — during design / pre-production — instead of after the artifact that
embeds it is built. It mirrors the image-generation provider pattern in
``image_gen.py``:

* the offline registry (``.claude/config/dependencies.default.json`` merged with
  an optional ``dependencies.local.json``) declares each dependency's
  ``license_reference`` + an ``embedding_allowed`` / ``commercial_use_verified``
  pair (the analog of a provider's ``commercial_rights_verified``);
* ``select_font`` writes a rights-ledger record whose ``clearance_status`` is
  DRIVEN by those flags — ``cleared`` iff both are true, else ``pending`` — so
  an unverified family blocks the rights gate exactly like an unverified image
  provider.

No network, no clock beyond the ledger ``acquired_at`` stamp (which belongs on a
ledger record, mirroring ``image_gen.ingest``), no state-machine mutation.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .paths import ProjectPaths
from .rights import add_rights_record
from .util import deep_merge, load_json, load_yaml, slugify, utc_now

CONFIG_RELPATH = (".claude", "config", "dependencies.default.json")
LOCAL_RELPATH = (".claude", "config", "dependencies.local.json")


def load_dependency_config(root: Path) -> dict[str, Any]:
    """Merge ``dependencies.default.json`` with an optional local override.

    Mirrors :func:`image_gen.load_tools_config`. Offline read only; validated
    against ``dependency-registry.schema.json``.
    """
    default = load_json(root.joinpath(*CONFIG_RELPATH), {})
    local_path = root.joinpath(*LOCAL_RELPATH)
    config = deep_merge(default, load_json(local_path, {})) if local_path.exists() else default

    from .validation import validate_data

    errors = validate_data(root, config, "dependency-registry.schema.json")
    if errors:
        raise ValueError("Invalid dependencies.default.json: " + "; ".join(errors))
    return config


def font_registry(root: Path) -> list[dict[str, Any]]:
    """Normalized font list, sorted by family for deterministic output."""
    fonts = load_dependency_config(root).get("fonts", []) or []
    normalized: list[dict[str, Any]] = []
    for entry in fonts:
        normalized.append(
            {
                "family": entry.get("family"),
                "role_tags": list(entry.get("role_tags", [])),
                "source": entry.get("source"),
                "license_reference": entry.get("license_reference"),
                "license_text_path": entry.get("license_text_path"),
                "embedding_allowed": bool(entry.get("embedding_allowed", False)),
                "commercial_use_verified": bool(entry.get("commercial_use_verified", False)),
                "territories": list(entry.get("territories", []) or ["WORLD"]),
                "font_file_path": entry.get("font_file_path"),
                "notes": entry.get("notes", ""),
            }
        )
    return sorted(normalized, key=lambda item: item.get("family") or "")


def get_font(root: Path, family: str) -> dict[str, Any]:
    for font in font_registry(root):
        if font["family"] == family:
            return font
    known = ", ".join(f["family"] for f in font_registry(root)) or "(none configured)"
    raise ValueError(f"Unknown font family: {family!r}. Registered families: {known}")


def font_is_clearable(font: dict[str, Any]) -> bool:
    """A font clears only when it is both embeddable AND commercial-verified."""
    return bool(font["embedding_allowed"]) and bool(font["commercial_use_verified"])


def _selection_hash(root: Path, font: dict[str, Any]) -> str:
    """Deterministic ``sha256:`` identity for a selected-but-not-embedded font.

    Per Plan-A D4 option (a): the LICENSE clears at selection against the
    registry entry + its recorded license evidence, so the rights record binds
    to a stable identity now; the concrete embedded ``.ttf`` is hashed and
    registered as its own artifact at build time. We hash the registry identity
    (family + license reference) together with the license-evidence file bytes
    when present, so the record's ``asset_hash`` is reproducible and traceable to
    real evidence rather than a 64-zero placeholder.
    """
    digest = hashlib.sha256()
    digest.update(b"font-selection\x00")
    digest.update((font.get("family") or "").encode("utf-8"))
    digest.update(b"\x00")
    digest.update((font.get("license_reference") or "").encode("utf-8"))
    digest.update(b"\x00")
    evidence_rel = font.get("license_text_path")
    if evidence_rel:
        evidence_path = root / evidence_rel
        if evidence_path.is_file():
            digest.update(evidence_path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def select_font(
    root: Path,
    project_id: str,
    family: str,
    role: str = "body",
    actor: str = "dependency-select",
) -> dict[str, Any]:
    """Clear a font dependency at SELECTION time and write its rights record.

    The record's ``clearance_status`` is driven by the registry entry: ``cleared``
    iff the family is embeddable AND commercial-use-verified, else ``pending``.
    This shifts the font license check LEFT of the layout/epub build that embeds
    it. Offline: registry read + ledger write only.
    """
    paths = ProjectPaths(root, project_id).require()
    font = get_font(root, family)

    project = load_yaml(paths.config, {})
    territories = font.get("territories") or (project.get("rights") or {}).get("territories") or ["WORLD"]
    formats = project.get("formats") or ["epub"]

    clearable = font_is_clearable(font)
    clearance_status = "cleared" if clearable else "pending"
    asset_hash = _selection_hash(root, font)
    family_slug = slugify(family, 24)
    role_slug = slugify(role, 12)

    evidence_paths = [p for p in [font.get("license_text_path")] if p]

    rights_record = {
        "rights_id": f"rgt-font-{role_slug}-{family_slug}",
        "asset_path": f"[selected dependency] font:{family} ({role})",
        "asset_hash": asset_hash,
        "asset_type": "font",
        "creator_or_provider": font.get("source") or family,
        "source": f"Open-licensed font family selected from the dependency registry ({font.get('license_reference')}).",
        "acquired_at": utc_now(),
        "creation_method": "open-license",
        "model_or_tool": None,
        "human_contribution": "Font family selected at design/pre-production from the offline license-checked dependency registry.",
        "license_or_contract": font.get("license_reference"),
        "commercial_use": bool(font["commercial_use_verified"]),
        "modification_allowed": True if font.get("license_reference") == "OFL-1.1" else None,
        "attribution": None,
        "territories": territories,
        "formats": formats,
        "term_end": None,
        "consent_evidence": None,
        "disclosure_obligations": [],
        "evidence_paths": evidence_paths,
        "clearance_status": clearance_status,
        "notes": (
            f"clearance driven by embedding_allowed={font['embedding_allowed']} "
            f"AND commercial_use_verified={font['commercial_use_verified']}. "
            "License cleared at selection (shift-left); the concrete embedded font "
            "file is hashed and registered as its own artifact at build time. "
            "An unverified family yields a `pending` record that blocks the rights gate."
        ),
    }
    add_rights_record(root, project_id, rights_record)

    return {
        "status": "pass" if clearable else "pending",
        "project_id": project_id,
        "family": family,
        "role": role,
        "license_reference": font.get("license_reference"),
        "embedding_allowed": font["embedding_allowed"],
        "commercial_use_verified": font["commercial_use_verified"],
        "rights_id": rights_record["rights_id"],
        "asset_hash": asset_hash,
        "clearance_status": clearance_status,
        "font_file_path": font.get("font_file_path"),
        "next_action": (
            "Font license cleared at selection. Bundle the concrete .ttf/.otf and register it "
            "as an artifact at layout/build; the compositor and epub build require this cleared "
            "family. An unverified family (pending) must be reviewed by a human before use."
        ),
    }
