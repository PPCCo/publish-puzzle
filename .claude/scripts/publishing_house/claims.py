"""Deterministic truthful-claims audit.

``audit_claims`` reconciles the human-facing CLAIM STRINGS a buyer will see
(metadata title/description, listing-kit copy, and the cover callout/descriptor
recomputed exactly as ``layout.build_cover`` derives them) against the VERIFIED
facts of the product: the independently-verified item count and decision, the
audience band, the answer-key placement, and per-item solution uniqueness.

It is the durable promotion of the "cover builder hardcoded 100 Puzzles / Large
Print" learning: instead of trusting any string, a claim is only accurate when it
matches a fact the framework has verified by code. Mirrors ``metadata_audit`` —
it writes ``metadata/claims-report.json`` (schema-validated) and mutates NO
workflow state.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .paths import ProjectPaths
from .util import atomic_write_json, load_json, load_yaml, utc_now
from .validation import validate_data

_LARGE_PRINT_BAND = "senior-large-print"
_LARGE_PRINT_RE = re.compile(r"large[\s-]*print", re.IGNORECASE)
_COUNT_RE = re.compile(r"(\d+)\s+puzzles", re.IGNORECASE)
_BACK_ONLY_RE = re.compile(r"(back[\s-]*(of[\s-]*the[\s-]*book|only)|solutions?\s+at\s+the\s+back|complete\s+solutions)", re.IGNORECASE)
_UNIQUE_RE = re.compile(r"(unique|one\s+solution|single\s+solution|no\s+guessing)", re.IGNORECASE)
_DIFFICULTY_WORDS = ("easy", "medium", "hard", "expert")


def _resolved_band(project: dict[str, Any]) -> str:
    """Recompute the audience band exactly as layout.build_cover does."""
    design = project.get("production", {}).get("design", {}) or {}
    return str(
        (design.get("reading_level_target", {}) or {}).get("band")
        or project.get("audience", "")
    )


def _verified_facts(paths: ProjectPaths, project: dict[str, Any]) -> dict[str, Any]:
    band = _resolved_band(project)
    facts: dict[str, Any] = {
        "item_count": None,
        "content_verification_decision": None,
        "audience_band": band or None,
        "is_large_print": band == _LARGE_PRINT_BAND,
        "solutions_placement": None,
        "all_unique_solutions": None,
        "difficulty_tier": None,
    }

    verification_path = paths.directory / "verification" / "content-verification-latest.json"
    if verification_path.is_file():
        try:
            report = load_json(verification_path)
            facts["item_count"] = report.get("item_count")
            facts["content_verification_decision"] = report.get("decision")
            batches = report.get("batches", []) or []
            unique_flags: list[bool] = []
            for batch in batches:
                for item in batch.get("item_checks", []) or []:
                    checks = item.get("checks", {}) if isinstance(item, dict) else {}
                    if "unique_solution" in checks:
                        unique_flags.append(bool(checks["unique_solution"]))
            if unique_flags:
                facts["all_unique_solutions"] = all(unique_flags)
        except Exception:  # noqa: BLE001
            pass

    # Answer-key placement + difficulty tier from the page map when present.
    page_map = paths.directory / "outputs" / "interior" / "page-map.json"
    if page_map.is_file():
        try:
            pm = load_json(page_map)
            placement = pm.get("solutions_placement") or pm.get("answer_key_placement")
            if placement:
                facts["solutions_placement"] = str(placement)
        except Exception:  # noqa: BLE001
            pass

    # Difficulty tier from the content plan (single-tier products declare one).
    content_plan = project.get("content_plan", {}) or {}
    tier = content_plan.get("difficulty") or content_plan.get("difficulty_tier")
    if isinstance(tier, str):
        facts["difficulty_tier"] = tier.lower()
    return facts


def _cover_claim_strings(project: dict[str, Any], facts: dict[str, Any]) -> dict[str, Any]:
    """Recompute the cover callout + descriptor exactly as layout.build_cover does."""
    content_plan = project.get("content_plan", {}) or {}
    puzzle_count = int(content_plan.get("target_content_count", 0) or 0)
    is_large_print = facts["is_large_print"]
    count_label = f"{puzzle_count} Puzzles" if puzzle_count > 0 else "Puzzles"
    descriptor_parts = (["Large Print"] if is_large_print else []) + ["Easy", "Complete Solutions"]
    return {
        "count_label": count_label,
        "declared_count": puzzle_count,
        "descriptor": "  •  ".join(descriptor_parts),
        "descriptor_parts": descriptor_parts,
    }


def _gather_claim_text(paths: ProjectPaths) -> dict[str, str]:
    """Collect the buyer-facing text blocks that carry claims."""
    texts: dict[str, str] = {}
    book_path = paths.directory / "metadata" / "book.json"
    if book_path.is_file():
        try:
            book = load_json(book_path)
            texts["metadata"] = " ".join(
                str(book.get(k, "")) for k in ("title", "subtitle", "description", "short_description")
            )
        except Exception:  # noqa: BLE001
            pass
    kit_path = paths.directory / "marketing" / "listing-kit.json"
    if kit_path.is_file():
        try:
            kit = load_json(kit_path)
            texts["listing_kit"] = " ".join(
                str(kit.get(k, "")) for k in ("title", "subtitle", "description")
            ) + " " + " ".join(str(b) for b in (kit.get("bullets") or []))
        except Exception:  # noqa: BLE001
            pass
    return texts


def audit_claims(root: Path, project_id: str) -> dict[str, Any]:
    paths = ProjectPaths(root, project_id).require()
    project = load_yaml(paths.config)
    facts = _verified_facts(paths, project)
    cover = _cover_claim_strings(project, facts)
    claim_texts = _gather_claim_text(paths)

    issues: list[str] = []
    warnings: list[str] = []
    checks: dict[str, bool] = {}

    combined = " ".join(claim_texts.values())

    # count-matches: any "<n> puzzles" in buyer text, and the cover count, must
    # equal the verified item count.
    verified_count = facts["item_count"]
    if verified_count is None:
        warnings.append("No verified item count available (run content verification); count claims not checked.")
        checks["count_matches"] = True
    else:
        claimed_counts = {int(m) for m in _COUNT_RE.findall(combined)}
        if cover["declared_count"] > 0:
            claimed_counts.add(cover["declared_count"])
        mismatched = sorted(c for c in claimed_counts if c != int(verified_count))
        checks["count_matches"] = not mismatched
        if mismatched:
            issues.append(
                f"Claimed puzzle count(s) {mismatched} do not match the verified item count {verified_count} "
                "(metadata/listing/cover)."
            )

    # large-print-valid: a "large print" claim is only accurate for the
    # senior-large-print band.
    claims_large_print = bool(_LARGE_PRINT_RE.search(combined)) or ("Large Print" in cover["descriptor_parts"])
    if claims_large_print and not facts["is_large_print"]:
        checks["large_print_valid"] = False
        issues.append(
            f"'Large Print' is claimed but the resolved audience band is "
            f"{facts['audience_band']!r}, not {_LARGE_PRINT_BAND}."
        )
    else:
        checks["large_print_valid"] = True

    # uniqueness-valid: a "unique / no guessing" claim requires verified unique
    # solutions (when uniqueness was measured).
    if _UNIQUE_RE.search(combined):
        if facts["all_unique_solutions"] is False:
            checks["uniqueness_valid"] = False
            issues.append("A 'unique solution / no guessing' claim is made, but not every item has a verified unique solution.")
        elif facts["all_unique_solutions"] is None:
            checks["uniqueness_valid"] = True
            warnings.append("A uniqueness claim is made but solution uniqueness was not measured; verify before release.")
        else:
            checks["uniqueness_valid"] = True
    else:
        checks["uniqueness_valid"] = True

    # back-only-valid: a "solutions at the back / complete solutions" claim
    # requires a back-only placement when the placement is known.
    if _BACK_ONLY_RE.search(combined):
        placement = facts["solutions_placement"]
        if placement is not None and "back" not in placement.lower():
            checks["back_only_valid"] = False
            issues.append(f"Copy implies back-of-book solutions, but the recorded placement is {placement!r}.")
        else:
            checks["back_only_valid"] = True
            if placement is None:
                warnings.append("A back-of-book solutions claim is made but no answer-key placement is recorded.")
    else:
        checks["back_only_valid"] = True

    # difficulty-word-valid: a difficulty word on the cover/copy must match the
    # declared single-tier difficulty when one exists.
    tier = facts["difficulty_tier"]
    if tier in _DIFFICULTY_WORDS:
        other_words = [w for w in _DIFFICULTY_WORDS if w != tier]
        wrong = sorted(w for w in other_words if re.search(rf"\b{w}\b", combined, re.IGNORECASE))
        # The cover descriptor hardcodes "Easy"; flag it when the tier is not easy.
        if "Easy" in cover["descriptor_parts"] and tier != "easy":
            wrong = sorted(set(wrong) | {"easy"})
        checks["difficulty_word_valid"] = not wrong
        if wrong:
            issues.append(f"Difficulty word(s) {wrong} claimed, but the declared difficulty tier is {tier!r}.")
    else:
        checks["difficulty_word_valid"] = True

    decision = "PASS" if not issues else "FAIL"
    result = {
        "schema_version": "1.0",
        "project_id": project_id,
        "evaluated_at": utc_now(),
        "decision": decision,
        "verified_facts": facts,
        "claim_sources": {"cover": cover, "text_blocks": sorted(claim_texts.keys())},
        "checks": checks,
        "issues": issues,
        "warnings": warnings,
    }
    errors = validate_data(root, result, "claims-report.schema.json")
    if errors:
        raise ValueError("claims report failed schema validation: " + "; ".join(errors))
    atomic_write_json(paths.directory / "metadata" / "claims-report.json", result)
    return result
