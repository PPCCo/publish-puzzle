"""Bridge committed coloring line-art briefs into image-generation briefs.

Deterministic, network-free. Coloring books ship ORIGINAL line-art only; the
``line-art-brief`` content generator (``generators/coloring.py``) emits a
structured, self-contained original brief — subject, complexity band, minimum
line weight, target region count, composition, style, and an originality
attestation — into ``content/coloring/*-batch.json``. Those items carry NO
``generation_prompt`` and live in a different location from the image-gen briefs
(``visuals/briefs/``), so the existing render → ingest → rights machinery cannot
pick them up as-is.

This module bridges the gap: for each ``line-art-brief`` item it emits one
schema-valid ``visuals/briefs/<brief_id>.json`` illustration brief carrying a
pure-black-and-white ``generation_prompt.positive`` (plus a recorded negative),
so ``image_gen.build_guide`` / ``image_gen_status`` / ``image_gen.ingest`` act on
it with zero change to those functions. It also writes a machine-readable
``<brief_id>.attestation.json`` sidecar preserving the raw originality
attestation, because the shared ``illustration-brief.schema.json`` is
``additionalProperties: false`` and must not be changed.

The bridge produces briefs only; it renders nothing and clears nothing. Live
rendering is a deferred human step (rule 17). Coloring interiors are
``colour_interior = false`` (rule 22) — the prompt asks for pure B&W outlines.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .paths import ProjectPaths
from .util import atomic_write_json, load_json, load_yaml, utc_now
from .validation import validate_data

# The trim → (width_in, height_in) map is single-sourced from the layout module
# so a bridged brief's pixel dimensions match the trim the interior builder will
# render it into. Never duplicate the trim table.
from .layout import _trim as _trim_inches

_DEFAULT_DPI = 300
_COLORING_PURPOSE = "coloring interior page"


def _dimensions(project: dict[str, Any]) -> dict[str, int]:
    """Pixel dimensions from the project trim × dpi. Deterministic, offline."""
    width_in, height_in = _trim_inches(project)
    dpi = int(
        ((project.get("production") or {}).get("print") or {}).get("dpi")
        or _DEFAULT_DPI
    )
    return {
        "width_px": int(round(width_in * dpi)),
        "height_px": int(round(height_in * dpi)),
        "dpi": dpi,
    }


def _positive_prompt(payload: dict[str, Any]) -> str:
    subject = str(payload.get("subject", "")).strip()
    composition = str(payload.get("composition", "")).strip()
    style = str(payload.get("style", "")).strip()
    band = str(payload.get("complexity_band", "standard")).strip()
    min_line = payload.get("min_line_weight_pt")
    line_clause = f"{min_line}pt minimum line weight" if min_line else "bold minimum line weight"
    return (
        f"black and white line art coloring page, {subject}, {composition}, {style}, "
        f"clean bold closed outlines, {line_clause}, no shading, no fill, no grayscale, "
        f"no gradients, pure white background, high contrast, printable, {band} detail level"
    )


_NEGATIVE_PROMPT = (
    "color, colour, shading, gradient, grayscale, grey fill, watermark, text, signature, frame"
)


def _alt_text(payload: dict[str, Any]) -> str:
    subject = str(payload.get("subject", "an original subject")).strip()
    composition = str(payload.get("composition", "")).strip()
    tail = f"; {composition}" if composition else ""
    return f"Black-and-white line-art coloring page: {subject}{tail}."


def _rights_constraints(attestation: dict[str, Any]) -> list[str]:
    """Flatten the originality attestation into schema-allowed string constraints."""
    constraints = [
        "Original line-art only; no tracing, copying, or derivation from any "
        "third-party or IP-protected photograph, artwork, character, or logo.",
        "No imitation of a living artist by name or recognisable style.",
        "Must clear the rights gate as an original before advancing past interior.",
    ]
    statement = str(attestation.get("statement", "")).strip()
    if statement:
        constraints.append(statement)
    return constraints


def briefs_from_coloring(
    root: Path,
    project_id: str,
    provider: str | None = None,
    actor: str = "coloring-bridge",
) -> dict[str, Any]:
    """Emit one image brief (+ attestation sidecar) per ``line-art-brief`` item.

    Deterministic and offline. Each emitted brief is validated against
    ``illustration-brief.schema.json`` before it is written; a validation error
    aborts before any write for that brief. Returns a summary listing every
    emitted brief_id.
    """
    paths = ProjectPaths(root, project_id).require()
    project = load_yaml(paths.config, {}) or {}

    # Resolve preferred provider deterministically: explicit arg wins, else the
    # configured default. Advisory only — image_gen re-resolves at guide/ingest.
    from . import image_gen  # lazy: avoid Pillow-adjacent import at module load

    default_provider = image_gen.image_generation_config(root).get("default_provider")
    preferred_provider = provider or default_provider

    coloring_dir = paths.directory / "content" / "coloring"
    briefs_dir = paths.directory / "visuals" / "briefs"
    dimensions = _dimensions(project)

    emitted: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    errors: list[str] = []

    if coloring_dir.is_dir():
        for batch_path in sorted(coloring_dir.glob("*-batch.json")):
            batch = load_json(batch_path, {})
            if not isinstance(batch, dict):
                continue
            for item in batch.get("items", []):
                if item.get("content_type") != "line-art-brief":
                    continue
                index = int(item.get("index", 0))
                payload = item.get("payload") or {}
                attestation = payload.get("originality_attestation") or {}
                brief_id = f"clr-line-art-brief-{index:03d}"

                brief = {
                    "brief_id": brief_id,
                    "project_id": project_id,
                    "location": f"coloring interior, page {index + 1}",
                    "page_number": index + 1,
                    "purpose": _COLORING_PURPOSE,
                    "scene_or_subject": str(payload.get("subject", "")).strip(),
                    "required_elements": [
                        "clean closed outlines",
                        f"minimum line weight {payload.get('min_line_weight_pt')}pt",
                        f"target regions {payload.get('target_region_count')}",
                    ],
                    "prohibited_elements": [
                        "shading",
                        "grayscale fills",
                        "colour",
                        "gradients",
                        "traced or derivative content",
                    ],
                    "composition": str(payload.get("composition", "")).strip()
                    or "single centred subject, generous margins",
                    "colour_and_lighting": "pure black outlines on a pure white background; no shading or fill",
                    "dimensions": dimensions,
                    "alt_text_draft": _alt_text(payload),
                    "rights_constraints": _rights_constraints(attestation),
                    "generation_prompt": {
                        "positive": _positive_prompt(payload),
                        "negative": _NEGATIVE_PROMPT,
                        "seed": item.get("seed"),
                    },
                    "image_complexity": "simple",
                    "preferred_provider": preferred_provider,
                    "status": "draft",
                }

                schema_errors = validate_data(root, brief, "illustration-brief.schema.json")
                if schema_errors:
                    errors.append(f"{brief_id}: {'; '.join(schema_errors)}")
                    skipped.append({"brief_id": brief_id, "reason": "schema-invalid"})
                    continue

                brief_path = briefs_dir / f"{brief_id}.json"
                atomic_write_json(brief_path, brief)

                # Machine-readable attestation sidecar. The shared brief schema is
                # additionalProperties:false, so the originality attestation cannot
                # live in the brief itself — the review + rights path read it here.
                sidecar = {
                    "schema_version": "1.0",
                    "brief_id": brief_id,
                    "project_id": project_id,
                    "source_batch": batch_path.relative_to(paths.directory).as_posix(),
                    "source_index": index,
                    "originality_attestation": attestation,
                    "min_line_weight_pt": payload.get("min_line_weight_pt"),
                    "target_region_count": payload.get("target_region_count"),
                    "complexity_band": payload.get("complexity_band"),
                    "bridged_at": utc_now(),
                    "bridged_by": actor,
                }
                atomic_write_json(briefs_dir / f"{brief_id}.attestation.json", sidecar)

                emitted.append(
                    {
                        "brief_id": brief_id,
                        "page_number": index + 1,
                        "brief_path": brief_path.relative_to(paths.directory).as_posix(),
                    }
                )

    return {
        "status": "pass" if not errors else "fail",
        "project_id": project_id,
        "provider": preferred_provider,
        "briefs_emitted": emitted,
        "count": len(emitted),
        "skipped": skipped,
        "errors": errors,
        "briefs_dir": briefs_dir.relative_to(paths.directory).as_posix(),
    }
