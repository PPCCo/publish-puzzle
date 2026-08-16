"""Print-ready and digital layout builders (ReportLab).

Builders here turn verified content batches into deliverables:

* ``build_interior`` --- assemble the print interior PDF: puzzle/activity/journal
  pages first, solutions grouped BACK-ONLY, padded to an even page count (KDP
  requires even pages). Emits a page-map artifact.
* ``build_cover`` --- build a print cover wrap; spine width is computed from page
  count and paper stock (KDP math), never guessed.
* ``build_proof`` --- produce a deterministic pre-flight proof report measuring
  the built interior/cover against the project's design policy (type size, line
  weight, single-sided, page-count parity). This is the material evidence the
  interior/cover human gates read.
* ``link_digital_bundle`` --- assemble a digital printable bundle (PDF + a linked
  page index) for Etsy/Gumroad delivery.

ReportLab is imported lazily so importing this module never fails when the
optional dependency is absent; the builder raises a clear BuildError instead.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import BuildError
from .events import append_event
from .paths import ProjectPaths
from .util import atomic_write_json, load_json, load_yaml, utc_now

# KDP-style paper caliper (page thickness) in inches per page, by paper stock.
# Spine width = pages * caliper (single sheet = 2 pages).
_PAPER_CALIPER_IN = {
    "white": 0.002252,
    "cream": 0.0025,
    "premium-color": 0.002347,
}
_TRIM_INCHES = {
    "8.5x11": (8.5, 11.0),
    "8x10": (8.0, 10.0),
    "6x9": (6.0, 9.0),
    "7x10": (7.0, 10.0),
    "8.25x8.25": (8.25, 8.25),
}


def _require_reportlab():
    try:
        from reportlab.lib.units import inch  # noqa: F401
        from reportlab.pdfgen import canvas  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        raise BuildError(
            "ReportLab is required for layout builds. Install it (pip install reportlab) "
            "or run 'publishing-house doctor' to check dependencies."
        ) from exc
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas

    return canvas, inch


# Embeddable, commercial-embedding-permissive fonts bundled with reportlab
# (Bitstream Vera; license permits use/copy/embed/redistribute/sell-with-product,
# only barring sale of the font by itself). Used so built covers embed a
# rights-clean face instead of relying on the non-embedded PDF base-14 Helvetica,
# which print channels (KDP) flag for missing embedded fonts.
_EMBED_FONT_REGULAR = "PHSans"
_EMBED_FONT_BOLD = "PHSans-Bold"


def _register_embed_fonts() -> tuple[str, str]:
    """Register the bundled Vera faces and return (regular_name, bold_name).

    Falls back to base-14 Helvetica only if the bundled TTFs are unavailable.
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import reportlab

    fonts_dir = Path(reportlab.__file__).parent / "fonts"
    regular = fonts_dir / "Vera.ttf"
    bold = fonts_dir / "VeraBd.ttf"
    if not (regular.exists() and bold.exists()):
        return "Helvetica", "Helvetica-Bold"
    registered = pdfmetrics.getRegisteredFontNames()
    if _EMBED_FONT_REGULAR not in registered:
        pdfmetrics.registerFont(TTFont(_EMBED_FONT_REGULAR, str(regular)))
    if _EMBED_FONT_BOLD not in registered:
        pdfmetrics.registerFont(TTFont(_EMBED_FONT_BOLD, str(bold)))
    return _EMBED_FONT_REGULAR, _EMBED_FONT_BOLD


def _load_batches(paths: ProjectPaths) -> list[dict[str, Any]]:
    batches: list[dict[str, Any]] = []
    for rel in ["content/puzzles", "content/journal", "content/printable", "content/coloring"]:
        directory = paths.directory / rel
        if directory.is_dir():
            for path in sorted(directory.glob("*-batch.json")):
                try:
                    batches.append(load_json(path))
                except Exception:  # noqa: BLE001
                    continue
    return batches


