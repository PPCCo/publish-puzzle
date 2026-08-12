from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .errors import ValidationFailure
from .events import append_event, read_events
from .paths import PROJECT_DIRS, ProjectPaths
from .util import (
    atomic_write_json,
    atomic_write_yaml,
    load_company_config,
    load_json,
    load_yaml,
    parse_csv,
    slugify,
    utc_now,
)
from .validation import validate_file


def generate_project_id(topic: str) -> str:
    year = datetime.now(UTC).year
    return f"clr-{year}-{slugify(topic, 48)}"


# Audience bands treated as "young reader" for colour policy.
YOUNG_READER_BANDS = frozenset(
    {"kids-4-8", "kids-6-10", "tween-8-12", "teen-13-17"}
)


def default_colour_policy(audience: str) -> dict[str, Any]:
    """Return the default per-audience colour policy for a new project.

    For puzzle / coloring / journal / printable products, print-interior colour
    is the dominant COGS driver on KDP (a colour interior can be several times
    the print cost of black-and-white). The default therefore leans toward
    black-and-white interiors for puzzle/journal products and low-ink line art
    for coloring products, RAISED to colour only where a product family or
    audience genuinely needs it (see .claude/rules/19-colour-policy.md).

    This is the single source of truth for the audience colour default. The
    design-policy engine (publishing_house.design_policy) reuses this function
    verbatim and may RAISE the interior to colour for a colour-carrying
    ``book_type`` (product family); it never duplicates the derivation. The
    ``colour_interior_default`` boolean is preserved for compatibility with
    ``production.colour_interior``. See .claude/rules/20-design-policy.md.
    """
    # Digital editions are always full colour (no marginal print cost).
    digital = {"text": "colour", "images": "colour"}
    global_page_rule = (
        "Whenever a print page carries a colour image, the entire page is a "
        "colour page for costing; keep colour pages contiguous to avoid "
        "per-signature colour surcharges."
    )
    if audience in {"kids-4-8", "kids-6-10"}:
        # Youngest activity/coloring audiences: colour interior expected.
        print_interior = {"text": "colour", "images": "colour"}
        colour_interior = True
        notes = f"{audience}: full colour interior expected for young activity/coloring products."
    elif audience == "tween-8-12":
        # Colour on image-bearing pages; puzzle grids stay black-and-white.
        print_interior = {"text": "black-and-white", "images": "colour-on-image-pages"}
        colour_interior = False
        notes = (
            "tween-8-12: puzzle grids and text black-and-white; colour only on "
            "dedicated image/coloring pages if the product family needs it."
        )
    elif audience in {"teen-13-17", "adult-general"}:
        # Adult puzzle/journal: black-and-white interior is the norm.
        print_interior = {"text": "black-and-white", "images": "black-and-white"}
        colour_interior = False
        notes = (
            f"{audience}: black-and-white interior is standard for puzzle/journal "
            "products; colour only where a product family requires it."
        )
    elif audience == "senior-large-print":
        # Large-print accessibility band: high-contrast black-and-white.
        print_interior = {"text": "black-and-white-high-contrast", "images": "black-and-white"}
        colour_interior = False
        notes = (
            "senior-large-print: high-contrast black-and-white interior for "
            "legibility; large grids/type; colour avoided to preserve contrast."
        )
    else:
        # Unspecified bands: conservative black-and-white default.
        print_interior = {"text": "black-and-white", "images": "by-image-type"}
        colour_interior = False
        notes = "other/unspecified: conservative black-and-white default; project may override."
    return {
        "colour_interior_default": colour_interior,
        "digital": digital,
        "print_interior": print_interior,
        "image_colour_rule": (
            "Interior colour is used only when it carries meaning or the product "
            "family requires it (young coloring, colour-by-number). Puzzle grids, "
            "solutions, and journal pages default to black-and-white to control "
            "print cost."
        ),
        "global_page_rule": global_page_rule,
        "notes": notes,
    }


