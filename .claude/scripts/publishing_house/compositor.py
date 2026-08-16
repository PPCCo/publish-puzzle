"""Deterministic composite-panel compositor.

Assembles ONE indivisible composited PNG per composite brief from
single-object component images + REAL caption text set in a rights-cleared,
embeddable repo font. This is the assembler half of Plan B; component
generation reuses the flux + ``image-gen ingest`` path unchanged.

Why this exists: flux-schnell renders clean single-object study panels but
fabricates captions and miscounts multi-object comparison panels. So the
composite clue panels are assembled deterministically instead of prompted as
one image. The approved prototype layout spec requires each panel to be ONE
indivisible composited-to-scale figure (scale-integrity rule R1): compositing
happens INSIDE the asset and it is delivered as a single PNG.

Determinism (mirrors the design-policy engine + the epub/print builders'
byte-reproducibility discipline): no network, no clock read, no RNG, stable
iteration order, fixed PNG encoder options -> identical inputs produce a
byte-identical PNG and therefore a stable registered hash.

Font gate (the hard dependency on Plan A): captions are drawn ONLY with a
font that (a) has a ``cleared`` rights record for the project (shift-left
selection) AND (b) resolves to a real embeddable font file bundled in-repo via
the dependency registry's ``font_file_path``. If either is missing, ``compose``
refuses with an actionable message -- it never silently falls back to a system
font, which would re-open the exact license hole Plan A closes.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifacts import register_artifact
from .dependencies import font_registry
from .paths import ProjectPaths
from .rights import add_rights_record
from .util import (
    atomic_write_json,
    load_json,
    load_yaml,
    sha256_path,
    slugify,
    utc_now,
)

SPEC_SCHEMA = "composite-spec.schema.json"

_DEFAULT_MAX_PT = 40
_DEFAULT_MIN_PT = 10
_PT_STEP = 1  # deterministic font-fit descent step


class FontNotClearedError(RuntimeError):
    """Raised when no cleared, file-resolvable font is available (Plan A gate)."""


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def _cleared_font_families(root: Path, project_id: str) -> list[str]:
    """Families that carry a ``cleared`` font rights record for the project.

    Deterministic: ledger order preserved, de-duplicated stably. The record's
    ``asset_path`` is ``[selected dependency] font:<family> (<role>)`` (written
    by ``dependencies.select_font``); we parse the family back out of it.
    """
    paths = ProjectPaths(root, project_id).require()
    ledger = load_json(paths.rights_ledger, {"records": []})
    families: list[str] = []
    for record in ledger.get("records", []):
        if record.get("asset_type") != "font":
            continue
        if record.get("clearance_status") != "cleared":
            continue
        asset_path = record.get("asset_path") or ""
        marker = "font:"
        if marker in asset_path:
            tail = asset_path.split(marker, 1)[1]
            family = tail.split(" (", 1)[0].strip()
            if family and family not in families:
                families.append(family)
    return families


def resolve_cleared_font(
    root: Path,
    project_id: str,
    family: str | None = None,
) -> tuple[str, Path]:
    """Resolve a (family, absolute-font-file-path) that passes the Plan A gate.

    Requires BOTH a ``cleared`` font rights record for the project AND a
    registry ``font_file_path`` that resolves to a real in-repo file. Raises
    :class:`FontNotClearedError` with an actionable message otherwise.

    When ``family`` is given it must itself be cleared; otherwise the first
    cleared family (ledger order) that also has a resolvable bundled file wins.
    """
    cleared = _cleared_font_families(root, project_id)
    if not cleared:
        raise FontNotClearedError(
            "No cleared font for this project. Run the font shift-left first: "
            "`ph_cli.py dependency select <project-id> --family <family>` "
            "(Plan A). The compositor never falls back to a system font."
        )

    if family is not None:
        if family not in cleared:
            raise FontNotClearedError(
                f"Font family {family!r} is not cleared for this project. "
                f"Cleared families: {', '.join(cleared) or '(none)'}. "
                "Select/clear it via `dependency select` first."
            )
        candidates = [family]
    else:
        candidates = cleared

    known = {font["family"]: font for font in font_registry(root)}
    missing_file: list[str] = []
    for candidate in candidates:
        entry = known.get(candidate)
        if entry is None:
            continue
        rel = entry.get("font_file_path")
        if not rel:
            missing_file.append(candidate)
            continue
        absolute = (root / rel).resolve()
        # Keep the resolved font file inside the repository (rule 17/18).
        try:
            absolute.relative_to(root.resolve())
        except ValueError as exc:  # pragma: no cover - defensive
            raise FontNotClearedError(
                f"Font file path for {candidate!r} escapes the repository: {rel}"
            ) from exc
        if absolute.is_file():
            return candidate, absolute
        missing_file.append(candidate)

    raise FontNotClearedError(
        "Font is license-cleared but no embeddable font FILE is bundled yet for "
        f"{', '.join(missing_file) or 'the cleared family'}. Bundle the cleared "
        ".ttf/.otf under .claude/config/fonts/ and set its `font_file_path` in "
        ".claude/config/dependencies.default.json (or dependencies.local.json). "
        "The license cleared at selection (Plan A); the concrete file is required "
        "to render real captions."
    )


def load_spec(
    root: Path,
    project_id: str,
    brief_id: str | None = None,
    spec_path: str | Path | None = None,
) -> dict[str, Any]:
    """Load and schema-validate a composite layout spec.

    Resolves ``spec_path`` if given, else
    ``visuals/composite-specs/<brief_id>.compose.json`` inside the project.
    """
    paths = ProjectPaths(root, project_id).require()
    if spec_path is not None:
        resolved = paths.resolve_inside(spec_path)
    else:
        if not brief_id:
            raise ValueError("Provide either brief_id or spec_path.")
        resolved = paths.resolve_inside(
            f"visuals/composite-specs/{brief_id}.compose.json"
        )
    spec = load_json(resolved)
    if spec is None:
        raise FileNotFoundError(f"Composite spec not found: {resolved}")

    from .validation import validate_data

    errors = validate_data(root, spec, SPEC_SCHEMA)
    if errors:
        raise ValueError(f"Invalid composite spec {resolved}: " + "; ".join(errors))
    return spec


def _fit_component(image: "Any", box_w: int, box_h: int, fit: str) -> "Any":
    from PIL import Image

    src_w, src_h = image.size
    if fit == "stretch":
        return image.resize((max(1, box_w), max(1, box_h)), Image.LANCZOS)
    if src_w == 0 or src_h == 0:
        return image
    scale_contain = min(box_w / src_w, box_h / src_h)
    scale_cover = max(box_w / src_w, box_h / src_h)
    scale = scale_cover if fit == "cover" else scale_contain
    new_w = max(1, int(src_w * scale))
    new_h = max(1, int(src_h * scale))
    resized = image.resize((new_w, new_h), Image.LANCZOS)
    if fit == "cover":
        # Deterministic centre-crop to the box.
        left = max(0, (new_w - box_w) // 2)
        top = max(0, (new_h - box_h) // 2)
        return resized.crop((left, top, left + box_w, top + box_h))
    return resized


def _matte_edge_white(image: "Any", fill: tuple[int, int, int], threshold: int) -> "Any":
    """Replace a component's near-white BACKGROUND with ``fill`` deterministically.

    Flood-fills inward from every border pixel: any pixel whose R, G and B are
    all >= ``threshold`` (i.e. near-white ground) that is reachable from the
    image edge is repainted to ``fill`` (the canvas colour). The fill stops at
    the object's edge, so near-white pixels ENCLOSED by the object (e.g. a
    highlight inside a tooth) are never reached and are preserved. Pure BFS over
    a fixed pixel order -> fully deterministic, offline, no RNG/clock.

    Components are generated on a white ground; without this they paste as white
    tiles on the cream canvas (visual-review finding VC-01/VCR-01/F-01).
    """
    from collections import deque

    from PIL import Image

    src = image.convert("RGB")
    w, h = src.size
    if w == 0 or h == 0:
        return src
    px = src.load()

    def is_ground(x: int, y: int) -> bool:
        r, g, b = px[x, y]
        return r >= threshold and g >= threshold and b >= threshold

    visited = bytearray(w * h)
    queue: deque[tuple[int, int]] = deque()
    # Seed from all four borders (stable order: top, bottom, left, right).
    for x in range(w):
        for y in (0, h - 1):
            idx = y * w + x
            if not visited[idx] and is_ground(x, y):
                visited[idx] = 1
                queue.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            idx = y * w + x
            if not visited[idx] and is_ground(x, y):
                visited[idx] = 1
                queue.append((x, y))

    while queue:
        x, y = queue.popleft()
        px[x, y] = fill
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h:
                nidx = ny * w + nx
                if not visited[nidx] and is_ground(nx, ny):
                    visited[nidx] = 1
                    queue.append((nx, ny))
    return src


_DEFAULT_MATTE_THRESHOLD = 235


def _fit_font_size(draw: "Any", text: str, font_path: Path, box_w: int, box_h: int,
                   max_pt: int, min_pt: int) -> "Any":
    """Deterministically descend point size until text fits the box."""
    from PIL import ImageFont

    pt = max(min_pt, max_pt)
    while pt >= min_pt:
        font = ImageFont.truetype(str(font_path), pt)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        if text_w <= box_w and text_h <= box_h:
            return font
        pt -= _PT_STEP
    return ImageFont.truetype(str(font_path), min_pt)


def compose(
    root: Path,
    project_id: str,
    spec: dict[str, Any],
    output_path: str | Path,
    font_family: str | None = None,
) -> dict[str, Any]:
    """Assemble one indivisible composited PNG from ``spec`` and write it.

    Deterministic + offline. Enforces the Plan A font gate before drawing any
    caption. Returns a summary dict (output path, resolved font, component +
    caption counts, the source component asset ids referenced by the spec).
    """
    from PIL import Image, ImageDraw

    paths = ProjectPaths(root, project_id).require()

    canvas = spec["canvas"]
    width = int(canvas["width"])
    height = int(canvas["height"])
    background = _hex_to_rgb(canvas.get("background", "#FFFFFF"))

    image = Image.new("RGB", (width, height), background)

    # Components: stable spec order; each opened, fitted, pasted at its box.
    for component in spec.get("components", []):
        box = component["box"]
        bx, by, bw, bh = int(box[0]), int(box[1]), int(box[2]), int(box[3])
        asset_abs = paths.resolve_inside(component["asset_path"])
        if not asset_abs.is_file():
            raise FileNotFoundError(
                f"Component asset not found for {component['id']!r}: {component['asset_path']}"
            )
        with Image.open(asset_abs) as raw:
            comp = raw.convert("RGB")
            if component.get("matte_white"):
                threshold = int(
                    component.get("matte_threshold", _DEFAULT_MATTE_THRESHOLD)
                )
                comp = _matte_edge_white(comp, background, threshold)
            fitted = _fit_component(comp, bw, bh, component.get("fit", "contain"))
            fw, fh = fitted.size
            # Deterministic centring inside the box for contain.
            paste_x = bx + max(0, (bw - fw) // 2)
            paste_y = by + max(0, (bh - fh) // 2)
            image.paste(fitted, (paste_x, paste_y))

    resolved_font_family: str | None = None
    resolved_font_path: Path | None = None
    captions = spec.get("captions", [])
    if captions:
        resolved_font_family, resolved_font_path = resolve_cleared_font(
            root, project_id, font_family or spec.get("font_family")
        )
        draw = ImageDraw.Draw(image)
        for caption in captions:
            text = caption.get("text", "")
            if not text:
                continue
            box = caption["box"]
            bx, by, bw, bh = int(box[0]), int(box[1]), int(box[2]), int(box[3])
            max_pt = int(caption.get("max_pt", _DEFAULT_MAX_PT))
            min_pt = int(caption.get("min_pt", _DEFAULT_MIN_PT))
            colour = _hex_to_rgb(caption.get("colour", "#1A1A1A"))
            font = _fit_font_size(draw, text, resolved_font_path, bw, bh, max_pt, min_pt)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            align = caption.get("align", "center")
            valign = caption.get("valign", "middle")
            if align == "left":
                tx = bx - bbox[0]
            elif align == "right":
                tx = bx + bw - text_w - bbox[0]
            else:
                tx = bx + (bw - text_w) // 2 - bbox[0]
            if valign == "top":
                ty = by - bbox[1]
            elif valign == "bottom":
                ty = by + bh - text_h - bbox[1]
            else:
                ty = by + (bh - text_h) // 2 - bbox[1]
            draw.text((tx, ty), text, font=font, fill=colour)

    out_abs = paths.resolve_inside(output_path)
    out_abs.parent.mkdir(parents=True, exist_ok=True)
    # Fixed encoder options -> byte-reproducible output (no time chunk).
    # Stamp a fixed 300dpi pHYs so downstream print/EPUB sizing never assumes
    # 72dpi (visual-review finding TR-01/VCR-05/F-03). Constant density keeps
    # the output byte-reproducible.
    image.save(out_abs, format="PNG", optimize=False, dpi=(300, 300))

    source_ids = [
        component.get("source_artifact_id")
        for component in spec.get("components", [])
        if component.get("source_artifact_id")
    ]

    return {
        "status": "pass",
        "project_id": project_id,
        "brief_id": spec.get("brief_id"),
        "output_path": str(out_abs.resolve().relative_to(paths.directory.resolve())),
        "canvas": {"width": width, "height": height},
        "component_count": len(spec.get("components", [])),
        "caption_count": len(captions),
        "font_family": resolved_font_family,
        "source_artifact_ids": source_ids,
    }


def build(
    root: Path,
    project_id: str,
    brief_id: str | None = None,
    spec_path: str | Path | None = None,
    output_path: str | Path | None = None,
    font_family: str | None = None,
) -> dict[str, Any]:
    """CLI entry: load the spec, compose, write ``visuals/assets/<brief-id>.png``."""
    spec = load_spec(root, project_id, brief_id, spec_path)
    effective_brief = brief_id or spec.get("brief_id")
    out = output_path or f"visuals/assets/{effective_brief}.png"
    return compose(root, project_id, spec, out, font_family)


def composite_ingest(
    root: Path,
    project_id: str,
    brief_id: str,
    file: str,
    source_artifact_ids: list[str] | None = None,
    spec_path: str | Path | None = None,
    actor: str = "composite-ingest",
) -> dict[str, Any]:
    """Register a composited PNG with component provenance and a rights record.

    This is the one place ingest passes a non-empty ``source_artifact_ids``: the
    composite is a DERIVATIVE of ``cleared`` flux components + a ``cleared`` font,
    so it records ``cleared`` when all inputs are cleared. Provenance names the
    compositor tool, the spec hash, and the component artifact ids. Offline:
    hashing + registry + ledger writes only. Ingestion is never review-complete —
    always queue /book-visual-review afterwards.
    """
    paths = ProjectPaths(root, project_id).require()
    absolute = paths.resolve_inside(file)
    if not absolute.exists():
        raise FileNotFoundError(f"Composited image not found: {file}")

    # Enforce the Plan A font gate at ingest too, so a hand-composited PNG cannot
    # bypass the cleared-font requirement. Records the family used.
    font_family, _font_path = resolve_cleared_font(root, project_id)

    spec_hash: str | None = None
    resolved_ids = list(source_artifact_ids or [])
    if spec_path is not None or brief_id:
        try:
            spec = load_spec(root, project_id, brief_id, spec_path)
            spec_abs = (
                paths.resolve_inside(spec_path)
                if spec_path is not None
                else paths.resolve_inside(
                    f"visuals/composite-specs/{brief_id}.compose.json"
                )
            )
            spec_hash, _ = sha256_path(spec_abs)
            if not resolved_ids:
                resolved_ids = [
                    c.get("source_artifact_id")
                    for c in spec.get("components", [])
                    if c.get("source_artifact_id")
                ]
        except (FileNotFoundError, ValueError):
            spec_hash = None

    digest, _size = sha256_path(absolute)
    project = load_yaml(paths.config, {})
    territories = (project.get("rights") or {}).get("territories") or ["WORLD"]
    formats = project.get("formats") or ["epub"]

    provenance = {
        "brief_id": brief_id,
        "creation_method": "deterministic-composite",
        "generation_method": "deterministic-composite",
        "model_or_tool": "publishing_house.compositor",
        "spec_hash": spec_hash,
        "font_family": font_family,
        "source_artifact_ids": resolved_ids,
        "ingested_at": utc_now(),
    }
    provenance_rel = f"visuals/assets/{brief_id}.provenance.json"
    atomic_write_json(paths.resolve_inside(provenance_rel), provenance)

    artifact = register_artifact(
        root,
        project_id,
        absolute,
        "illustration",
        "VISUAL_DEVELOPMENT",
        actor,
        rights_status="cleared",
        validation_status="not-run",
        source_artifact_ids=resolved_ids,
        provenance=provenance,
        active=True,
    )

    rights_record = {
        "rights_id": f"rgt-composite-{slugify(brief_id, 30)}-{digest.split(':')[1][:8]}",
        "asset_path": str(absolute.resolve().relative_to(paths.directory.resolve())),
        "asset_hash": digest,
        "asset_type": "illustration",
        "creator_or_provider": "publishing_house.compositor",
        "source": "Deterministic composite of cleared flux components + a cleared repo font.",
        "acquired_at": utc_now(),
        "creation_method": "ai-generated",
        "model_or_tool": "publishing_house.compositor",
        "human_contribution": "Layout spec authored from the approved composite brief; assembled deterministically from cleared components.",
        "license_or_contract": "Derivative of cleared components (Apache-2.0 flux output) + OFL-1.1 font.",
        "commercial_use": True,
        "modification_allowed": True,
        "attribution": None,
        "territories": territories,
        "formats": formats,
        "term_end": None,
        "consent_evidence": None,
        "disclosure_obligations": ["Disclose AI-generated images per current channel policy (e.g. KDP AI-content question)."],
        "evidence_paths": [provenance_rel],
        "clearance_status": "cleared",
        "notes": (
            "Composite derivative: all inputs (flux components + repo font) are cleared, "
            "so the composite records cleared. Component provenance is recorded via "
            "source_artifact_ids on the registered artifact."
        ),
    }
    add_rights_record(root, project_id, rights_record)

    return {
        "status": "pass",
        "project_id": project_id,
        "brief_id": brief_id,
        "artifact_id": artifact["artifact_id"],
        "asset_hash": digest,
        "rights_id": rights_record["rights_id"],
        "clearance_status": rights_record["clearance_status"],
        "source_artifact_ids": resolved_ids,
        "font_family": font_family,
        "provenance_path": provenance_rel,
        "next_action": "Queue /book-visual-review for the composited asset; do not treat ingestion as review-complete.",
    }
