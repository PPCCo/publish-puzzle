"""Bridge a project's approved design into a cover-art image brief.

Deterministic, network-free. Mirrors :mod:`coloring_bridge`: it reads the
canonical product spec (``project.yaml`` — working title, audience band, and the
resolved ``production.design`` block) and emits ONE schema-valid
``visuals/briefs/<brief_id>.json`` illustration brief carrying a
``generation_prompt.positive`` tuned for a COMMERCIAL COVER BACKGROUND, so the
existing ``image_gen.build_guide`` / ``image_gen_status`` / ``image_gen.ingest``
machinery acts on it with zero change.

Two rules shape the prompt (locked decisions, see the Phase 3 plan):

* **Reserve white space for typography (DECISION #2).** Generative models are
  poor at typography, so the cover ART requests NO in-image text and explicitly
  asks the model to leave a clean, uncluttered band (upper third for the title,
  a calm lower band for author/series, generous margins). Claude then composites
  REAL type into that reserved space with the cleared-font compositor
  (:func:`compositor.compose_cover_wrap`).
* **flux negatives are inert (CFG~1).** ``local-flux-schnell`` ignores the
  negative prompt, so every "no text / no watermark / reserve space" constraint
  is stated in the POSITIVE prompt. A negative is still recorded for the SDXL
  fallback, which does honour it.

The bridge produces the brief only; it renders nothing and clears nothing. Live
rendering is the skill/agent step through the out-of-core MCP bridge (rule 18).
Covers MAY be full colour even when the interior is greyscale (rule 22).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .paths import ProjectPaths
from .util import atomic_write_json, load_yaml, utc_now
from .validation import validate_data

# Single-source the trim table + spine math from the layout module so a cover
# brief's pixel dimensions match the wrap the cover builder will render into.
# Never duplicate the trim table (rule 20 analog of TRIM_SIZES).
from .layout import _trim as _trim_inches

_DEFAULT_DPI = 300
_BLEED_IN = 0.125
_COVER_PURPOSE = "cover front art"

# Deterministic palette + mood descriptors derived from the audience band. These
# are DESCRIPTORS fed to the generator (not hand-picked craft literals baked into
# a build); they follow the resolved design policy's tone_register/high_contrast.
# Kept small and offline; an inspiration pass (Phase 3 #4) may augment them.
_BAND_MOOD: dict[str, str] = {
    "senior-large-print": (
        "calm, warm, reassuring, high-contrast, uncluttered, generous negative space, "
        "soft even lighting, dignified and inviting, easy on the eyes"
    ),
    "adult-general": (
        "calm, relaxing, elegant, modern, tasteful, uncluttered, soothing, "
        "premium bookstore quality, restful negative space"
    ),
    "kids-4-8": "friendly, cheerful, bright, playful, rounded, gentle, non-scary",
    "kids-6-10": "playful, bright, adventurous, positive, welcoming",
    "tween-8-12": "cool, confident, energetic, age-appropriate, non-horror",
}
_DEFAULT_MOOD = "clean, professional, uncluttered, commercially appealing, tasteful negative space"


def _dimensions(project: dict[str, Any]) -> dict[str, int]:
    """Front-panel pixel dimensions from trim x dpi + bleed. Deterministic."""
    width_in, height_in = _trim_inches(project)
    dpi = int(
        ((project.get("production") or {}).get("print") or {}).get("dpi")
        or _DEFAULT_DPI
    )
    return {
        "width_px": int(round((width_in + _BLEED_IN) * dpi)),
        "height_px": int(round((height_in + 2 * _BLEED_IN) * dpi)),
        "dpi": dpi,
    }


def _subject_phrase(project: dict[str, Any]) -> str:
    """A neutral, IP-safe subject phrase for the cover art background.

    Derived from the product family + topic. Never names a living artist, a
    protected character, or a real person; the prompt asks for an ORIGINAL,
    generic illustrative background suitable behind puzzle-book typography.
    """
    family = str(project.get("book_type") or project.get("product_type") or "puzzle-book")
    topic = str(project.get("topic") or "").strip()
    if family == "coloring-book":
        return "an original decorative illustrative motif suitable for a coloring-book cover"
    if family == "puzzle-book":
        return (
            "an original, abstract, tasteful background motif evoking quiet puzzle-solving "
            "(soft geometric grid textures, gentle light, no readable numbers or letters)"
        )
    if family in {"guided-journal", "planner", "workbook"}:
        return "an original, serene, minimal background motif suitable for a guided journal cover"
    # Generic fall-through keeps the topic as loose inspiration only.
    return f"an original, tasteful, abstract background motif loosely evoking: {topic}"


def _mood(project: dict[str, Any]) -> str:
    band = str(
        ((project.get("production") or {}).get("design") or {})
        .get("reading_level_target", {})
        .get("band")
        or project.get("audience", "")
    )
    return _BAND_MOOD.get(band, _DEFAULT_MOOD)


def _positive_prompt(project: dict[str, Any]) -> str:
    """Cover-art positive prompt with reserved white space + no in-image text.

    Every constraint lives here because flux-schnell ignores the negative prompt.
    """
    subject = _subject_phrase(project)
    mood = _mood(project)
    design = (project.get("production") or {}).get("design") or {}
    high_contrast = bool(design.get("high_contrast"))
    density = str(design.get("visual_density") or "medium")
    contrast_clause = "high contrast, bold, legible" if high_contrast else "balanced contrast"
    return (
        f"professional book cover background illustration, {subject}, {mood}, "
        f"{contrast_clause}, {density} visual density, "
        "portrait orientation, full-bleed composition, "
        # Reserved-white-space instruction (DECISION #2) — stated positively:
        "leave a clean uncluttered upper band with calm empty space for a title, "
        "leave a calm lower band with empty space for author and series text, "
        "generous quiet margins, simple focal composition, "
        # No-typography instruction — flux honours these only in the positive:
        "absolutely no text, no words, no letters, no numbers, no lettering, "
        "no typography, no captions, no watermark, no signature, no logo, no frame, "
        "original artwork, not derivative of any existing book cover or protected work, "
        "commercial print quality, 300 dpi, crisp, clean"
    )


# Recorded for the SDXL fallback, which DOES honour negatives (flux ignores it).
_NEGATIVE_PROMPT = (
    "text, words, letters, numbers, typography, caption, watermark, signature, logo, "
    "frame, border, cluttered, busy, low contrast, blurry, distorted, deformed, "
    "copyrighted character, trademarked logo, real person, celebrity likeness"
)


def _alt_text(project: dict[str, Any]) -> str:
    title = str(project.get("working_title") or project.get("project_id") or "the book")
    mood = _mood(project).split(",")[0].strip()
    return (
        f"Original {mood} illustrative background art for the cover of “{title}”, "
        "with clean reserved space for the title and author typography; no in-image text."
    )


def _rights_constraints() -> list[str]:
    return [
        "Original AI-generated cover art only; not a trace, copy, or close derivative of any "
        "existing book cover, photograph, artwork, character, or logo.",
        "No imitation of a living artist by name or recognisable style.",
        "No trademarked logo, protected character, trade dress, or identifiable real person's likeness.",
        "In-image text is prohibited; the title/author/series typography is composited separately "
        "in a rights-cleared embeddable font.",
        "Must clear the rights gate (provider commercial_rights_verified) before advancing past cover.",
    ]


def brief_from_cover_art(
    root: Path,
    project_id: str,
    provider: str | None = None,
    actor: str = "cover-bridge",
) -> dict[str, Any]:
    """Emit one schema-valid cover-art image brief for the project.

    Deterministic and offline. Validated against ``illustration-brief.schema.json``
    before it is written; a validation error aborts before any write. Returns a
    summary with the emitted brief_id and path. Re-running overwrites the brief
    with identical content (idempotent bar the ``status`` field), never the art.
    """
    paths = ProjectPaths(root, project_id).require()
    project = load_yaml(paths.config, {}) or {}

    # Resolve preferred provider deterministically: explicit arg wins, else the
    # configured default. Advisory only — image_gen re-resolves at guide/ingest.
    from . import image_gen  # lazy: avoid Pillow-adjacent import at module load

    default_provider = image_gen.image_generation_config(root).get("default_provider")
    preferred_provider = provider or default_provider

    briefs_dir = paths.directory / "visuals" / "briefs"
    dimensions = _dimensions(project)
    brief_id = "clr-cover-art-front"

    brief = {
        "brief_id": brief_id,
        "project_id": project_id,
        "location": "cover front panel background (full-bleed)",
        "purpose": _COVER_PURPOSE,
        "scene_or_subject": _subject_phrase(project),
        "required_elements": [
            "original full-bleed background illustration",
            "clean uncluttered upper band reserved for the title",
            "calm lower band reserved for author/series text",
            "generous quiet margins",
        ],
        "prohibited_elements": [
            "in-image text",
            "lettering",
            "numbers",
            "watermark",
            "signature",
            "logo",
            "frame",
            "protected character or trademarked design",
            "identifiable real person's likeness",
        ],
        "composition": (
            "portrait full-bleed background; single calm focal motif; upper third and lower "
            "band left visually quiet so real typography can be composited into them"
        ),
        "colour_and_lighting": (
            "full colour cover art (covers MAY be colour even when the interior is greyscale, "
            "rule 22); soft even lighting; palette derived from the audience band and tone register"
        ),
        "dimensions": dimensions,
        "alt_text_draft": _alt_text(project),
        "rights_constraints": _rights_constraints(),
        "generation_prompt": {
            "positive": _positive_prompt(project),
            "negative": _NEGATIVE_PROMPT,
            "seed": None,
        },
        "image_complexity": "complex",
        "preferred_provider": preferred_provider,
        "status": "draft",
    }

    schema_errors = validate_data(root, brief, "illustration-brief.schema.json")
    if schema_errors:
        return {
            "status": "fail",
            "project_id": project_id,
            "errors": [f"{brief_id}: {'; '.join(schema_errors)}"],
            "brief_id": brief_id,
        }

    brief_path = briefs_dir / f"{brief_id}.json"
    atomic_write_json(brief_path, brief)

    return {
        "status": "pass",
        "project_id": project_id,
        "provider": preferred_provider,
        "brief_id": brief_id,
        "brief_path": brief_path.relative_to(paths.directory).as_posix(),
        "dimensions": dimensions,
        "bridged_at": utc_now(),
        "bridged_by": actor,
        "next_action": (
            "Generate the cover art via the comfyui-mcp bridge (provider "
            f"{preferred_provider}), save to visuals/assets/{brief_id}.png, then "
            f"`image-gen ingest {project_id} --brief-id {brief_id} "
            f"--file visuals/assets/{brief_id}.png --provider <provider>`. "
            "Then `build cover --project-id <id> --style art`."
        ),
    }