def init_project(
    root: Path,
    topic: str,
    audience: str = "adult-general",
    book_type: str = "puzzle-book",
    formats: list[str] | str | None = None,
    project_id: str | None = None,
    language: str = "en-US",
    working_title: str | None = None,
    created_by: str = "human",
    product_type: str | None = None,
) -> dict[str, Any]:
    """Create a new puzzle / coloring / journal / printable product project.

    ``book_type`` here names the PRODUCT FAMILY (puzzle-book, coloring-book,
    guided-journal, digital-printable) so the shared design-policy engine and
    schemas carry over from bk-pub unchanged. ``product_type`` is a convenience
    alias for the same value; when omitted it defaults to ``book_type``.
    """
    product_type = product_type or book_type
    project_id = slugify(project_id or generate_project_id(topic), 80)
    paths = ProjectPaths(root, project_id)
    if paths.directory.exists():
        raise ValidationFailure(f"Project already exists: {project_id}")
    # Default to a print paperback: the dominant format for KDP puzzle/activity
    # and coloring products. Digital-printable projects pass --formats digital-pdf.
    formats_list = parse_csv(formats) or ["paperback"]
    # Derive craft parameters from audience x product family x age band. Experts /
    # rules decide craft; humans do not pick these per product. See
    # .claude/rules/20-design-policy.md. Colour is single-sourced from
    # default_colour_policy (reused by the engine), keeping colour_interior and
    # colour_policy consistent with production.design.
    from .design_policy import derive_design

    design = derive_design(root, audience, book_type, formats_list)
    # Copy the company-wide legal/rights posture into the project so the human
    # confirms only *deltas* at the compliance and release gates rather than
    # re-collecting disclosure/rights/safety values ad hoc. These are DEFAULTS,
    # not clearances: default_asset_rights_status stays "unknown-blocks-release",
    # preserving the rule that clearance is never inferred from missing evidence
    # (.claude/rules/12-rights.md). Deep-copy via JSON round-trip so later project
    # edits never alias the shared company config; offline and deterministic.
    company = load_company_config(root)
    legal_defaults = json.loads(json.dumps(company.get("legal_defaults", {})))
    project = {
        "schema_version": "1.0",
        "project_id": project_id,
        "working_title": working_title or topic,
        "topic": topic,
        "book_type": book_type,
        "product_type": product_type,
        "genre": "",
        "audience": audience,
        "language": language,
        "formats": formats_list,
        "sales_channels": ["kdp", "etsy"],
        "edition": 1,
        "created_at": utc_now(),
        "created_by": created_by,
        "objectives": [],
        "constraints": [],
        "content_plan": {
            # Content mix is decided during PLANNING; empty at init so the
            # niche/planning stage can populate puzzle types + counts.
            "puzzle_types": [],
            "target_content_count": None,
            "difficulty_progression": design.get("pedagogy_approach") or "eased",
            "solutions_placement": "back-only",
        },
        "production": {
            "trim_size": design.get("trim_size") or "8.5x11",
            "bleed": False,
            "colour_interior": design["colour_interior"],
            "colour_policy": design["colour_policy"],
            "design": design,
            "print": {
                "paper": design.get("paper_hint") or "white",
                "binding": design.get("binding_hint") or "paperback",
                "spine_width_in": None,
            },
            # Company legal/rights defaults, copied at init. The owner MAY edit
            # these per project; the compliance and release gates read them as the
            # pre-filled decision so the human confirms only deltas.
            "legal_defaults": legal_defaults,
        },
        "commercial": {"currency": "USD", "ebook_price": None, "paperback_price": None, "hardcover_price": None, "digital_price": None},
        "rights": {"territories": ["WORLD"], "ai_assistance_disclosure_required": "unknown", "originals_only": True},
        "status_notes": "",
    }
    project_errors = validate_file_data(root, project, "project.schema.json")
    if project_errors:
        raise ValidationFailure("Invalid project configuration: " + "; ".join(project_errors))

    for directory in PROJECT_DIRS:
        (paths.directory / directory).mkdir(parents=True, exist_ok=True)
    atomic_write_yaml(paths.config, project)
    state = {
        "schema_version": "1.0",
        "project_id": project_id,
        "current_state": "DISCOVERY",
        "previous_state": None,
        "revision_cycle": 0,
        "targeted_repairs": {},
        "active_artifacts": {},
        "required_reviews": [],
        "completed_reviews": [],
        "blocked_reasons": [],
        "quality_gate": None,
        "rights_gate": None,
        "invalidated_approvals": [],
        "updated_at": utc_now(),
        "updated_by": created_by,
    }
    atomic_write_json(paths.state, state)
    atomic_write_json(paths.artifact_manifest, {"schema_version": "1.0", "project_id": project_id, "artifacts": []})
    atomic_write_json(paths.rights_ledger, {"schema_version": "1.0", "project_id": project_id, "records": []})
    atomic_write_json(paths.reviews_index, {"schema_version": "1.0", "project_id": project_id, "reviews": []})
    paths.events.touch()
    append_event(paths.events, project_id, "PROJECT_CREATED", created_by, {"topic": topic, "audience": audience, "book_type": book_type, "product_type": product_type, "formats": formats_list})
    sync_catalog(root)
    return {"project": project, "state": state, "path": paths.directory.as_posix()}


