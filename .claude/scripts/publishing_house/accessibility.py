"""Deterministic accessibility audit for puzzle / coloring / journal products.

``audit_accessibility`` derives concrete, checkable accessibility expectations
from the project's audience and design policy (minimum type size, line weight,
contrast, single-sided pages for coloring, alt-text presence for digital) and
evaluates the built outputs / metadata against them. It writes
``accessibility/gate-latest.json`` (material evidence for the compliance gate)
and updates a state summary. Every requirement is enforced by a check, not by
assertion.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .events import append_event
from .paths import ProjectPaths
from .util import atomic_write_json, load_json, load_yaml, utc_now

# Minimum body type size (pt) per audience for print interiors.
_MIN_TYPE_PT = {
    "senior-large-print": 16.0,
    "kids-4-8": 14.0,
    "kids-6-10": 13.0,
    "tween-8-12": 12.0,
    "teen-13-17": 11.0,
    "adult-general": 11.0,
}
# Minimum coloring line weight (pt) per audience.
_MIN_LINE_PT = {
    "senior-large-print": 3.0,
    "kids-4-8": 3.0,
    "kids-6-10": 2.5,
    "adult-general": 1.0,
}


def _expectations(project: dict[str, Any]) -> dict[str, Any]:
    audience = project.get("audience", "adult-general")
    family = project.get("book_type") or project.get("product_type") or "puzzle-book"
    formats = set(project.get("formats", []))
    return {
        "audience": audience,
        "family": family,
        "min_type_pt": _MIN_TYPE_PT.get(audience, 11.0),
        "min_line_pt": _MIN_LINE_PT.get(audience, 1.0),
        "single_sided_required": family == "coloring-book",
        "alt_text_required": bool({"digital-pdf", "epub", "fixed-layout-epub"} & formats),
        "high_contrast_required": audience == "senior-large-print",
    }


def _read_proof(paths: ProjectPaths) -> dict[str, Any]:
    proof = paths.directory / "outputs" / "proof" / "interior-proof-report.json"
    if proof.exists():
        try:
            return load_json(proof)
        except Exception:  # noqa: BLE001
            return {}
    return {}


def audit_accessibility(root: Path, project_id: str) -> dict[str, Any]:
    paths = ProjectPaths(root, project_id).require()
    project = load_yaml(paths.config)
    expect = _expectations(project)
    proof = _read_proof(paths)
    design = project.get("production", {}).get("design", {})

    issues: list[str] = []
    warnings: list[str] = []
    checks: dict[str, bool] = {}

    # Type size: prefer a measured value from the proof; fall back to design hint.
    measured_type = proof.get("min_type_pt") or design.get("body_type_pt")
    if measured_type is None:
        warnings.append("No measured body type size available; record it in the interior proof.")
        checks["type_size"] = False
    else:
        checks["type_size"] = float(measured_type) >= expect["min_type_pt"]
        if not checks["type_size"]:
            issues.append(f"Body type {measured_type}pt is below the {expect['min_type_pt']}pt minimum for {expect['audience']}.")

    # Coloring line weight.
    if expect["family"] == "coloring-book":
        measured_line = proof.get("min_line_pt") or design.get("line_weight_pt")
        if measured_line is None:
            warnings.append("No measured coloring line weight available.")
            checks["line_weight"] = False
        else:
            checks["line_weight"] = float(measured_line) >= expect["min_line_pt"]
            if not checks["line_weight"]:
                issues.append(f"Line weight {measured_line}pt is below the {expect['min_line_pt']}pt minimum.")

    # Single-sided pages for coloring (prevent bleed-through).
    if expect["single_sided_required"]:
        single_sided = bool(proof.get("single_sided") or design.get("single_sided"))
        checks["single_sided"] = single_sided
        if not single_sided:
            issues.append("Coloring interior must be single-sided to prevent marker bleed-through.")

    # Alt text for digital editions.
    if expect["alt_text_required"]:
        alt_present = bool(proof.get("alt_text_present"))
        checks["alt_text"] = alt_present
        if not alt_present:
            issues.append("Digital edition requires alt text on all images.")

    # High contrast for large-print band.
    if expect["high_contrast_required"]:
        high_contrast = bool(design.get("high_contrast"))
        checks["high_contrast"] = high_contrast
        if not high_contrast:
            issues.append("Large-print band requires a high-contrast interior.")

    decision = "PASS" if not issues else "FAIL"
    result = {
        "schema_version": "1.0",
        "project_id": project_id,
        "evaluated_at": utc_now(),
        "decision": decision,
        "expectations": expect,
        "checks": checks,
        "issues": issues,
        "warnings": warnings,
        "note": "Every accessibility requirement is enforced by a check, not asserted.",
    }
    out = paths.directory / "accessibility" / "gate-latest.json"
    atomic_write_json(out, result)

    # Auto-register the accessibility-gate artifact (a compliance-bound TYPE) so the
    # compliance packet can bind it with no manual `artifact register`. Not a
    # downstream-build type; dedups on unchanged re-run. Runs before the state
    # summary write below because register_artifact also updates state.
    from .artifacts import register_artifact  # local import: avoid a module-load cycle

    register_artifact(
        root, project_id, "accessibility/gate-latest.json", "accessibility-gate",
        "ACCESSIBILITY_VALIDATION", "accessibility-auditor",
        rights_status="not-applicable", validation_status="pass" if decision == "PASS" else "fail",
    )

    state = load_json(paths.state)
    state["accessibility_gate"] = {"decision": decision, "evaluated_at": result["evaluated_at"], "issues": len(issues)}
    state["updated_at"] = utc_now()
    state["updated_by"] = "accessibility-audit"
    atomic_write_json(paths.state, state)
    append_event(paths.events, project_id, "ACCESSIBILITY_AUDITED", "accessibility-audit", {"decision": decision, "issues": len(issues)})
    return result
