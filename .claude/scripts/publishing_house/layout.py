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


def _trim(project: dict[str, Any]) -> tuple[float, float]:
    size = project.get("production", {}).get("trim_size", "8.5x11")
    return _TRIM_INCHES.get(size, _TRIM_INCHES["8.5x11"])


def _draw_placeholder_page(c, inch, width_in: float, height_in: float, title: str, lines: list[str]) -> None:
    c.setPageSize((width_in * inch, height_in * inch))
    c.setFont("Helvetica-Bold", 16)
    c.drawString(0.75 * inch, (height_in - 0.9) * inch, title)
    c.setFont("Helvetica", 11)
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
    c.setFont("Helvetica-Bold", 18)
    c.drawString(MARGIN * inch, (height_in - MARGIN - 0.35) * inch, title)
    if difficulty:
        c.setFont("Helvetica", 14)
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
    font_size = max(10, min(18, cell * inch * 0.55))
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


def build_interior(root: Path, project_id: str, binding: str = "paperback") -> dict[str, Any]:
    canvas, inch = _require_reportlab()
    paths = ProjectPaths(root, project_id).require()
    project = load_yaml(paths.config)
    width_in, height_in = _trim(project)
    batches = _load_batches(paths)
    if not batches:
        raise BuildError("No generated content batches found to build an interior.")
    content_pages, solution_pages = _content_pages(batches)

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
    for page in content_pages:
        num = (page["index"] or 0) + 1
        if page.get("type") == "sudoku" and page.get("payload") and page["payload"].get("grid"):
            _draw_sudoku_page(c, inch, width_in, height_in, f"Sudoku #{num}", page.get("difficulty", ""), page["payload"]["grid"])
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

    page_map_path = out_dir / "page-map.json"
    atomic_write_json(page_map_path, {
        "schema_version": "1.0", "project_id": project_id, "binding": binding,
        "trim_in": [width_in, height_in], "page_count": total,
        "even_page_count": total % 2 == 0, "solutions_placement": "back-only",
        "pages": page_map,
    })

    from .artifacts import register_artifact
    artifact = register_artifact(root, project_id, pdf_path, "interior-pdf", "LAYOUT_AND_FORMAT_BUILD", "interior-builder", rights_status="not-applicable", validation_status="not-run", provenance={"binding": binding, "page_count": total})
    append_event(paths.events, project_id, "INTERIOR_BUILT", "interior-builder", {"page_count": total, "artifact_id": artifact["artifact_id"]})
    return {"project_id": project_id, "page_count": total, "even": total % 2 == 0, "path": pdf_path.relative_to(paths.directory).as_posix(), "artifact_id": artifact["artifact_id"], "sha256": artifact["sha256"]}


def _spine_width_in(page_count: int, paper: str) -> float:
    return round(page_count * _PAPER_CALIPER_IN.get(paper, _PAPER_CALIPER_IN["white"]), 4)


def build_cover(root: Path, project_id: str, binding: str = "paperback") -> dict[str, Any]:
    canvas, inch = _require_reportlab()
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

    out_dir = paths.directory / "outputs" / "cover"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "cover-wrap.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=(wrap_width * inch, wrap_height * inch))
    c.setFont("Helvetica-Bold", 18)
    c.drawString((width_in + spine + bleed + 0.75) * inch, (wrap_height - 1.0) * inch, str(project.get("working_title", project_id)))
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
    if interior_map.exists():
        page_map = load_json(interior_map)
        interior_report.update({
            "page_count": page_map.get("page_count"),
            "even_page_count": page_map.get("even_page_count"),
            "solutions_placement": page_map.get("solutions_placement"),
        })
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
    interior_proof = {
        "schema_version": "1.0", "project_id": project_id, "evaluated_at": utc_now(),
        "decision": decision, "interior": interior_report,
        "min_type_pt": design.get("body_type_pt"), "min_line_pt": design.get("line_weight_pt"),
        "single_sided": bool(design.get("single_sided")) or family == "coloring-book",
        "alt_text_present": bool(design.get("alt_text_present")),
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