def validate_file_data(root: Path, data: Any, schema_name: str) -> list[str]:
    from .validation import validate_data
    return validate_data(root, data, schema_name)


def list_projects(root: Path) -> list[dict[str, Any]]:
    projects_dir = root / "projects"
    output: list[dict[str, Any]] = []
    if not projects_dir.exists():
        return output
    for config in sorted(projects_dir.glob("*/project.yaml")):
        try:
            project = load_yaml(config)
            state = load_json(config.parent / "state.json")
            output.append({
                "project_id": project["project_id"],
                "working_title": project["working_title"],
                "product_type": project.get("product_type") or project.get("book_type"),
                "audience": project.get("audience"),
                "edition": project["edition"],
                "state": state["current_state"],
                "formats": project["formats"],
                "updated_at": state["updated_at"],
            })
        except Exception as exc:  # noqa: BLE001
            output.append({"project_id": config.parent.name, "state": "ERROR", "error": str(exc)})
    return output


def validate_project(root: Path, project_id: str) -> dict[str, Any]:
    paths = ProjectPaths(root, project_id).require()
    errors: list[str] = []
    warnings: list[str] = []
    for path, schema in [(paths.config, "project.schema.json"), (paths.state, "state.schema.json"), (paths.artifact_manifest, None), (paths.rights_ledger, None)]:
        if not path.exists():
            errors.append(f"Missing required file: {path.relative_to(paths.directory)}")
        elif schema:
            errors.extend(f"{path.name}: {x}" for x in validate_file(root, path, schema))
    project = load_yaml(paths.config)
    state = load_json(paths.state)
    if project.get("project_id") != project_id or state.get("project_id") != project_id:
        errors.append("Project ID differs between directory/config/state")
    workflow = load_json(root / ".claude" / "config" / "workflow_states.json")
    if state.get("current_state") not in workflow.get("states", []):
        errors.append(f"Unknown workflow state: {state.get('current_state')}")
    manifest = load_json(paths.artifact_manifest, {"artifacts": []})
    known_hashes = {item.get("sha256") for item in manifest.get("artifacts", [])}
    for kind, digest in state.get("active_artifacts", {}).items():
        if digest not in known_hashes:
            errors.append(f"Active artifact hash for {kind} is not registered: {digest}")
    for item in manifest.get("artifacts", []):
        artifact_path = paths.directory / item.get("path", "")
        if not artifact_path.exists():
            warnings.append(f"Registered artifact missing from disk: {item.get('path')}")
    return {"project_id": project_id, "status": "pass" if not errors else "fail", "errors": errors, "warnings": warnings}


def project_status(root: Path, project_id: str) -> dict[str, Any]:
    from .approvals import list_approvals
    from .artifacts import list_artifacts
    from .state import next_actions

    paths = ProjectPaths(root, project_id).require()
    project = load_yaml(paths.config)
    state = load_json(paths.state)
    reviews = sorted(paths.directory.glob("reviews/**/*.json"))
    open_findings = {"blocker": 0, "major": 0, "minor": 0, "note": 0}
    for path in reviews:
        if path.name in {"index.json", "quality-gate-latest.json"}:
            continue
        try:
            data = load_json(path)
        except Exception:  # noqa: BLE001
            continue
        for finding in data.get("findings", []):
            if finding.get("status") not in {"closed", "rejected-with-rationale"}:
                severity = finding.get("severity", "note")
                if severity in open_findings:
                    open_findings[severity] += 1
    return {
        "project": project,
        "state": state,
        "active_artifacts": state.get("active_artifacts", {}),
        "artifact_count": len(list_artifacts(root, project_id)),
        "approvals": list_approvals(root, project_id),
        "open_findings": open_findings,
        "recent_events": read_events(paths.events, limit=10),
        "next_actions": next_actions(root, project_id)["actions"],
        "validation": validate_project(root, project_id),
    }


def sync_catalog(root: Path) -> dict[str, Any]:
    catalog = {"schema_version": "1.0", "products": list_projects(root)}
    atomic_write_json(root / "catalog" / "products.json", catalog)
    return catalog
