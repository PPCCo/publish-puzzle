"""Audience-driven, deterministic design-policy engine.

This module resolves craft parameters (trim size, colour policy, tone register,
reading-level targets, visual density, emotional-intensity ceiling, pedagogy
approach, binding/paper hints) from ``audience`` x ``book_type`` x the numeric
age-band table -- with a recorded ``rationale`` and ``provenance`` for every
resolved field.

Experts (and the config in ``.claude/config/design_policy.json`` +
``.claude/config/age_bands.json``) decide craft; humans do not pick these per
book. See ``.claude/rules/20-design-policy.md``.

The module is pure and deterministic: no network, no state mutation, no clock
reads. Output keys are emitted in a stable order.

Colour derivation is single-sourced. The audience colour default comes from
``default_colour_policy`` in ``project.py`` (reused verbatim, never duplicated).
A colour-carrying ``book_type`` (atlas, picture-book, illustrated-*, encyclopedia,
activity-book) may RAISE the interior to colour on top of that audience default
via the ``colour_interior`` signal in ``book_type_overrides``; a book_type never
lowers colour below the audience default. The resulting ``production.colour_interior``
boolean and ``production.colour_policy`` structure stay backward compatible, with
the source of the final colour decision recorded in provenance.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .util import load_json

CONFIG_RELPATH = (".claude", "config", "design_policy.json")
AGE_BANDS_RELPATH = (".claude", "config", "age_bands.json")
RECORD_SCHEMA = "design-record.schema.json"

# Overridable per-field keys a book_type override may set on top of the
# audience default. Kept explicit so provenance can be recorded per field.
# NOTE: colour is handled separately (see _resolve_colour) because it must
# only ever be RAISED by a book_type, never lowered below the audience default.
_OVERRIDABLE_FIELDS = (
    "trim_size_recommended",
    "trim_size_candidates",
    "tone_register",
    "visual_density",
    "emotional_intensity_ceiling",
    "pedagogy_approach",
    "binding_hint",
    "paper_hint",
)


def load_design_policy(root: Path) -> dict[str, Any]:
    """Load and schema-validate the design-policy CONFIGURATION.

    Validates ``config/design_policy.json`` against the CONFIG schema
    (``design-policy.schema.json``). Raises ``ValueError`` if the config is
    missing or fails its schema. The validation import is local to avoid a
    hard import cycle with modules that themselves import this one.
    """
    config_path = root.joinpath(*CONFIG_RELPATH)
    config = load_json(config_path)
    if config is None:
        raise ValueError(f"Design-policy config not found: {config_path}")

    from .validation import validate_data

    errors = validate_data(root, config, "design-policy.schema.json")
    if errors:
        raise ValueError(
            "Invalid design_policy.json: " + "; ".join(errors)
        )
    return config


def load_age_bands(root: Path) -> dict[str, Any]:
    """Load the numeric age-band table (previously read only by agents)."""
    bands_path = root.joinpath(*AGE_BANDS_RELPATH)
    bands = load_json(bands_path)
    if bands is None:
        raise ValueError(f"Age-band config not found: {bands_path}")
    return bands


def _reading_level_target(root: Path, audience: str) -> dict[str, Any]:
    """Copy the numeric reading-level ranges for ``audience`` from age_bands."""
    bands = load_age_bands(root)
    profile = bands.get("profiles", {}).get(audience)
    if profile is None:
        return {
            "band": audience,
            "resolved": False,
            "note": (
                f"No age-band profile for '{audience}'; reading-level targets "
                "must be set by the audience specialist."
            ),
        }
    # Preserve only the numeric craft ranges (deterministic key subset).
    keys = (
        "age_min",
        "age_max",
        "default_words",
        "sentence_words_target",
        "paragraph_sentences_target",
        "technical_terms_per_1000_words_max",
        "visuals_per_spread_target",
        "visuals_per_chapter_target",
    )
    target: dict[str, Any] = {"band": audience, "resolved": True}
    for key in keys:
        if key in profile:
            target[key] = profile[key]
    if "guidance" in profile:
        target["guidance"] = list(profile["guidance"])
    return target


def _resolve_colour(
    audience: str,
    book_type_override: dict[str, Any],
) -> tuple[dict[str, Any], bool, str]:
    """Resolve the final colour policy for ``audience`` x book_type.

    Returns ``(colour_policy, colour_interior, source)``.

    The audience colour default is single-sourced from
    ``project.default_colour_policy`` (never duplicated). A colour-carrying
    ``book_type`` may RAISE ``colour_interior`` to True (e.g. an atlas is
    colour-carrying regardless of audience) but never lowers it below the
    audience default. When the book_type raises colour, print-interior images
    are set to ``mostly-colour`` and the global page rule applies, while the
    audience-derived text treatment is preserved.
    """
    from .project import default_colour_policy  # local import: avoid cycle

    colour_policy = dict(default_colour_policy(audience))
    audience_default = bool(colour_policy["colour_interior_default"])

    raise_colour = bool(book_type_override.get("colour_interior")) is True and (
        book_type_override.get("colour_interior") is True
    )
    if raise_colour and not audience_default:
        # book_type raises interior to colour; preserve audience text treatment.
        print_interior = dict(colour_policy.get("print_interior", {}))
        print_interior["images"] = "mostly-colour"
        colour_policy = dict(colour_policy)
        colour_policy["print_interior"] = print_interior
        colour_policy["colour_interior_default"] = True
        colour_policy["notes"] = (
            colour_policy.get("notes", "")
            + " Raised to colour interior because the book_type is colour-carrying "
            "(images mostly colour; any page with a colour image is a colour page)."
        ).strip()
        return colour_policy, True, f"book_type:{book_type_override.get('_book_type', 'override')}"

    return colour_policy, audience_default, f"audience:{audience}"


def derive_design(
    root: Path,
    audience: str,
    book_type: str,
    formats: list[str] | None = None,
) -> dict[str, Any]:
    """Resolve the full design record for ``audience`` x ``book_type``.

    Returns a deterministic dict carrying the resolved craft fields, per-field
    ``rationale``/``provenance``, the reused colour policy, the reading-level
    targets copied from the age-band table, and a top-level ``provenance``
    block describing the derivation inputs. No per-book human input.

    Colour is derived from ``audience`` AND ``book_type``: a colour-carrying
    book_type raises the interior to colour on top of the audience default.
    """
    formats = list(formats or [])
    config = load_design_policy(root)

    audience_defaults: dict[str, Any] = config["defaults_by_audience"].get(
        audience, {}
    )
    book_type_override: dict[str, Any] = dict(
        config.get("book_type_overrides", {}).get(book_type, {})
    )
    # Tag the override so _resolve_colour can name the book_type in provenance.
    book_type_override["_book_type"] = book_type

    audience_resolved = bool(audience_defaults)

    # Resolve each overridable field, tracking where its value came from.
    resolved: dict[str, Any] = {}
    field_source: dict[str, str] = {}
    for field in _OVERRIDABLE_FIELDS:
        if field in book_type_override:
            resolved[field] = book_type_override[field]
            field_source[field] = f"book_type:{book_type}"
        elif field in audience_defaults:
            resolved[field] = audience_defaults[field]
            field_source[field] = f"audience:{audience}"
        else:
            field_source[field] = "unresolved"

    # Colour policy: audience default, possibly RAISED by a colour-carrying
    # book_type. Single-sourced from project.default_colour_policy.
    colour_policy, colour_interior, colour_source = _resolve_colour(
        audience, book_type_override
    )
    field_source["colour_interior"] = colour_source

    # Reading-level numeric targets from the age-band table.
    reading_level = _reading_level_target(root, audience)

    # Assemble the per-field rationale trail.
    rationale: dict[str, str] = {}
    if audience_resolved and audience_defaults.get("rationale"):
        rationale["audience_default"] = audience_defaults["rationale"]
    if book_type_override.get("rationale"):
        rationale["book_type_override"] = book_type_override["rationale"]
    rationale["colour"] = colour_policy["notes"]

    trim_candidates = list(resolved.get("trim_size_candidates", []))
    trim_recommended = resolved.get("trim_size_recommended")
    # Keep the recommended trim inside the candidate set for auditability.
    if trim_recommended and trim_recommended not in trim_candidates:
        trim_candidates = [trim_recommended, *trim_candidates]

    design: dict[str, Any] = {
        "schema_version": "1.0",
        "resolved": audience_resolved,
        "inputs": {
            "audience": audience,
            "book_type": book_type,
            "formats": formats,
        },
        "trim_size": trim_recommended,
        "trim_size_candidates": trim_candidates,
        "colour_interior": colour_interior,
        "colour_policy": colour_policy,
        "tone_register": resolved.get("tone_register"),
        "reading_level_target": reading_level,
        "visual_density": resolved.get("visual_density"),
        "emotional_intensity_ceiling": resolved.get("emotional_intensity_ceiling"),
        "pedagogy_approach": resolved.get("pedagogy_approach"),
        "binding_hint": resolved.get("binding_hint"),
        "paper_hint": resolved.get("paper_hint"),
        "rationale": rationale,
        "provenance": {
            "engine": "publishing_house.design_policy.derive_design",
            "config": "/".join(CONFIG_RELPATH),
            "age_bands": "/".join(AGE_BANDS_RELPATH),
            "colour_source": "publishing_house.project.default_colour_policy",
            "field_source": dict(sorted(field_source.items())),
            "audience_profile_resolved": audience_resolved,
            "book_type_override_applied": bool(
                {k: v for k, v in book_type_override.items() if k != "_book_type"}
            ),
        },
    }
    return design
