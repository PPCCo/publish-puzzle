from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .paths import ProjectPaths
from .util import atomic_write_json, load_json, utc_now
from .validation import validate_data


def review_files(paths: ProjectPaths) -> list[Path]:
    return [
        path for path in sorted((paths.directory / "reviews").rglob("*.json"))
        if path.name not in {"index.json", "quality-gate-latest.json"}
    ]


def evaluate_quality(root: Path, project_id: str, stage: str = "current") -> dict[str, Any]:
    paths = ProjectPaths(root, project_id).require()
    config = load_json(root / ".claude" / "config" / "quality_gates.json")
    threshold = config["default_final_gate"]
    state = load_json(paths.state)
    current_hashes = set(state.get("active_artifacts", {}).values())
    counts = {"blocker": 0, "major": 0, "minor": 0, "note": 0}
    score_values: dict[str, list[float]] = defaultdict(list)
    accepted_reviews: list[str] = []
    stale_reviews: list[str] = []
    invalid_reviews: list[dict[str, Any]] = []

    for path in review_files(paths):
        try:
            review = load_json(path)
        except Exception as exc:  # noqa: BLE001
            invalid_reviews.append({"path": path.relative_to(paths.directory).as_posix(), "errors": [str(exc)]})
            continue
        if "review_id" not in review:
            continue
        errors = validate_data(root, review, "review.schema.json")
        if errors:
            invalid_reviews.append({"path": path.relative_to(paths.directory).as_posix(), "errors": errors})
            continue
        if current_hashes and review.get("artifact_hash") not in current_hashes:
            stale_reviews.append(path.relative_to(paths.directory).as_posix())
            continue
        accepted_reviews.append(path.relative_to(paths.directory).as_posix())
        for dimension, score in review.get("scores", {}).items():
            if isinstance(score, (int, float)):
                score_values[dimension].append(float(score))
        for finding in review.get("findings", []):
            if finding.get("status") in {"closed", "rejected-with-rationale"}:
                continue
            severity = finding.get("severity", "note")
            if severity in counts:
                counts[severity] += 1

    scores = {dimension: round(sum(values) / len(values), 3) for dimension, values in score_values.items() if values}
    weighted = round(sum(scores.values()) / len(scores), 3) if scores else 0.0
    reasons: list[str] = []
    decision = "PASS"
    if not accepted_reviews:
        decision = "INCOMPLETE"
        reasons.append("No current, valid reviews were found")
    if invalid_reviews:
        decision = "INCOMPLETE"
        reasons.append(f"{len(invalid_reviews)} review file(s) are invalid")
    if stale_reviews:
        decision = "INCOMPLETE"
        reasons.append(f"{len(stale_reviews)} review file(s) reference stale artifact hashes")
    if counts["blocker"] > threshold["max_open_blockers"]:
        decision = "FAIL"
        reasons.append(f"Open blockers: {counts['blocker']}")
    if counts["major"] > threshold["max_open_majors"]:
        decision = "FAIL"
        reasons.append(f"Open majors: {counts['major']}")
    for dimension, score in scores.items():
        minimum = threshold["critical_dimension_minimum"] if dimension in threshold["critical_dimensions"] else threshold["minimum_dimension_score"]
        if score < minimum:
            decision = "FAIL"
            reasons.append(f"{dimension} score {score} is below {minimum}")
    if scores and weighted < threshold["minimum_weighted_overall"]:
        decision = "FAIL"
        reasons.append(f"Weighted overall {weighted} is below {threshold['minimum_weighted_overall']}")

    final_states = {"FINAL_PROOF", "LISTING_APPROVAL", "PLATFORM_PACKAGING", "RELEASE_AUTHORIZATION", "READY_FOR_SUBMISSION", "SUBMISSION", "PUBLISHED"}
    if stage == "final" or state["current_state"] in final_states:
        required = set(threshold["critical_dimensions"] + ["production_readiness"])
        missing = sorted(required - set(scores))
        if missing:
            decision = "INCOMPLETE"
            reasons.append("Missing final-gate dimensions: " + ", ".join(missing))

    result = {
        "schema_version": "1.0",
        "project_id": project_id,
        "artifact_hashes": sorted(current_hashes),
        "evaluated_at": utc_now(),
        "counts": counts,
        "scores": scores,
        "weighted_overall": weighted,
        "decision": decision,
        "reasons": reasons,
        "source_reviews": accepted_reviews,
        "stale_reviews": stale_reviews,
        "invalid_reviews": invalid_reviews,
    }
    # Schema excludes diagnostic extras; validate the core subset.
    core = {key: result[key] for key in ["schema_version", "project_id", "artifact_hashes", "evaluated_at", "counts", "scores", "weighted_overall", "decision", "reasons", "source_reviews"]}
    errors = validate_data(root, core, "quality-gate.schema.json")
    if errors:
        result["decision"] = "INCOMPLETE"
        result["reasons"].extend(errors)
    atomic_write_json(paths.directory / "reviews" / "quality-gate-latest.json", result)
    state["quality_gate"] = {"decision": result["decision"], "evaluated_at": result["evaluated_at"], "counts": counts, "weighted_overall": weighted}
    state["updated_at"] = utc_now()
    state["updated_by"] = "quality-gate"
    atomic_write_json(paths.state, state)
    return result
