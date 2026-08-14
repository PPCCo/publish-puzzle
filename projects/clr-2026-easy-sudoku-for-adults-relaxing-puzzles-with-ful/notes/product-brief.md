# Product Brief — Easy Sudoku for Adults: Relaxing Puzzles with Full Solutions

**Project ID:** `clr-2026-easy-sudoku-for-adults-relaxing-puzzles-with-ful`
**Creator role:** acquisitions-editor (AGT-006, Discovery)
**Timestamp:** 2026-08-14
**Status:** draft (pre-niche-gate; not approved, not registered by this agent)
**Intended schema:** product-brief
**Stage:** DISCOVERY → (targets NICHE_ASSESSMENT)

## Source artifacts

- `project.yaml` — engine-derived design policy under `production.design` (AUTHORITATIVE for craft parameters, rule 20).
- `notes/intake.md` — advisory pipeline context (NOT approved craft values).
- `.claude/config/age_bands.json` — audience profile `adult-general`.

Exact source hashes are recorded by the calling skill at artifact registration; this
agent does not register artifacts or record approvals.

---

## 1. Product identity

- **Working title:** Easy Sudoku for Adults: Relaxing Puzzles with Full Solutions
- **Product-type / family:** `puzzle-book`
- **Series context:** Position 1 of the advisory `adult-difficulty-tier` series (Easy → Medium → Hard → Expert). This brief covers the Easy volume only. Series is advisory and not auto-created (intake F-009). Sibling volumes are out of scope for this brief.
- **One-sentence description:** A single-tier, low-difficulty Sudoku collection for adult beginners and relaxation-seekers, presenting clean high-contrast 9×9 grids with a complete back-of-book numbered solution key.

## 2. Audience specification

- **Audience-band:** `adult-general` (from `age_bands.json`; `age_min` 18, `age_max` null).
- **Reading-level range (instructional text only):** sentence target 8–26 words; paragraph target 1–6 sentences; ≤40 technical terms / 1000 words. *(Source: `age_bands.json:adult-general`; ranges apply to instructions, not puzzle grids.)*
- **Sub-audience notes:** Positioned toward beginners / re-entry solvers and adults seeking a low-pressure "relaxing" experience — the entry point of the difficulty-tiered series. This is a positioning emphasis, not a separate age band.

## 3. Format targets

- **Formats:** `paperback` + `digital-pdf` (from `project.yaml.formats`).
- **Trim-size recommendation:** `8.5x11` (engine-derived recommended; provenance `field_source.trim_size_recommended = audience:adult-general`). Candidate set: `8.5x11`, `6x9`, `7x10`.
  - **Note / open question:** Pipeline advisory expressed a `6x9` preference (intake F-007). Per rule 20 the engine value (`8.5x11`) is authoritative unless a human records a revision. `6x9` is in the candidate set. See Open Question OQ-1.
- **Binding:** paperback (engine `binding_hint = paperback`; provenance `audience:adult-general`).
- **Paper:** white (engine `paper_hint = white`; provenance `audience:adult-general`).

## 4. Channel targets

- **Channels:** `kdp` + `etsy` (from `project.yaml.sales_channels`).
- **Channel-specific constraints (advisory, confirmed at listing gate):**
  - KDP: paperback interior is black-and-white per the derived colour policy; category candidate "Humor & Entertainment > Puzzles & Games > Sudoku" (intake SEO, conf med, F-011/F-012).
  - Etsy: digital-pdf edition must be print-at-home ready (US Letter / A4, DPI minimum) — accessibility/DPI checks apply at the accessibility and listing gates, not here.
  - No live marketplace writes, price commits, or identifier purchases are made by this brief.

## 5. Content specification

- **Puzzle types:** Classic 9×9 Sudoku (single puzzle type). *(Advisory: intake describes a single-tier easy Sudoku collection; exact `content_plan.puzzle_types` literals are set at PLANNING by the content-architect, not here.)*
- **Difficulty range:** Single uniform **easy** tier ("single-tier easy"; intake F-001/F-009, conf high).
- **Difficulty progression structure:** **Flat / single-tier — NO required intra-section difficulty gradient.** A uniform givens count across all puzzles is correct and intended; do NOT specify a rising-givens ramp.
  - **Reconciliation note (rule 20):** The engine-derived `pedagogy_approach = progressive` (provenance `book_type:puzzle-book`) is the generic puzzle-book default (front-to-back ramp). It is intentionally overridden for THIS product to a flat easy tier by the advisory single-tier plan. The tier-to-tier ramp lives at the *series* level (Easy → Medium → Hard → Expert), not within this volume. Verification of the easy tier per-puzzle still applies (see §5 answer/verification).
- **Page-count target range:** ~150 pages. **ADVISORY — pipeline-sourced (intake F-007).** Even-page enforcement and final count are set at layout/build; treat 150 as a target, not a committed literal.
- **Content-volume target:** 200 puzzles. **ADVISORY — pipeline-sourced (intake F-001).** Exact `target_content_count` is committed at PLANNING.
- **Answer-key format:** Complete solutions, grouped **back-only**, keyed to **numbered puzzles** (engine `guidance: "Solutions grouped back-only"`; provenance `age_bands.json:adult-general`; consistent with `content_plan.solutions_placement = back-only`). Interior style: clean high-contrast grids (intake advisory).
- **Verification commitment:** Every puzzle independently verified by code for unique solution, solvability, correct answer key, and that measured difficulty sits within the easy tier (CLAUDE.md §7). Flat progression does not waive per-puzzle easy-tier verification.