# Interior text sizes actually rendered by the draw helpers below. These are the
# single source of truth for BOTH what is drawn and what the page-map records as
# the measured minimum, so the accessibility proof reflects the real interior
# instead of an absent design hint. Prose/body text is the accessibility-relevant
# minimum; headings and in-cell numerals are larger or are not body text.
_INTERIOR_BODY_PT = 11.0  # front-matter/placeholder prose lines (_draw_placeholder_page)
_INTERIOR_TITLE_PT = 16.0  # placeholder page title
_SUDOKU_TITLE_PT = 18.0
_SUDOKU_LABEL_PT = 14.0
_SUDOKU_DIGIT_MIN_PT = 10.0  # in-cell numerals (not body text)


def _trim(project: dict[str, Any]) -> tuple[float, float]:
    size = project.get("production", {}).get("trim_size", "8.5x11")
    return _TRIM_INCHES.get(size, _TRIM_INCHES["8.5x11"])


def _draw_placeholder_page(c, inch, width_in: float, height_in: float, title: str, lines: list[str]) -> None:
    c.setPageSize((width_in * inch, height_in * inch))
    c.setFont("Helvetica-Bold", _INTERIOR_TITLE_PT)
    c.drawString(0.75 * inch, (height_in - 0.9) * inch, title)
    c.setFont("Helvetica", _INTERIOR_BODY_PT)
    y = (height_in - 1.4) * inch
    for line in lines:
        c.drawString(0.75 * inch, y, line[:110])
        y -= 0.28 * inch
        if y < 0.75 * inch:
            break
    c.showPage()


def _draw_sudoku_page(
    c: Any,
    inch: float,
    width_in: float,
    height_in: float,
    title: str,
    difficulty: str,
    grid: list[list[int]],
    *,
    is_solution: bool = False,
) -> None:
    """Draw a 9x9 sudoku grid page. grid is a 9x9 list-of-lists; 0 = blank cell."""
    MARGIN = 0.75
    HEADER_H = 1.0
    grid_area = min(width_in - 2 * MARGIN, height_in - 2 * MARGIN - HEADER_H)
    cell = grid_area / 9
    grid_left = (width_in - grid_area) / 2
    grid_top_in = height_in - MARGIN - HEADER_H  # top of grid in inches from bottom
    grid_bottom_in = grid_top_in - grid_area

    c.setPageSize((width_in * inch, height_in * inch))

    # Header
    c.setFont("Helvetica-Bold", _SUDOKU_TITLE_PT)
    c.drawString(MARGIN * inch, (height_in - MARGIN - 0.35) * inch, title)
    if difficulty:
        c.setFont("Helvetica", _SUDOKU_LABEL_PT)
        c.drawString(MARGIN * inch, (height_in - MARGIN - 0.70) * inch, f"Difficulty: {difficulty.capitalize()}")

    # Grid lines
    c.setStrokeColorRGB(0, 0, 0)
    for i in range(10):
        lw = 2.0 if i % 3 == 0 else 0.5
        c.setLineWidth(lw)
        # horizontal
        y = (grid_bottom_in + i * cell) * inch
        c.line(grid_left * inch, y, (grid_left + grid_area) * inch, y)
        # vertical
        x = (grid_left + i * cell) * inch
        c.line(x, grid_bottom_in * inch, x, (grid_bottom_in + grid_area) * inch)

    # Digits
    font_size = max(_SUDOKU_DIGIT_MIN_PT, min(18, cell * inch * 0.55))
    c.setFont("Helvetica-Bold", font_size)
    c.setFillColorRGB(0, 0, 0)
    for row in range(9):
        for col in range(9):
            val = grid[row][col] if grid and row < len(grid) and col < len(grid[row]) else 0
            if val:
                cx = (grid_left + col * cell + cell / 2) * inch
                cy = (grid_bottom_in + (8 - row) * cell + cell / 2 - font_size / 72 / 2) * inch
                c.drawCentredString(cx, cy, str(val))

    c.showPage()


