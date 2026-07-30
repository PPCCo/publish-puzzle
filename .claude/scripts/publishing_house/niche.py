"""Deterministic niche / market assessment for a topic + product family.

``assess_niche`` produces a repeatable, evidence-shaped assessment from the
project's own configuration (topic, product family, audience, formats, channels)
plus offline heuristics. It performs NO external network calls --- market signals
a human must supply (live BSR, ad costs, competitor counts) are surfaced as
explicit ``human_inputs_required`` rather than invented. It writes
``niche/assessment-latest.json`` (material evidence for the niche gate) and a
state summary. The decision is advisory (PASS/REVIEW); the human niche gate is
still the authority.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .events import append_event
from .paths import ProjectPaths
from .util import atomic_write_json, load_json, load_yaml, utc_now

# Offline saturation heuristic per product family: how crowded the KDP/Etsy shelf
# generally is. Higher = harder to differentiate. These are conservative priors,
# NOT live data; the human gate revises them with current market evidence.
_FAMILY_SATURATION = {
    "puzzle-book": 0.75,
    "coloring-book": 0.85,
    "guided-journal": 0.65,
    "digital-printable": 0.70,
}
_FAMILY_DIFFERENTIATORS = {
    "puzzle-book": [
        "large-print / accessibility band",
        "themed content set with a narrative hook",
        "verified-unique solutions as a trust signal",
        "difficulty progression tuned to a specific audience",
    ],
    "coloring-book": [
        "original art in an under-served subject",
        "bold-and-easy band for seniors / low-vision",
        "single-sided pages to prevent bleed-through",
        "cohesive collectible series identity",
    ],
    "guided-journal": [
        "specific life-transition framing",
        "structured method (not generic blank lines)",
        "companion prompts + trackers in one system",
    ],
    "digital-printable": [
        "cohesive bundle over single sheet",
        "editable + print-ready formats",
        "clear commercial-use licensing",
    ],
}


def _audience_signal(audience: str) -> dict[str, Any]:
    accessibility_bands = {"senior-large-print", "kids-4-8", "kids-6-10"}
    return {
        "audience": audience,
        "accessibility_sensitive": audience in accessibility_bands,
        "note": (
            "Large-print / high-contrast is a strong differentiator for this band."
            if audience in accessibility_bands
            else "Standard-sight audience; differentiate on content and cohesion."
        ),
    }


def assess_niche(root: Path, project_id: str) -> dict[str, Any]:
    paths = ProjectPaths(root, project_id).require()
    project = load_yaml(paths.config)
    family = project.get("book_type") or project.get("product_type") or "puzzle-book"
    audience = project.get("audience", "adult-general")
    topic = project.get("topic", "")
    channels = project.get("sales_channels", [])

    saturation = _FAMILY_SATURATION.get(family, 0.75)
    differentiators = _FAMILY_DIFFERENTIATORS.get(family, [])
    audience_signal = _audience_signal(audience)

    # A conservative, explainable opportunity score in [0,1]: lower saturation and
    # an accessibility-sensitive audience both raise it. This is a PRIOR, revised
    # by the human gate with live evidence.
    score = round(max(0.0, min(1.0, (1.0 - saturation) + (0.15 if audience_signal["accessibility_sensitive"] else 0.0))), 3)
    decision = "PASS" if score >= 0.25 else "REVIEW"

    human_inputs_required = [
        "Current best-seller rank / demand for the exact sub-niche",
        "Live competitor count and top-listing quality on each target channel",
        "Advertising cost and keyword competition, if paid launch is planned",
        "Confirmation the topic is evergreen vs. trend-dependent",
    ]

    result = {
        "schema_version": "1.0",
        "project_id": project_id,
        "evaluated_at": utc_now(),
        "topic": topic,
        "product_family": family,
        "audience": audience,
        "sales_channels": channels,
        "offline_saturation_prior": saturation,
        "audience_signal": audience_signal,
        "opportunity_score": score,
        "recommended_differentiators": differentiators,
        "human_inputs_required": human_inputs_required,
        "decision": decision,
        "external_data_used": False,
        "note": (
            "Advisory, offline assessment from project config + conservative priors. "
            "No live market data was fetched; the human niche gate is the authority."
        ),
    }
    out = paths.directory / "niche" / "assessment-latest.json"
    atomic_write_json(out, result)

    state = load_json(paths.state)
    state["niche_assessment"] = {"decision": decision, "opportunity_score": score, "evaluated_at": result["evaluated_at"]}
    state["updated_at"] = utc_now()
    state["updated_by"] = "niche-assessor"
    atomic_write_json(paths.state, state)
    append_event(paths.events, project_id, "NICHE_ASSESSED", "niche-assessor", {"decision": decision, "score": score})
    return result
