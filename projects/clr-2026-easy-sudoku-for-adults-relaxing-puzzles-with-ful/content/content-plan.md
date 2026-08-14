# Content Plan — Easy Sudoku for Adults: Relaxing Puzzles with Full Solutions

**Project ID:** `clr-2026-easy-sudoku-for-adults-relaxing-puzzles-with-ful`
**Creator role:** content-architect (AGT-008, Content)
**Timestamp:** 2026-08-14
**Status:** draft (PLANNING stage; not approved, not registered by this agent)
**Intended schema:** content-plan
**Stage:** PLANNING

## Source artifacts

- Product brief: `notes/product-brief.md` — `sha256:503b2bcdee75f6c8196efd09b7734a6e1eb22ec83e53d3fef8d9d3a624e4e608` (niche gate APPROVED).
- `project.yaml` — engine-derived `production.design` block (AUTHORITATIVE for craft parameters, rule 20). Hash recorded by the calling skill at registration.
- `.claude/config/age_bands.json` — audience profile `adult-general`.

This agent produces plans only; it does not generate or verify puzzle content, transition
state, approve gates, or register artifacts.

---

## 1. Product and audience summary

- **Product family:** `puzzle-book`
- **Audience band:** `adult-general` (`age_min` 18, `age_max` null)
- **Single puzzle type:** classic 9×9 Sudoku
- **Colour:** black-and-white print interior (`colour_interior = false`); digital-pdf may be full colour. Not a `senior-large-print` product — no oversized/≥16pt mandate, but grids/rules must stay high-contrast at 8.5×11 (CLAUDE.md §9).
- **Trim (engine-authoritative):** `8.5x11`; candidate set `8.5x11`, `6x9`, `7x10`. Trim revision to `6x9` remains an open human decision (brief OQ-1) and would change all page-budget arithmetic below.

## 2. Committed content volume

- **`target_content_count` = 200 puzzles** (commits brief §5 / OQ-3 advisory target).
- All 200 are a single easy-tier batch (see §4).

## 3. Section structure

The book is a single uniform batch, not a multi-tier ramp. Sections are organizational
(navigation / pacing) rather than difficulty bands, consistent with the flat progression.

| Section | Content | Puzzle numbers | Difficulty label |
|---|---|---|---|
| Front matter | Cover page, title page, copyright/AI-disclosure page, how-to-solve + instructions, one warm-up/example solved grid | n/a | n/a |
| Main puzzle set | 200 classic 9×9 Sudoku, uniform easy tier | 1–200 | easy (uniform) |
| Back matter — answer key | Complete solutions, back-only, grouped by ascending puzzle number | keyed to 1–200 | n/a |

There is a single puzzle section by design. The three example section names in the
generic playbook (Easy Warm-Up / Medium Main / Hard Challenge) do NOT apply here: this
volume is the "Easy" position of the series, so its entire interior is one easy tier. The
tier-to-tier ramp lives at the series level (Easy → Medium → Hard → Expert), not inside
this volume.

## 4. Puzzle-batch composition

- **Batch:** one batch — `main-easy` — 200 items.
- **Puzzle type:** classic 9×9 Sudoku (single type).
- **Grid size / format:** standard adult-scale 9×9 grid.
- **Difficulty label:** `easy` (uniform across all 200).
- **Clue/givens density:** a **uniform givens count** across all 200 puzzles, held within
  the easy tier. This plan does NOT specify a rising-givens ramp; a flat givens count is
  correct and intended (see §5). Exact numeric givens count sits within the easy-tier
  band and is set by the deterministic generator/verifier, not hand-picked here.
- **Cell/type-size numeric literals:** `age_bands.json:adult-general` enumerates no
  per-cell numeric range for adult puzzle grids (only `senior-large-print` does). No
  human-approved numeric default exists; this is deferred to the design-policy/layout
  stage and flagged (carries forward brief OQ-2). This plan does NOT invent a cell size.

## 5. Difficulty progression — FLAT / SINGLE-TIER

- **Recorded progression: FLAT (single-tier easy). There is NO required intra-section
  difficulty gradient.** A uniform givens count across all 200 puzzles is the committed,
  intended structure.
- **Rationale note:** This volume is position 1 (Easy) of the advisory
  `adult-difficulty-tier` series. Its purpose is a low-pressure, uniform "relaxing"
  experience for beginners / re-entry solvers. A front-to-back ramp within the volume
  would contradict that positioning. The engine-derived generic
  `pedagogy_approach = progressive` (provenance `book_type:puzzle-book`) is intentionally
  OVERRIDDEN for this volume to a flat easy tier by the committed plan; the ramp lives at
  the series level, not within this book.
- **Downstream verification directive:** flat givens is CORRECT for this product.
  Downstream verification must NOT flag uniform/flat givens as a difficulty-progression
  mismatch. Per-puzzle easy-tier verification still fully applies: every puzzle is
  independently verified by code for unique solution, solvability, correct answer key,
  and that measured difficulty sits within the easy tier (CLAUDE.md §7). The flat
  progression waives only the intra-volume ramp check, not per-puzzle difficulty
  accuracy.