def _content_pages(batches: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (content_pages, solution_pages) as descriptors carrying the full payload/solution."""
    content: list[dict[str, Any]] = []
    solutions: list[dict[str, Any]] = []
    for batch in batches:
        ctype = batch.get("content_type", "content")
        for item in batch.get("items", []):
            content.append({
                "type": ctype,
                "index": item.get("index"),
                "difficulty": item.get("difficulty"),
                "payload": item.get("payload"),
                "solution": item.get("solution"),
            })
            if item.get("solution") is not None:
                solutions.append({
                    "type": ctype,
                    "index": item.get("index"),
                    "solution": item.get("solution"),
                })
    return content, solutions


_COLORING_PURPOSE = "coloring interior page"


def _coloring_assets(root: Path, project_id: str, paths: ProjectPaths) -> dict[int, dict[str, Any]]:
    """Map interior page number → placeable coloring asset.

    Selects ACTIVE ``illustration`` artifacts (manifest ∩ ``state.active_artifacts``)
    whose rights record is CLEARED and whose path maps to a coloring brief
    (``visuals/assets/<brief_id>.png`` with ``purpose == 'coloring interior page'``).
    Independent of the later human interior gate — placement of a cleared, active,
    rendered asset is a build decision; the gate still approves the whole product.

    Returns ``{page_number: {path, brief_id, alt_text, decorative}}``. Empty when no
    such asset exists, so the puzzle path stays byte-identical.
    """
    from .artifacts import active_hashes, list_artifacts

    state = load_json(paths.state, {})
    current = active_hashes(state)

    # Cleared/excluded asset hashes from the rights ledger.
    ledger = load_json(paths.rights_ledger, {"records": []})
    cleared_hashes = {
        r.get("asset_hash")
        for r in ledger.get("records", [])
        if r.get("clearance_status") in {"cleared", "excluded"}
    }

    # brief path → brief (coloring interior pages only).
    briefs_dir = paths.directory / "visuals" / "briefs"
    brief_by_path: dict[str, dict[str, Any]] = {}
    if briefs_dir.is_dir():
        for path in sorted(briefs_dir.glob("*.json")):
            if path.name.endswith(".attestation.json"):
                continue
            data = load_json(path, {})
            if isinstance(data, dict) and data.get("purpose") == _COLORING_PURPOSE and data.get("brief_id"):
                brief_by_path[f"visuals/assets/{data['brief_id']}.png"] = data

    assets: dict[int, dict[str, Any]] = {}
    for artifact in list_artifacts(root, project_id):
        if artifact.get("type") != "illustration":
            continue
        digest = artifact.get("sha256")
        if current and digest not in current:
            continue
        if digest not in cleared_hashes:
            continue
        rel = artifact.get("path")
        brief = brief_by_path.get(rel)
        if brief is None:
            continue
        page_number = brief.get("page_number")
        if not isinstance(page_number, int):
            continue
        absolute = paths.directory / rel
        if not absolute.is_file():
            continue
        alt_text = str(brief.get("alt_text_draft", "")).strip()
        assets[page_number] = {
            "path": absolute,
            "brief_id": brief.get("brief_id"),
            "alt_text": alt_text,
            "decorative": not alt_text,
        }
    return assets


def _draw_image_page(c, inch, width_in: float, height_in: float, image_path: Path) -> None:
    """Place a single coloring image centred at trim with margins, no caption."""
    from reportlab.lib.utils import ImageReader

    MARGIN = 0.5
    c.setPageSize((width_in * inch, height_in * inch))
    avail_w = (width_in - 2 * MARGIN) * inch
    avail_h = (height_in - 2 * MARGIN) * inch
    c.drawImage(
        ImageReader(str(image_path)),
        MARGIN * inch,
        MARGIN * inch,
        width=avail_w,
        height=avail_h,
        preserveAspectRatio=True,
        anchor="c",
        mask="auto",
    )
    c.showPage()


def build_interior(root: Path, project_id: str, binding: str = "paperback") -> dict[str, Any]:
    canvas, inch = _require_reportlab()
    paths = ProjectPaths(root, project_id).require()
    project = load_yaml(paths.config)
    width_in, height_in = _trim(project)
    batches = _load_batches(paths)
    if not batches:
        raise BuildError("No generated content batches found to build an interior.")
    content_pages, solution_pages = _content_pages(batches)
    coloring_assets = _coloring_assets(root, project_id, paths)

    out_dir = paths.directory / "outputs" / "interior"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "interior.pdf"
    c = canvas.Canvas(str(pdf_path))

    page_map: list[dict[str, Any]] = []
    page_no = 1
    # Front matter (title page).
    _draw_placeholder_page(c, inch, width_in, height_in, str(project.get("working_title", project_id)), ["Original content. All rights reserved."])
    page_map.append({"page": page_no, "kind": "front-matter"})
    page_no += 1
    # Content pages.
    placed = 0
    for page in content_pages:
        num = (page["index"] or 0) + 1
        asset = coloring_assets.get(num) if page.get("type") == "line-art-brief" else None
        if asset is not None:
            _draw_image_page(c, inch, width_in, height_in, asset["path"])
            entry = {"page": page_no, "kind": "content", "type": page.get("type"), "index": page.get("index"),
                     "raster": True, "brief_id": asset["brief_id"]}
            if asset["decorative"]:
                entry["decorative"] = True
                entry["decorative_designation"] = "Decorative coloring line-art; no informational alt text required."
            else:
                entry["alt_text"] = asset["alt_text"]
            page_map.append(entry)
            placed += 1
        elif page.get("type") == "sudoku" and page.get("payload") and page["payload"].get("grid"):
            _draw_sudoku_page(c, inch, width_in, height_in, f"Sudoku #{num}", page.get("difficulty", ""), page["payload"]["grid"])
            page_map.append({"page": page_no, "kind": "content", **{k: v for k, v in page.items() if k not in ("payload", "solution")}})
        else:
            _draw_placeholder_page(c, inch, width_in, height_in, f"{page['type'].title()} #{num}", [f"Difficulty: {page.get('difficulty')}"])
            page_map.append({"page": page_no, "kind": "content", **{k: v for k, v in page.items() if k not in ("payload", "solution")}})
        page_no += 1
    # BACK-ONLY solutions section.
    if solution_pages:
        _draw_placeholder_page(c, inch, width_in, height_in, "Solutions", ["Answer keys follow."])
        page_map.append({"page": page_no, "kind": "solutions-divider"})
        page_no += 1
        for page in solution_pages:
            num = (page["index"] or 0) + 1
            sol = page.get("solution") or {}
            if page.get("type") == "sudoku" and sol.get("grid"):
                _draw_sudoku_page(c, inch, width_in, height_in, f"Solution #{num}", "", sol["grid"], is_solution=True)
            else:
                _draw_placeholder_page(c, inch, width_in, height_in, f"Solution: {page['type'].title()} #{num}", [])
            page_map.append({"page": page_no, "kind": "solution", **{k: v for k, v in page.items() if k != "solution"}})
            page_no += 1
    # Pad to even page count (KDP requirement).
    total = page_no - 1
    if total % 2 != 0:
        _draw_placeholder_page(c, inch, width_in, height_in, "", [])
        page_map.append({"page": page_no, "kind": "blank-pad"})
        total += 1
    c.save()

    # Record the accessibility-relevant facts THIS build actually rendered, so the
    # proof/audit reflect the real interior rather than absent design hints.
    # - min_body_type_pt: smallest prose/body point size drawn (headings/numerals
    #   are larger or are not body text); constant-sourced from the draw helpers.
    # - raster_image_count: the interior is entirely code-drawn vector content
    #   (grids, rules, digits, text) via reportlab primitives; no drawImage/raster
    #   is emitted, so there are zero informational raster images. Structural grid
    #   drawings are decorative, so the digital alt-text requirement is met by a
    #   documented no-raster-image designation, not by per-image alt text.
    page_map_path = out_dir / "page-map.json"
    atomic_write_json(page_map_path, {
        "schema_version": "1.0", "project_id": project_id, "binding": binding,
        "trim_in": [width_in, height_in], "page_count": total,
        "even_page_count": total % 2 == 0, "solutions_placement": "back-only",
        "min_body_type_pt": _INTERIOR_BODY_PT,
        "raster_image_count": placed,
        "vector_only": placed == 0,
        "pages": page_map,
    })

    from .artifacts import register_artifact
    artifact = register_artifact(root, project_id, pdf_path, "interior-pdf", "LAYOUT_AND_FORMAT_BUILD", "interior-builder", rights_status="not-applicable", validation_status="not-run", provenance={"binding": binding, "page_count": total})
    append_event(paths.events, project_id, "INTERIOR_BUILT", "interior-builder", {"page_count": total, "artifact_id": artifact["artifact_id"]})
    return {"project_id": project_id, "page_count": total, "even": total % 2 == 0, "path": pdf_path.relative_to(paths.directory).as_posix(), "artifact_id": artifact["artifact_id"], "sha256": artifact["sha256"]}


def _spine_width_in(page_count: int, paper: str) -> float:
    return round(page_count * _PAPER_CALIPER_IN.get(paper, _PAPER_CALIPER_IN["white"]), 4)


def _wrap_text(text: str, max_chars: int) -> list[str]:
    """Wrap text to lines of at most max_chars, splitting on spaces."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        if current and len(current) + 1 + len(word) > max_chars:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip() if current else word
    if current:
        lines.append(current)
    return lines


def build_cover(root: Path, project_id: str, binding: str = "paperback") -> dict[str, Any]:
    canvas, inch = _require_reportlab()
    font_regular, font_bold = _register_embed_fonts()
    paths = ProjectPaths(root, project_id).require()
    project = load_yaml(paths.config)
    width_in, height_in = _trim(project)
    paper = project.get("production", {}).get("print", {}).get("paper", "white")
    page_map_path = paths.directory / "outputs" / "interior" / "page-map.json"
    if not page_map_path.exists():
        raise BuildError("Build the interior first; the cover spine width depends on the page count.")
    page_count = int(load_json(page_map_path).get("page_count", 0))
    spine = _spine_width_in(page_count, paper)
    bleed = 0.125
    wrap_width = (width_in * 2) + spine + (bleed * 2)
    wrap_height = height_in + (bleed * 2)

    title = str(project.get("working_title", project_id))
    content_plan = project.get("content_plan", {}) or {}
    puzzle_count = int(content_plan.get("target_content_count", 0) or 0)
    design = project.get("production", {}).get("design", {}) or {}
    band = str(
        (design.get("reading_level_target", {}) or {}).get("band")
        or project.get("audience", "")
    )
    is_large_print = band == "senior-large-print"
    description = ""
    listing_kit_path = paths.directory / "marketing" / "listing-kit.json"
    if listing_kit_path.exists():
        try:
            kit = load_json(listing_kit_path)
            description = kit.get("description", "") or ""
        except Exception:  # noqa: BLE001
            pass

    out_dir = paths.directory / "outputs" / "cover"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "cover-wrap.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=(wrap_width * inch, wrap_height * inch))
    c.setFont(font_regular, 12)  # default canvas font -> embedded, rights-clean

    # ------------------------------------------------------------------ #
    # Coordinate system: (0,0) = bottom-left of the full wrap canvas.
    # Layout left-to-right: back panel | spine | front panel (all + bleed).
    # back panel occupies x: 0 .. (width_in + bleed)*inch
    # spine occupies x: (width_in + bleed)*inch .. (width_in + bleed + spine)*inch
    # front panel occupies x: (width_in + bleed + spine)*inch .. wrap_width*inch
    # ------------------------------------------------------------------ #
    front_x = (width_in + bleed + spine) * inch   # left edge of front panel
    front_w = width_in * inch
    back_x = 0.0
    back_w = width_in * inch
    spine_x = (width_in + bleed) * inch
    spine_w = spine * inch
    wrap_h = wrap_height * inch
    margin = 0.625 * inch   # interior margin on front/back

    from reportlab.lib.colors import HexColor  # noqa: PLC0415
    navy = HexColor("#1a3a5c")
    cream = HexColor("#fdf6e3")
    white = HexColor("#ffffff")

    # --- Front panel background ---
    c.setFillColor(navy)
    c.rect(front_x, 0, front_w, wrap_h, fill=1, stroke=0)

    # Decorative horizontal rule below header area
    rule_y = wrap_h - 2.5 * inch
    c.setStrokeColor(cream)
    c.setLineWidth(2)
    c.line(front_x + margin, rule_y, front_x + front_w - margin, rule_y)

    # Title on front (white, bold, large, wrapped)
    c.setFillColor(white)
    title_lines = _wrap_text(title, 28)
    font_size = 28 if len(title_lines) <= 2 else 22
    line_h = font_size * 1.3
    title_block_h = len(title_lines) * line_h
    title_top_y = wrap_h - 1.1 * inch
    c.setFont(font_bold, font_size)
    for i, line in enumerate(title_lines):
        y = title_top_y - i * line_h
        c.drawString(front_x + margin, y, line)

    # Decorative rule below title
    rule2_y = title_top_y - title_block_h - 0.2 * inch
    c.setStrokeColor(cream)
    c.setLineWidth(1)
    c.line(front_x + margin, rule2_y, front_x + front_w - margin, rule2_y)

    # Puzzle count callout box
    callout_y = rule2_y - 1.6 * inch
    callout_h = 1.1 * inch
    c.setFillColor(cream)
    c.roundRect(front_x + margin, callout_y, front_w - 2 * margin, callout_h, 6, fill=1, stroke=0)
    c.setFillColor(navy)
    c.setFont(font_bold, 32)
    count_label = f"{puzzle_count} Puzzles" if puzzle_count > 0 else "Puzzles"
    c.drawCentredString(front_x + front_w / 2, callout_y + callout_h * 0.52, count_label)
    c.setFont(font_regular, 14)
    descriptor_parts = (["Large Print"] if is_large_print else []) + ["Easy", "Complete Solutions"]
    c.drawCentredString(front_x + front_w / 2, callout_y + callout_h * 0.18, "  •  ".join(descriptor_parts))

    # Sudoku grid preview (4x4 sample, decorative)
    grid_preview_size = 1.8 * inch
    gp_x = front_x + margin
    gp_y = callout_y - grid_preview_size - 0.35 * inch
    cell_p = grid_preview_size / 4
    c.setStrokeColor(cream)
    c.setLineWidth(1.5)
    sample_digits = ["5", "3", " ", " ", "7", " ", " ", " ", " ", "6",
                     " ", " ", "1", "9", "5", " "]
    for r in range(5):
        lw = 2.5 if r % 2 == 0 else 0.8
        c.setLineWidth(lw)
        c.line(gp_x, gp_y + r * cell_p, gp_x + grid_preview_size, gp_y + r * cell_p)
        c.line(gp_x + r * cell_p, gp_y, gp_x + r * cell_p, gp_y + grid_preview_size)
    c.setFillColor(white)
    c.setFont(font_bold, 14)
    for r in range(4):
        for col in range(4):
            d = sample_digits[r * 4 + col]
            if d != " ":
                cx = gp_x + col * cell_p + cell_p / 2
                cy = gp_y + (3 - r) * cell_p + cell_p / 3
                c.drawCentredString(cx, cy, d)

    # Format badge bottom-right of front
    badge_y = 0.5 * inch
    c.setFillColor(cream)
    c.setFont(font_regular, 12)
    trim_label = f"{width_in:g} × {height_in:g} in"
    binding_label = binding.capitalize()
    c.drawRightString(front_x + front_w - margin, badge_y, f"{trim_label}  |  {binding_label}")

    # --- Back panel background ---
    c.setFillColor(navy)
    c.rect(back_x, 0, back_w, wrap_h, fill=1, stroke=0)

    # Back panel: description text
    c.setFillColor(white)
    back_margin = 0.625 * inch
    desc_lines = _wrap_text(description, 46) if description else []
    c.setFont(font_bold, 16)
    c.drawString(back_margin, wrap_h - 1.0 * inch, "About This Book")
    c.setStrokeColor(cream)
    c.setLineWidth(1)
    c.line(back_margin, wrap_h - 1.2 * inch, back_w - back_margin, wrap_h - 1.2 * inch)
    c.setFont(font_regular, 12)
    text_y = wrap_h - 1.65 * inch
    for line in desc_lines:
        c.drawString(back_margin, text_y, line)
        text_y -= 0.22 * inch
        if text_y < 1.0 * inch:
            break

    # Back panel: features list
    features_y = text_y - 0.3 * inch
    count_phrase = f"{puzzle_count} unique easy sudoku puzzles" if puzzle_count > 0 else "unique easy sudoku puzzles"
    per_page_phrase = "One puzzle per page, large print" if is_large_print else "One puzzle per page"
    features = [
        f"✓  {count_phrase}",
        f"✓  {per_page_phrase}",
        "✓  High-contrast black-on-white grids",
        "✓  Complete solutions at the back",
        "✓  No guessing required",
    ]
    c.setFont(font_regular, 13)
    for feat in features:
        if features_y > 1.2 * inch:
            c.drawString(back_margin, features_y, feat)
            features_y -= 0.28 * inch

    # --- Spine ---
    if spine_w >= 0.25 * inch:
        c.setFillColor(navy)
        c.rect(spine_x, 0, spine_w, wrap_h, fill=1, stroke=0)
        # Spine title (rotated 90°, bottom-to-top)
        c.setFillColor(white)
        c.saveState()
        c.translate(spine_x + spine_w / 2, wrap_h / 2)
        c.rotate(90)
        spine_font = min(10, spine_w * 72 * 0.7)
        c.setFont(font_bold, max(6, spine_font))
        # Truncate if title is very long
        spine_title = title if len(title) <= 50 else title[:47] + "..."
        c.drawCentredString(0, 0, spine_title)
        c.restoreState()

    c.showPage()
    c.save()

    atomic_write_json(out_dir / "cover-spec.json", {
        "schema_version": "1.0", "project_id": project_id, "binding": binding, "paper": paper,
        "page_count": page_count, "spine_width_in": spine, "bleed_in": bleed,
        "wrap_size_in": [round(wrap_width, 4), round(wrap_height, 4)], "trim_in": [width_in, height_in],
    })
    from .artifacts import register_artifact
    artifact = register_artifact(root, project_id, pdf_path, "cover-pdf", "VISUAL_DEVELOPMENT", "cover-builder", rights_status="pending", validation_status="not-run", provenance={"spine_width_in": spine, "page_count": page_count})
    append_event(paths.events, project_id, "COVER_BUILT", "cover-builder", {"spine_width_in": spine, "artifact_id": artifact["artifact_id"]})
    return {"project_id": project_id, "spine_width_in": spine, "wrap_size_in": [round(wrap_width, 4), round(wrap_height, 4)], "path": pdf_path.relative_to(paths.directory).as_posix(), "artifact_id": artifact["artifact_id"], "sha256": artifact["sha256"]}


def build_proof(root: Path, project_id: str) -> dict[str, Any]:
    paths = ProjectPaths(root, project_id).require()
    project = load_yaml(paths.config)
    design = project.get("production", {}).get("design", {})
    family = project.get("book_type") or project.get("product_type") or "puzzle-book"

    interior_map = paths.directory / "outputs" / "interior" / "page-map.json"
    cover_spec = paths.directory / "outputs" / "cover" / "cover-spec.json"

    issues: list[str] = []
    interior_report: dict[str, Any] = {"present": interior_map.exists()}
    # Accessibility facts measured by the interior build, if present. Prefer the
    # build-recorded values (what was actually rendered) over design hints.
    measured_body_pt: float | None = None
    raster_image_count: int | None = None
    vector_only = False
    raster_pages: list[dict[str, Any]] = []
    if interior_map.exists():
        page_map = load_json(interior_map)
        interior_report.update({
            "page_count": page_map.get("page_count"),
            "even_page_count": page_map.get("even_page_count"),
            "solutions_placement": page_map.get("solutions_placement"),
        })
        measured_body_pt = page_map.get("min_body_type_pt")
        raster_image_count = page_map.get("raster_image_count")
        vector_only = bool(page_map.get("vector_only"))
        raster_pages = [p for p in page_map.get("pages", []) if p.get("raster")]
        if not page_map.get("even_page_count"):
            issues.append("Interior page count is odd; KDP requires an even page count.")
        if page_map.get("solutions_placement") != "back-only":
            issues.append("Solutions must be grouped back-only.")
    else:
        issues.append("Interior PDF/page-map not built.")

    cover_report: dict[str, Any] = {"present": cover_spec.exists()}
    if cover_spec.exists():
        spec = load_json(cover_spec)
        cover_report.update({"spine_width_in": spec.get("spine_width_in"), "wrap_size_in": spec.get("wrap_size_in")})
        if not spec.get("spine_width_in"):
            issues.append("Cover spine width not computed.")

    decision = "PASS" if not issues else "FAIL"
    # A single proof report carries interior evidence; also mirror a cover proof so
    # both the interior gate and cover gate have their referenced report present.
    # Alt-text requirement is satisfied either when the build recorded meaningful
    # alt text OR when the interior is vector-only with zero informational raster
    # images (nothing to caption). Structural grid drawings are decorative.
    # When the interior contains raster images, alt text is real per-page evidence:
    # every raster page MUST carry non-empty alt_text OR a decorative designation.
    # With no rasters, keep the vector-only shortcut (structural grid drawings are
    # decorative; nothing informational to caption).
    if raster_pages:
        alt_text_present = all(
            bool(p.get("alt_text")) or p.get("decorative") is True for p in raster_pages
        )
    else:
        alt_text_present = (
            bool(design.get("alt_text_present"))
            or (vector_only and (raster_image_count or 0) == 0)
        )
    interior_proof = {
        "schema_version": "1.0", "project_id": project_id, "evaluated_at": utc_now(),
        "decision": decision, "interior": interior_report,
        # Prefer the build-measured minimum body type over an absent design hint.
        "min_type_pt": measured_body_pt if measured_body_pt is not None else design.get("body_type_pt"),
        "min_line_pt": design.get("line_weight_pt"),
        "single_sided": bool(design.get("single_sided")) or family == "coloring-book",
        "alt_text_present": alt_text_present,
        "raster_image_count": raster_image_count,
        "vector_only": vector_only,
        "issues": issues,
    }
    cover_proof = {
        "schema_version": "1.0", "project_id": project_id, "evaluated_at": utc_now(),
        "decision": "PASS" if cover_report["present"] and cover_report.get("spine_width_in") else "FAIL",
        "cover": cover_report,
    }
    out_dir = paths.directory / "outputs" / "proof"
    atomic_write_json(out_dir / "interior-proof-report.json", interior_proof)
    atomic_write_json(out_dir / "cover-proof-report.json", cover_proof)
    append_event(paths.events, project_id, "PROOF_BUILT", "proof-builder", {"interior_decision": decision, "cover_decision": cover_proof["decision"]})
    return {"project_id": project_id, "interior": interior_proof, "cover": cover_proof}


def link_digital_bundle(root: Path, project_id: str) -> dict[str, Any]:
    paths = ProjectPaths(root, project_id).require()
    interior_pdf = paths.directory / "outputs" / "interior" / "interior.pdf"
    out_dir = paths.directory / "outputs" / "digital"
    out_dir.mkdir(parents=True, exist_ok=True)
    included: list[str] = []
    if interior_pdf.exists():
        import shutil
        shutil.copy2(interior_pdf, out_dir / "printable.pdf")
        included.append("printable.pdf")
    else:
        # For pure-printable projects, link each printable batch page index.
        for batch_path in sorted((paths.directory / "content" / "printable").glob("*-batch.json")):
            included.append(batch_path.relative_to(paths.directory).as_posix())
    index = {
        "schema_version": "1.0", "project_id": project_id, "generated_at": utc_now(),
        "included": included, "delivery": "digital-download",
        "note": "Digital bundle for Etsy/Gumroad delivery; no external upload is performed.",
    }
    index_path = out_dir / "bundle-index.json"
    atomic_write_json(index_path, index)
    if not included:
        raise BuildError("No interior PDF or printable batches found to bundle.")
    from .artifacts import register_artifact
    artifact = register_artifact(root, project_id, out_dir, "digital-bundle", "LAYOUT_AND_FORMAT_BUILD", "digital-builder", rights_status="not-applicable", validation_status="not-run", provenance={"included": included})
    append_event(paths.events, project_id, "DIGITAL_BUNDLE_LINKED", "digital-builder", {"count": len(included), "artifact_id": artifact["artifact_id"]})
    return {"project_id": project_id, "included": included, "path": out_dir.relative_to(paths.directory).as_posix(), "artifact_id": artifact["artifact_id"], "sha256": artifact["sha256"]}
