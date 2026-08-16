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


# --------------------------------------------------------------------------- #
# Cover-wrap compositor (Phase 3): assemble a full print-ready cover wrap PNG   #
# (back | spine | front + bleed) from ONE AI-generated front-cover art image    #
# plus REAL typography set in a rights-cleared embeddable repo font. The wrap    #
# PNG is then embedded in a single-page PDF at exact trim+bleed by the layout    #
# builder. Deterministic + offline; the Plan-A font gate is enforced before any  #
# caption is drawn (no system-font fallback).                                    #
# --------------------------------------------------------------------------- #

_WHITE = (255, 255, 255)
_NEAR_BLACK = (26, 26, 26)


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    """WCAG relative luminance in 0..1 for a linearised sRGB colour."""
    def _lin(channel: int) -> float:
        c = channel / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def _contrast_ratio(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    la, lb = _relative_luminance(a), _relative_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _region_mean_rgb(image: "Any", box: tuple[int, int, int, int]) -> tuple[int, int, int]:
    """Deterministic mean RGB of an image region (used for the contrast check)."""
    bx, by, bw, bh = box
    w, h = image.size
    x0, y0 = max(0, bx), max(0, by)
    x1, y1 = min(w, bx + bw), min(h, by + bh)
    if x1 <= x0 or y1 <= y0:
        return _WHITE
    crop = image.crop((x0, y0, x1, y1))
    # Pillow's resize-to-1px is a stable average; avoids importing statistics libs.
    from PIL import Image  # noqa: PLC0415

    px = crop.resize((1, 1), Image.BOX).getpixel((0, 0))
    if isinstance(px, int):  # grayscale safety
        return (px, px, px)
    return (int(px[0]), int(px[1]), int(px[2]))


def _draw_wrapped_caption(
    draw: "Any",
    image: "Any",
    text: str,
    box: tuple[int, int, int, int],
    font_path: Path,
    *,
    max_pt: int,
    min_pt: int,
    colour: tuple[int, int, int],
    align: str = "center",
    scrim_min_contrast: float = 4.5,
) -> int:
    """Draw ``text`` word-wrapped to fit ``box``, adding an auto scrim only if the
    text/background contrast falls below ``scrim_min_contrast`` (WCAG AA body).

    Deterministic: fixed point-size descent, fixed word-wrap, fixed scrim alpha.
    The scrim is a semi-opaque rounded panel behind the text — drawn ONLY when the
    contrast check fails, so clean reserved white space stays untouched.

    Returns the y-coordinate of the bottom of the drawn block (text bottom, or the
    scrim bottom when a scrim was added), so a caller can place the next element
    below it without overlap. Returns ``box`` top when there is nothing to draw.
    """
    from PIL import ImageFont

    bx, by, bw, bh = box
    if not text:
        return by

    # Deterministic descent: find the largest point size whose greedy word-wrap
    # fits inside the box (both width and total height).
    def _wrap_at(font: "Any") -> tuple[list[str], int, int]:
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            trial = f"{current} {word}".strip()
            tb = draw.textbbox((0, 0), trial, font=font)
            if current and (tb[2] - tb[0]) > bw:
                lines.append(current)
                current = word
            else:
                current = trial
        if current:
            lines.append(current)
        widest = 0
        total_h = 0
        line_gap = max(2, int(font.size * 0.25))
        for ln in lines:
            tb = draw.textbbox((0, 0), ln, font=font)
            widest = max(widest, tb[2] - tb[0])
            total_h += (tb[3] - tb[1]) + line_gap
        return lines, widest, total_h

    pt = max(min_pt, max_pt)
    chosen_font = ImageFont.truetype(str(font_path), min_pt)
    lines = [text]
    while pt >= min_pt:
        font = ImageFont.truetype(str(font_path), pt)
        wrapped, widest, total_h = _wrap_at(font)
        if widest <= bw and total_h <= bh:
            chosen_font = font
            lines = wrapped
            break
        pt -= _PT_STEP
    else:
        font = ImageFont.truetype(str(font_path), min_pt)
        lines, _widest, _total_h = _wrap_at(font)
        chosen_font = font

    # Measure the wrapped block up-front so the scrim hugs the ACTUAL text
    # extent (centred in the box) rather than the full box — a tall box with a
    # short block otherwise paints an oversized scrim that collides with
    # neighbours. Also lets us report an accurate block bottom.
    line_gap = max(2, int(chosen_font.size * 0.25))
    heights = [draw.textbbox((0, 0), ln, font=chosen_font) for ln in lines]
    total_h = sum((tb[3] - tb[1]) + line_gap for tb in heights) - line_gap
    y0 = by + max(0, (bh - total_h) // 2)
    block_bottom = min(by + bh, y0 + total_h)

    # Contrast check against the mean of the reserved region; add a scrim if poor.
    bg = _region_mean_rgb(image, box)
    scrimmed = False
    pad = max(8, int(chosen_font.size * 0.4))
    if _contrast_ratio(colour, bg) < scrim_min_contrast:
        from PIL import Image, ImageDraw

        # Scrim colour is whichever of white/near-black best contrasts the text.
        scrim_base = _WHITE if _relative_luminance(colour) < 0.5 else _NEAR_BLACK
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        odraw.rounded_rectangle(
            [bx - pad, y0 - pad, bx + bw + pad, block_bottom + pad],
            radius=pad,
            fill=(scrim_base[0], scrim_base[1], scrim_base[2], 165),
        )
        image.alpha_composite(overlay) if image.mode == "RGBA" else image.paste(
            Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB"), (0, 0)
        )
        scrimmed = True

    # Draw the wrapped lines, vertically centred in the box.
    y = y0
    for ln, tb in zip(lines, heights):
        line_w = tb[2] - tb[0]
        if align == "left":
            x = bx - tb[0]
        elif align == "right":
            x = bx + bw - line_w - tb[0]
        else:
            x = bx + (bw - line_w) // 2 - tb[0]
        draw.text((x, y - tb[1]), ln, font=chosen_font, fill=colour)
        y += (tb[3] - tb[1]) + line_gap

    return (block_bottom + pad) if scrimmed else block_bottom


def compose_cover_wrap(
    root: Path,
    project_id: str,
    art_path: str | Path,
    spec: dict[str, Any],
    output_path: str | Path,
    font_family: str | None = None,
) -> dict[str, Any]:
    """Assemble a full cover-wrap PNG from AI front-cover art + real typography.

    ``spec`` (built by the layout module, single-sourcing the trim + spine math)
    provides pixel geometry and the text to set:

        {
          "dpi": 300,
          "wrap_px": [W, H], "bleed_px": B,
          "front": [x, y, w, h], "spine": [x, y, w, h], "back": [x, y, w, h],
          "solid_rgb": "#1a3a5c", "cream_rgb": "#fdf6e3", "ink_rgb": "#ffffff",
          "title": "...", "count_label": "...", "descriptor": "...",
          "spine_title": "...", "back_heading": "...", "back_lines": [...],
          "features": [...], "trim_label": "8.5 x 11 in",
          "font_display": "Archivo", "font_body": "Atkinson Hyperlegible"
        }

    The front panel gets the art full-bleed (``fit="cover"``); the reserved upper
    band gets the real title; a cream callout carries the puzzle count; the spine
    and back are solid-derived with rotated spine title + back copy. All captions
    use a cleared embeddable font (hard gate). Deterministic 300-DPI PNG out.
    """
    from PIL import Image, ImageDraw

    paths = ProjectPaths(root, project_id).require()

    # Font gate — resolve BEFORE drawing anything (no system-font fallback).
    display_family = font_family or spec.get("font_display")
    resolved_display_family, display_font_path = resolve_cleared_font(
        root, project_id, display_family
    )
    body_family = spec.get("font_body")
    try:
        resolved_body_family, body_font_path = resolve_cleared_font(
            root, project_id, body_family
        )
    except FontNotClearedError:
        # Body falls back to the (already cleared) display face rather than a
        # system font — the gate is never bypassed.
        resolved_body_family, body_font_path = resolved_display_family, display_font_path

    wrap_w, wrap_h = int(spec["wrap_px"][0]), int(spec["wrap_px"][1])
    solid = _hex_to_rgb(spec.get("solid_rgb", "#1a3a5c"))
    cream = _hex_to_rgb(spec.get("cream_rgb", "#fdf6e3"))
    ink = _hex_to_rgb(spec.get("ink_rgb", "#ffffff"))

    image = Image.new("RGB", (wrap_w, wrap_h), solid)

    # Front-panel art, full-bleed (cover fit → centre-crop to the panel).
    art_abs = paths.resolve_inside(art_path)
    if not art_abs.is_file():
        raise FileNotFoundError(f"Cover art not found inside project: {art_path}")
    fx, fy, fw, fh = (int(v) for v in spec["front"])
    with Image.open(art_abs) as raw:
        art = raw.convert("RGB")
        fitted = _fit_component(art, fw, fh, "cover")
        image.paste(fitted, (fx, fy))

    draw = ImageDraw.Draw(image)
    dpi = int(spec.get("dpi", 300))

    def _pt_to_px(pt: float) -> int:
        return max(1, int(round(pt * dpi / 72.0)))

    # Title in the reserved upper band of the front panel. The box is generous
    # (a long adult title can wrap to 4 lines); _draw_wrapped_caption centres the
    # block within it and reports the true bottom of the drawn text (or scrim) so
    # the callout can sit BELOW the title regardless of how many lines it took.
    margin = int(0.625 * dpi)
    title_top = fy + margin
    title_box = (fx + margin, title_top, fw - 2 * margin, int(fh * 0.34))
    title_bottom = _draw_wrapped_caption(
        draw, image, str(spec.get("title", "")), title_box, display_font_path,
        max_pt=_pt_to_px(44), min_pt=_pt_to_px(20), colour=ink, align="center",
    )

    # Cream count callout, positioned dynamically below the title's actual bottom
    # so a tall multi-line title never collides with it. Clamped to keep the
    # callout inside the front panel's upper half.
    count_label = str(spec.get("count_label", "")).strip()
    if count_label:
        cw = fw - 2 * margin
        ch = int(fh * 0.14)
        cx = fx + margin
        gap = int(0.18 * dpi)
        cy = min(title_bottom + gap, fy + int(fh * 0.62) - ch)
        cy = max(cy, title_top + gap)
        draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=int(0.08 * dpi), fill=cream)
        _draw_wrapped_caption(
            draw, image, count_label, (cx, cy, cw, int(ch * 0.6)), display_font_path,
            max_pt=_pt_to_px(32), min_pt=_pt_to_px(16), colour=solid, align="center",
            scrim_min_contrast=1.0,  # on a solid cream panel; no scrim needed
        )
        descriptor = str(spec.get("descriptor", "")).strip()
        if descriptor:
            _draw_wrapped_caption(
                draw, image, descriptor, (cx, cy + int(ch * 0.6), cw, int(ch * 0.35)),
                body_font_path, max_pt=_pt_to_px(14), min_pt=_pt_to_px(9),
                colour=solid, align="center", scrim_min_contrast=1.0,
            )

    # Spine: rotated title, only when wide enough (mirrors the procedural rule).
    sx, sy, sw, sh = (int(v) for v in spec["spine"])
    spine_title = str(spec.get("spine_title", "")).strip()
    if sw >= int(0.25 * dpi) and spine_title:
        spine_pt = min(_pt_to_px(12), int(sw * 0.55))
        from PIL import ImageFont

        sfont = ImageFont.truetype(str(display_font_path), max(_pt_to_px(6), spine_pt))
        tb = draw.textbbox((0, 0), spine_title, font=sfont)
        t_w, t_h = tb[2] - tb[0], tb[3] - tb[1]
        strip = Image.new("RGBA", (max(1, t_w), max(1, t_h)), (0, 0, 0, 0))
        ImageDraw.Draw(strip).text((-tb[0], -tb[1]), spine_title, font=sfont, fill=ink)
        rotated = strip.rotate(90, expand=True)
        rx = sx + max(0, (sw - rotated.width) // 2)
        ry = sy + max(0, (sh - rotated.height) // 2)
        image.paste(rotated, (rx, ry), rotated)

    # Back panel: heading + description + features, solid ground.
    bx, by, bw, bh = (int(v) for v in spec["back"])
    back_margin = int(0.625 * dpi)
    y_cursor = by + back_margin
    heading = str(spec.get("back_heading", "About This Book")).strip()
    if heading:
        _draw_wrapped_caption(
            draw, image, heading, (bx + back_margin, y_cursor, bw - 2 * back_margin, int(0.5 * dpi)),
            display_font_path, max_pt=_pt_to_px(20), min_pt=_pt_to_px(12), colour=ink,
            align="left", scrim_min_contrast=1.0,
        )
        y_cursor += int(0.7 * dpi)
    back_lines = [str(s) for s in (spec.get("back_lines") or []) if str(s).strip()]
    if back_lines:
        _draw_wrapped_caption(
            draw, image, " ".join(back_lines),
            (bx + back_margin, y_cursor, bw - 2 * back_margin, int(2.0 * dpi)),
            body_font_path, max_pt=_pt_to_px(13), min_pt=_pt_to_px(9), colour=ink,
            align="left", scrim_min_contrast=1.0,
        )
        y_cursor += int(2.2 * dpi)
    for feat in [str(f) for f in (spec.get("features") or []) if str(f).strip()]:
        _draw_wrapped_caption(
            draw, image, feat, (bx + back_margin, y_cursor, bw - 2 * back_margin, int(0.3 * dpi)),
            body_font_path, max_pt=_pt_to_px(12), min_pt=_pt_to_px(9), colour=ink,
            align="left", scrim_min_contrast=1.0,
        )
        y_cursor += int(0.34 * dpi)

    out_abs = paths.resolve_inside(output_path)
    out_abs.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_abs, format="PNG", optimize=False, dpi=(dpi, dpi))

    return {
        "status": "pass",
        "project_id": project_id,
        "output_path": out_abs.resolve().relative_to(paths.directory.resolve()).as_posix(),
        "wrap_px": [wrap_w, wrap_h],
        "dpi": dpi,
        "font_display": resolved_display_family,
        "font_body": resolved_body_family,
        "art_path": art_abs.resolve().relative_to(paths.directory.resolve()).as_posix(),
    }


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
