"""Digital-printable generators + structural validators.

Digital printables (Etsy/Gumroad) are template-driven: printable wall-art specs,
planner inserts, and gift-tag sheets. These are structurally verifiable (correct
page geometry, printable margins, non-overlapping cut grid) rather than having a
hidden solution.
"""
from __future__ import annotations

import random
from typing import Any

from .base import ContentType, GeneratedItem, ValidationResult, registry

# Common US/A-series printable trim sizes in inches.
_PAGE_SIZES = {
    "us-letter": (8.5, 11.0),
    "a4": (8.27, 11.69),
    "5x7": (5.0, 7.0),
    "8x10": (8.0, 10.0),
}
_QUOTES = [
    "Bloom where you are planted",
    "Today is a good day for a good day",
    "Small steps, big dreams",
    "Stay wild, moon child",
    "Coffee first, then the world",
]


def generate_printable(seed: int, difficulty: str, index: int, params: dict[str, Any]) -> GeneratedItem:
    rng = random.Random(seed)
    size_key = str(params.get("page_size") or "us-letter")
    width, height = _PAGE_SIZES.get(size_key, _PAGE_SIZES["us-letter"])
    margin = float(params.get("margin_in") or 0.25)
    quote = str(params.get("text") or rng.choice(_QUOTES))
    return GeneratedItem(
        content_type="printable",
        index=index,
        difficulty=difficulty,
        seed=seed,
        payload={
            "kind": params.get("kind") or "wall-art",
            "page_size": size_key,
            "width_in": width,
            "height_in": height,
            "margin_in": margin,
            "printable_area_in": [round(width - 2 * margin, 3), round(height - 2 * margin, 3)],
            "text": quote,
            "dpi": int(params.get("dpi") or 300),
        },
        solution=None,
        metadata={"open_ended": True, "commercial_license_required": True},
    )


def validate_printable(item: dict[str, Any]) -> ValidationResult:
    result = ValidationResult(content_type="printable", index=int(item.get("index", 0)), passed=True)
    payload = item.get("payload", {})
    width = float(payload.get("width_in", 0))
    height = float(payload.get("height_in", 0))
    margin = float(payload.get("margin_in", 0))
    dpi = int(payload.get("dpi", 0))
    area = payload.get("printable_area_in", [0, 0])
    checks = {
        "positive_page": width > 0 and height > 0,
        "margins_leave_area": margin > 0 and (2 * margin) < min(width, height),
        "area_correct": area == [round(width - 2 * margin, 3), round(height - 2 * margin, 3)],
        "print_dpi_ok": dpi >= 300,
    }
    result.checks = checks
    result.passed = all(checks.values())
    if not result.passed:
        result.errors = [name for name, ok in checks.items() if not ok]
    return result


registry.register(ContentType("printable", "printable", "Digital Printable", generate_printable, validate_printable))
