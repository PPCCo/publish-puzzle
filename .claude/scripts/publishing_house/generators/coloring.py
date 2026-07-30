"""Coloring-family generators + validators.

Two kinds here:

* ``dot-to-dot`` --- fully code-derivable: a numbered sequence of points whose
  connect order reveals a shape. The validator re-checks that numbering is a
  contiguous 1..N sequence and that points are in bounds.
* ``line-art-brief`` --- coloring books ship ORIGINAL art only. Code cannot draw
  publishable art, so this generator emits a structured, self-contained ORIGINAL
  brief (subject, composition, line-weight, complexity band) that an illustration
  agent must realise as an original asset, plus an explicit originality
  attestation the rights gate later checks. It never references, traces, or
  derives from a third-party or IP-protected image. The validator enforces that
  the brief carries the originality attestation and no prohibited-source fields.
"""
from __future__ import annotations

import math
import random
from typing import Any

from .base import ContentType, GeneratedItem, ValidationResult, registry

_SUBJECTS = [
    "a curled sleeping cat", "a blooming sunflower", "a hot-air balloon over hills",
    "a friendly garden snail", "a stack of teacups", "a paper sailboat",
    "a potted succulent", "a slice of watermelon", "a smiling crescent moon",
]
_COMPLEXITY = {
    "easy": {"band": "bold-and-easy", "min_line_pt": 3.0, "regions": "8-15"},
    "medium": {"band": "standard", "min_line_pt": 2.0, "regions": "15-30"},
    "hard": {"band": "detailed", "min_line_pt": 1.2, "regions": "30-60"},
    "expert": {"band": "intricate", "min_line_pt": 0.8, "regions": "60+"},
    "mixed": {"band": "standard", "min_line_pt": 2.0, "regions": "15-30"},
}


def generate_dot_to_dot(seed: int, difficulty: str, index: int, params: dict[str, Any]) -> GeneratedItem:
    rng = random.Random(seed)
    count = {"easy": 12, "medium": 20, "hard": 32, "expert": 48, "mixed": 20}.get(difficulty, 20)
    # Points on a jittered circle so connecting 1..N yields a clean closed shape.
    radius = 0.4
    points = []
    for i in range(count):
        angle = (2 * math.pi * i) / count
        jitter = rng.uniform(-0.03, 0.03)
        x = 0.5 + (radius + jitter) * math.cos(angle)
        y = 0.5 + (radius + jitter) * math.sin(angle)
        points.append({"n": i + 1, "x": round(x, 4), "y": round(y, 4)})
    return GeneratedItem(
        content_type="dot-to-dot",
        index=index,
        difficulty=difficulty,
        seed=seed,
        payload={"points": points, "count": count},
        solution={"order": list(range(1, count + 1))},
        metadata={"coordinate_space": "unit-square"},
    )


def validate_dot_to_dot(item: dict[str, Any]) -> ValidationResult:
    result = ValidationResult(content_type="dot-to-dot", index=int(item.get("index", 0)), passed=True)
    payload = item.get("payload", {})
    points = payload.get("points", [])
    numbers = sorted(p.get("n") for p in points)
    checks = {
        "contiguous_numbering": numbers == list(range(1, len(points) + 1)) and bool(points),
        "in_bounds": all(0.0 <= p.get("x", -1) <= 1.0 and 0.0 <= p.get("y", -1) <= 1.0 for p in points),
        "count_matches": int(payload.get("count", -1)) == len(points),
    }
    result.checks = checks
    result.passed = all(checks.values())
    if not result.passed:
        result.errors = [name for name, ok in checks.items() if not ok]
    return result


def generate_line_art_brief(seed: int, difficulty: str, index: int, params: dict[str, Any]) -> GeneratedItem:
    rng = random.Random(seed)
    subject = str(params.get("subject") or rng.choice(_SUBJECTS))
    spec = _COMPLEXITY.get(difficulty, _COMPLEXITY["mixed"])
    return GeneratedItem(
        content_type="line-art-brief",
        index=index,
        difficulty=difficulty,
        seed=seed,
        payload={
            "subject": subject,
            "complexity_band": spec["band"],
            "min_line_weight_pt": spec["min_line_pt"],
            "target_region_count": spec["regions"],
            "composition": params.get("composition") or "single centred subject, generous margins",
            "style": params.get("style") or "clean closed outlines, no shading fills",
            "originality_attestation": {
                "originals_only": True,
                "no_traced_sources": True,
                "no_third_party_ip": True,
                "statement": (
                    "This brief must be realised as a wholly ORIGINAL illustration. "
                    "Do not trace, copy, or derive from any existing photograph, "
                    "artwork, character, logo, or other third-party or IP-protected "
                    "source. The resulting asset must clear the rights gate as an original."
                ),
            },
        },
        solution=None,
        metadata={"realise_as": "original-line-art", "open_ended": True},
    )


_PROHIBITED_SOURCE_KEYS = {"source_image", "traced_from", "reference_url", "based_on_character", "ip_source"}


def validate_line_art_brief(item: dict[str, Any]) -> ValidationResult:
    result = ValidationResult(content_type="line-art-brief", index=int(item.get("index", 0)), passed=True)
    payload = item.get("payload", {})
    attestation = payload.get("originality_attestation", {})
    checks = {
        "has_subject": bool(str(payload.get("subject", "")).strip()),
        "originals_only": attestation.get("originals_only") is True,
        "no_traced_sources": attestation.get("no_traced_sources") is True,
        "no_third_party_ip": attestation.get("no_third_party_ip") is True,
        "no_prohibited_source_fields": not (_PROHIBITED_SOURCE_KEYS & set(payload)),
        "has_line_weight": float(payload.get("min_line_weight_pt", 0) or 0) > 0,
    }
    result.checks = checks
    result.passed = all(checks.values())
    if not result.passed:
        result.errors = [name for name, ok in checks.items() if not ok]
    return result


registry.register(ContentType("dot-to-dot", "activity", "Dot-to-Dot", generate_dot_to_dot, validate_dot_to_dot))
registry.register(
    ContentType(
        "line-art-brief",
        "coloring",
        "Original Line-Art Brief",
        generate_line_art_brief,
        validate_line_art_brief,
        verifiable=True,
    )
)