## 6. Answer-key placement policy

- **Placement: back-only.** No inline or per-page micro-keys (brief §5;
  `content_plan.solutions_placement = back-only`; engine guidance "Solutions grouped
  back-only"). Inline placement is prohibited for this product.
- **Content:** complete solved 9×9 grids (full solutions, not partial).
- **Format:** grid thumbnails (compact solved grids), high-contrast, black-and-white.
- **Grouping / keying:** grouped as one back-of-book section, ordered by ascending puzzle
  number, each solution labelled with its puzzle number (1–200) so a solver can locate any
  answer by number.

## 7. Page-budget estimate (ADVISORY — final count set at layout/build)

The brief records ~150 pages as an advisory pipeline target (OQ-3); the committed, even
final page count is set at LAYOUT_AND_FORMAT_BUILD, not here. At 8.5×11 the estimate
depends on puzzle-per-page layout, which is a layout-stage decision:

| Component | One puzzle / page | Two puzzles / page |
|---|---|---|
| Front matter | ~4–6 pp | ~4–6 pp |
| 200 puzzles | ~200 pp | ~100 pp |
| Answer key (200 solved grids @ ~6/page) | ~34 pp | ~34 pp |
| Back matter (about the series / blank) | ~2 pp | ~2 pp |
| **Approx. interior total (pre even-page rounding)** | **~240–242 pp** | **~140–142 pp** |

- The advisory ~150-page target closes cleanly under a **two-puzzles-per-8.5×11-page**
  layout (~140–142 pp before even-page rounding). A strict one-puzzle-per-page layout at
  8.5×11 would run ~240 pp and would NOT meet the ~150 advisory.
- **Layout recommendation (advisory, not a committed craft literal):** two easy 9×9 grids
  per 8.5×11 page keeps the page budget near the ~150 target while preserving high-contrast
  legibility for adult-general (no large-print mandate). Final cell size and puzzles-per-page
  are resolved at the layout stage against OQ-2; this plan does not fix them.
- Note: choosing the candidate `6x9` trim (OQ-1) would materially change this arithmetic
  (typically one puzzle per 6×9 page), pushing toward ~200+ interior pages. The estimate
  above assumes the engine-authoritative `8.5x11`.

## 8. Seed namespace convention

- **Convention:** `<project-id>/<section-slug>/<index>`
- **This volume:**
  `clr-2026-easy-sudoku-for-adults-relaxing-puzzles-with-ful/main-easy/001` …
  `clr-2026-easy-sudoku-for-adults-relaxing-puzzles-with-ful/main-easy/200`
- Zero-padded 3-digit index (`001`–`200`) so puzzle number maps 1:1 to seed index and to
  answer-key label. This lets the generator reproduce any puzzle deterministically and lets
  verification address any puzzle by its number.

## 9. Internal consistency check

- Puzzle count (200) = seed indices (`main-easy/001`–`200`) = answer-key entries (1–200). ✓
- Single type, single tier, single batch — no conflicting puzzle types within the trim. ✓
- Difficulty labelling (`easy`, uniform) matches the flat progression and the brief. ✓
- Answer key back-only matches brief and engine guidance; no inline keys. ✓
- Colour (black-and-white interior) unchanged from `project.yaml`. ✓
- Page budget: adjusted via layout density (puzzles-per-page), NOT by shrinking cells
  below any band minimum or trimming margins. No band cell/type minimum exists to violate
  for adult-general (OQ-2), so no minimum is breached. ✓

## 10. Proposed `content_plan` object for `project.yaml`

```yaml
content_plan:
  puzzle_types:
  - sudoku
  target_content_count: 200
  difficulty_progression: flat-single-tier-easy
  solutions_placement: back-only
```

`puzzle_types` uses `sudoku`, the exact generator-registry key
(`publishing_house/generators/puzzles.py`:
`registry.register(ContentType("sudoku", ...))`), so `generate --type sudoku`
resolves without a KeyError. The classic 9×9 form is recorded throughout this
document; the registry has one Sudoku content type (`sudoku`, "Sudoku (9x9)").
`difficulty_progression` is a free-form string in the `content_plan` schema (no
enum), so the explicit `flat-single-tier-easy` value is stored verbatim to record
the flat single easy tier for FIX-B downstream verification.

## 11. Open questions carried forward

- **OQ-1 (trim):** engine `8.5x11` is authoritative; `6x9` pipeline preference remains a
  human revision decision. Changes the §7 page budget materially.
- **OQ-2 (cell/type size):** no adult-general numeric cell/type literal in `age_bands.json`;
  deferred to design-policy/layout. Not invented here.
- **OQ-3 (final page count):** ~150 advisory; committed even page count set at layout/build.
  200 puzzles is now committed as `target_content_count`.
- **`content_plan` write mechanism:** whether the flat progression is committed by direct
  `project.yaml` edit or a sanctioned CLI verb is deferred to the invoking orchestrator
  (see completion summary).
