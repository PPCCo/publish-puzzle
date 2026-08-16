"""Deterministic code review of ingested coloring line-art assets.

Network-free, offline. This is the *code* half of coloring line-art review: it
emits structured, evidence-backed findings (rule 08 / rule 09 shape:
``severity, dimension, location, evidence, recommendation, acceptance_test,
status``) about the physical pixels of each ingested coloring page. It does NOT
apply human/agent judgment (originality, age-fit, alt-text quality) and it does
NOT approve — the ``product-coloring-line-art-review`` skill layers agent
judgment on top and queues the interior gate.

Checks per asset (all deterministic):

* ``pure_bw`` — the interior must be pure black/white (rule 22:
  ``colour_interior = false`` for coloring). Luminance values must be a subset of
  ``{0, 255}`` with exactly two present. Anything else is a **blocker** (the
  ``image-gen threshold`` step was skipped or the source had anti-aliasing).
* ``printability_at_trim_dpi`` — the pixel dimensions must match the brief's
  declared ``dimensions`` (trim × dpi). A mismatch prints at the wrong size / DPI:
  **major**.
* ``even_background`` — the dominant luminance must be white (255) covering a
  sane majority of the page; a mostly-black page is not a colorable line drawing:
  **major** if white coverage is implausibly low.
* ``min_line_weight`` (proxy) — the thinnest sustained black horizontal run vs
  the brief's ``min_line_weight_pt × dpi / 72``. A heuristic lower bound; under
  target is a **major** worth a human look, never an approval.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifacts import active_hashes, list_artifacts
from .paths import ProjectPaths
from .util import atomic_write_json, load_json, preserve_report_timestamp, utc_now

_COLORING_PURPOSE = "coloring interior page"

# White-coverage floor below which a "line drawing" is implausible (mostly ink).
_MIN_WHITE_FRACTION = 0.55


def _brief_index(paths: ProjectPaths) -> dict[str, dict[str, Any]]:
    """Map ``visuals/assets/<brief_id>.png`` → its coloring brief.

    Only briefs whose ``purpose`` marks them as coloring interior pages qualify.
    """
    briefs_dir = paths.directory / "visuals" / "briefs"
    index: dict[str, dict[str, Any]] = {}
    if not briefs_dir.is_dir():
        return index
    for path in sorted(briefs_dir.glob("*.json")):
        if path.name.endswith(".attestation.json"):
            continue
        data = load_json(path, {})
        if not isinstance(data, dict) or data.get("purpose") != _COLORING_PURPOSE:
            continue
        brief_id = data.get("brief_id")
        if brief_id:
            index[f"visuals/assets/{brief_id}.png"] = data
    return index


def _active_coloring_assets(
    root: Path, project_id: str, brief_id: str | None
) -> list[dict[str, Any]]:
    """Active ``illustration`` artifacts whose path maps to a coloring brief."""
    paths = ProjectPaths(root, project_id).require()
    state = load_json(paths.state, {})
    current = active_hashes(state)
    brief_by_path = _brief_index(paths)

    assets: list[dict[str, Any]] = []
    for artifact in list_artifacts(root, project_id):
        if artifact.get("type") != "illustration":
            continue
        if current and artifact.get("sha256") not in current:
            continue
        rel = artifact.get("path")
        brief = brief_by_path.get(rel)
        if brief is None:
            continue
        if brief_id is not None and brief.get("brief_id") != brief_id:
            continue
        assets.append({"artifact": artifact, "brief": brief, "rel": rel})
    assets.sort(key=lambda item: item["brief"].get("page_number") or 0)
    return assets


def _finding(
    severity: str,
    dimension: str,
    location: str,
    evidence: str,
    recommendation: str,
    acceptance_test: str,
    status: str = "open",
) -> dict[str, Any]:
    return {
        "severity": severity,
        "dimension": dimension,
        "location": location,
        "evidence": evidence,
        "recommendation": recommendation,
        "acceptance_test": acceptance_test,
        "status": status,
    }


def _measure(path: Path) -> dict[str, Any]:
    """Deterministic pixel measurements for one asset (Pillow lazy)."""
    from PIL import Image

    with Image.open(path) as source:
        grey = source.convert("L")
        width, height = grey.size
        # bytes() over the L-mode image yields row-major pixel bytes; stable across
        # Pillow versions (avoids the deprecated Image.getdata()).
        pixels = grey.tobytes()

    total = width * height or 1
    histogram: dict[int, int] = {}
    for value in pixels:
        histogram[value] = histogram.get(value, 0) + 1
    values = sorted(histogram)
    white = histogram.get(255, 0)

    # Thinnest sustained black horizontal run across all rows (line-weight proxy).
    min_black_run: int | None = None
    for row in range(height):
        base = row * width
        run = 0
        for col in range(width):
            if pixels[base + col] == 0:
                run += 1
            elif run:
                min_black_run = run if min_black_run is None else min(min_black_run, run)
                run = 0
        if run:
            min_black_run = run if min_black_run is None else min(min_black_run, run)

    return {
        "width_px": width,
        "height_px": height,
        "luminance_values": values,
        "white_fraction": round(white / total, 4),
        "min_black_run_px": min_black_run,
    }


def coloring_review(root: Path, project_id: str, brief_id: str | None = None) -> dict[str, Any]:
    """Run deterministic pixel checks on ingested coloring pages.

    Returns a report with per-asset findings. ``decision`` is ``PASS`` only when
    no blocker/major finding is open; it is evidence, never an approval.
    """
    paths = ProjectPaths(root, project_id).require()
    assets = _active_coloring_assets(root, project_id, brief_id)

    per_asset: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []

    for entry in assets:
        brief = entry["brief"]
        rel = entry["rel"]
        bid = brief.get("brief_id")
        absolute = paths.resolve_inside(rel)
        if not absolute.exists():
            findings.append(
                _finding(
                    "blocker", "asset_present", rel,
                    "Active illustration artifact is registered but the file is missing.",
                    "Re-ingest the produced asset before review.",
                    "The file exists at its registered path.",
                )
            )
            continue

        m = _measure(absolute)
        asset_findings: list[dict[str, Any]] = []

        # pure_bw — blocker.
        pure_bw = set(m["luminance_values"]).issubset({0, 255}) and len(m["luminance_values"]) == 2
        if not pure_bw:
            asset_findings.append(
                _finding(
                    "blocker", "pure_bw", rel,
                    f"luminance values present={m['luminance_values']} (expected exactly {{0, 255}}).",
                    "Run `image-gen threshold` on the asset before ingest so it is pure black/white.",
                    "The asset's luminance values are exactly {0, 255} (two values).",
                )
            )

        # printability_at_trim_dpi — major.
        dims = brief.get("dimensions") or {}
        want_w, want_h = dims.get("width_px"), dims.get("height_px")
        if want_w and want_h and (m["width_px"] != want_w or m["height_px"] != want_h):
            asset_findings.append(
                _finding(
                    "major", "printability_at_trim_dpi", rel,
                    f"asset is {m['width_px']}×{m['height_px']}px; brief requires {want_w}×{want_h}px.",
                    "Regenerate/resample the asset to the brief's trim × dpi dimensions.",
                    "Asset pixel dimensions equal the brief's declared dimensions.",
                )
            )

        # even_background — major if white coverage implausibly low.
        if m["white_fraction"] < _MIN_WHITE_FRACTION:
            asset_findings.append(
                _finding(
                    "major", "even_background", rel,
                    f"white coverage is {m['white_fraction']:.0%}; a colorable line drawing "
                    f"should be predominantly white (≥{_MIN_WHITE_FRACTION:.0%}).",
                    "Ensure the page is open line-art on a white ground, not filled/inverted.",
                    f"White pixel fraction ≥ {_MIN_WHITE_FRACTION:.0%}.",
                )
            )

        # min_line_weight proxy — major if under target.
        min_line_pt = None
        attestation_path = paths.directory / "visuals" / "briefs" / f"{bid}.attestation.json"
        if attestation_path.is_file():
            min_line_pt = load_json(attestation_path, {}).get("min_line_weight_pt")
        dpi = dims.get("dpi") or 300
        if min_line_pt and m["min_black_run_px"] is not None:
            target_px = float(min_line_pt) * float(dpi) / 72.0
            if m["min_black_run_px"] < target_px:
                asset_findings.append(
                    _finding(
                        "major", "min_line_weight", rel,
                        f"thinnest black run ≈ {m['min_black_run_px']}px; target ≈ "
                        f"{target_px:.0f}px ({min_line_pt}pt @ {dpi}dpi). Proxy heuristic.",
                        "Increase minimum stroke weight so the thinnest line meets the brief.",
                        f"Thinnest sustained black run ≥ ~{target_px:.0f}px (human confirms legibility).",
                    )
                )

        per_asset.append(
            {
                "brief_id": bid,
                "asset_path": rel,
                "page_number": brief.get("page_number"),
                "measurements": m,
                "pure_bw": pure_bw,
                "findings": asset_findings,
            }
        )
        findings.extend(asset_findings)

    blockers = [f for f in findings if f["severity"] == "blocker"]
    majors = [f for f in findings if f["severity"] == "major"]
    if not assets:
        decision = "NONE"
    else:
        decision = "PASS" if not blockers and not majors else "FAIL"

    result = {
        "schema_version": "1.0",
        "project_id": project_id,
        "evaluated_at": utc_now(),
        "decision": decision,
        "asset_count": len(assets),
        "assets": per_asset,
        "findings": findings,
        "open_blockers": len(blockers),
        "open_majors": len(majors),
        "note": (
            "Deterministic code checks only. Originality (rule 07), age-fit (rule 06), "
            "and alt-text quality are agent judgment layered by the review skill. This "
            "report is evidence for the interior gate, never an approval."
        ),
    }

    out = paths.directory / "reviews" / "coloring-review-latest.json"
    preserve_report_timestamp(out, result)
    atomic_write_json(out, result)
    return result