## 6. Design-policy parameters (DERIVED — rule 20, not hand-picked)

All values below are taken from the engine-resolved `production.design` block and the
`adult-general` age-band profile. Provenance cited per field.

| Parameter | Value | Provenance |
|---|---|---|
| Colour policy | Black-and-white print interior; digital-pdf may be full colour | `colour_interior = false`; `field_source.colour_interior = audience:adult-general`; colour_policy source `publishing_house.project.default_colour_policy` |
| Tone register | neutral | `field_source.tone_register = audience:adult-general` |
| Visual density | medium | `field_source.visual_density = book_type:puzzle-book` |
| Emotional-intensity ceiling | moderate | `emotional_intensity_ceiling`; `audience:adult-general` |
| Grid-size | 9×9 standard adult-scale grid | Product-type (classic Sudoku) + `adult-general` guidance "Full-difficulty grids" (`age_bands.json`) |
| Cell-size / type-size range | Not enumerated as numeric literals in `age_bands.json` for adult-general puzzle grids (only `senior-large-print` specifies ≥16pt / oversized). See OQ-2. | `age_bands.json:adult-general` (no per-cell numeric range) |
| Visuals per spread | 0–3 | `age_bands.json:adult-general.visuals_per_spread_target` |
| Reading level (instructions) | sentence 8–26 words; ≤40 tech terms/1000w | `age_bands.json:adult-general` |
| Accessibility requirements | High-contrast grids/rules legible at 8.5×11 trim; digital DPI + US Letter/A4 print-at-home (verified at accessibility gate) | CLAUDE.md §9; not a `senior-large-print` product, so no oversized/≥16pt mandate |

## 7. Rights and originality commitments

Stated affirmatively from the seeded `production.legal_defaults` (defaults, confirmed by
a human at compliance/release — not clearances asserted by this agent):

- **Puzzle content:** Generated deterministically by code from a seed and independently verified by code. Classic Sudoku rules and grids are not copyrightable expression; no third-party puzzle sets are copied.
- **Word lists / reference data:** None required (Sudoku is numeric). Rights posture `puzzle_word_lists = original-or-public-domain` applies vacuously; no third-party word lists used.
- **Line art / interior illustration:** Original-only (`rights_posture.line_art = original-only`). Any cover/interior art carries the originality attestation before the interior gate.
- **Fonts:** `licensed-for-commercial-embedding` (from defaults; embedding license confirmed before build).
- **AI disclosure:** Per `legal_defaults.ai_disclosure` — puzzles and layout generated and verified by software; art original; no AI text presented as human authorship.
- **Blocking default:** `default_asset_rights_status = unknown-blocks-release` remains in force until each asset's rights are cleared.

## 8. Competitive positioning statement

Entry point of a difficulty-tiered adult Sudoku series, capturing a low-competition tail
through an "easy / relaxing" beginner framing rather than competing in the saturated
general-Sudoku head term (intake positioning, F-009/F-016).

## 9. Open questions (require a human decision before the brief is complete)

- **OQ-1 — Trim size:** Engine recommends `8.5x11`; pipeline advisory preferred `6x9` (in candidate set). Per rule 20 the engine value stands unless a human records a revision. Decide at/ before the niche gate whether to record a trim revision.
- **OQ-2 — Cell/type-size numeric range:** `age_bands.json:adult-general` does not specify numeric cell-size or type-size literals for puzzle grids (only `senior-large-print` does). Deferred to the design-policy engine / layout stage; no human-approved numeric default exists for adult-general grid cells. Flagged rather than invented.
- **OQ-3 — Committed content-volume and page count:** 200 puzzles / ~150 pages are advisory pipeline targets; the committed `target_content_count` and even final page count are set at PLANNING by the content-architect.
- **OQ-4 — Price band:** Live BSR / price confirmation is deferred to the listing gate (intake open question); no price is committed here.
- **OQ-5 — Series creation:** The `adult-difficulty-tier` series is advisory and not auto-created; whether to formalize it via `/product-series-new` is a human decision outside this brief.

## 10. Consistency check (niche-opportunity ↔ design policy ↔ brief)

- **Audience band:** `adult-general` — agrees across `project.yaml`, intake, and this brief. ✓
- **Product type:** `puzzle-book` — agrees. ✓
- **Formats:** `paperback` + `digital-pdf` — agrees. ✓
- **Channels:** `kdp` + `etsy` — agrees. ✓
- **Colour / trim / density:** brief matches engine-derived `production.design`. ✓ (one flagged trim discrepancy handled as OQ-1, not silently resolved)
- **Difficulty:** brief reflects advisory "single-tier easy" and overrides the generic `progressive` default with a recorded rule-20 reconciliation note. ✓

No unresolved cross-source conflict on audience band or channel scope; no escalation
condition met.
