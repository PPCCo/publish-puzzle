# Content Plan — Large Print Sudoku for Seniors: Easy Puzzles with Solutions

- **Project ID:** clr-2026-large-print-sudoku-for-seniors-easy-puzzles-with
- **Lifecycle stage:** PLANNING
- **Creator role:** content-architect
- **Created:** 2026-07-31
- **Status:** DRAFT — planning artifact. No approval, freeze, verification, or clearance granted or implied.
- **Intended schema:** content plan (markdown; companion to `project.yaml` `content_plan` block)
- **Source artifacts (read-only):**
  - `projects/clr-2026-large-print-sudoku-for-seniors-easy-puzzles-with/project.yaml`
  - `projects/clr-2026-large-print-sudoku-for-seniors-easy-puzzles-with/notes/intake.md`
  - `projects/clr-2026-large-print-sudoku-for-seniors-easy-puzzles-with/brief/product-brief.md`
  - `.claude/config/age_bands.json` (band `senior-large-print`)
  - `.claude/config/design_policy.json`

> Hash binding: source-artifact hashes are recorded by the artifact-registration
> step at registration time (see `state.json` `active_artifacts`), not asserted here.
> This document produces a plan only. It does not generate or verify puzzle content,
> does not set difficulty as a fact, and does not mutate state or approvals.

---

## 1. Puzzle type and grid specification

- **Puzzle type:** standard 9x9 sudoku (`sudoku-9x9`). Single type; no variants (no killer,
  diagonal, jigsaw, or mini grids) — a single, familiar form suits the accessibility-first band.
- **Grid:** 9x9, 81 cells, digits 1–9, one solution per puzzle.
- **Givens (planning parameter — NOT a verified difficulty claim):** target 36–45 givens per
  easy puzzle. Higher given counts and forgiving logic paths keep the puzzle solvable without
  advanced techniques (naked/hidden singles dominant). Actual measured difficulty MUST match
  the `easy` label and be **code-verified** at generation/verification; this range is a
  generation target, not an asserted difficulty.
- **Uniqueness/solvability:** every puzzle SHALL be generated deterministically from a seed and
  independently verified by code for a unique solution and solvability before it advances.

## 2. Difficulty tier and progression rationale

- **Tiers:** `easy` only. Single tier — no medium or hard puzzles in this volume.
  Description: forgiving, single easy tier.
- **Progression (`progressive`, within the easy band):** puzzles are ordered from the
  most-forgiving (higher givens, purely single-based logic) toward the slightly-more-challenging
  end of the easy range (lower givens within 36–45, still no advanced techniques). The ramp
  stays entirely inside the easy tier — it never crosses into medium.
- **Rationale:** the `senior-large-print` band calls for forgiving difficulty and a gentle,
  confidence-building experience. A within-tier ramp gives a sense of progress without
  introducing frustration or techniques inappropriate for an easy-tier book. This is consistent
  with the derived pedagogy (`progressive`, front-to-back) recorded under
  `production.design` in `project.yaml`.

## 3. Puzzle count and page budget (ADVISORY)

Both figures below originate from the `/research` pipeline entry and are recorded as
**advisory planning targets, not committed counts**. No competition-analyst page-budget
report is on file; these require human confirmation (see §7) and code-verified confirmation
at generation.

- **Puzzle count target:** 100 puzzles (advisory). Rationale: 100 is a common, marketable
  volume for the category and fits the ~110-page budget at one puzzle per page. The final
  count is whatever code generates and verifies; any `[N]` used in a title or metadata MUST
  equal the code-verified count.
- **Page budget target:** ~110 pages (advisory). Closure check below.

### Page budget closure (advisory arithmetic)

| Section | Pages | Basis |
|---|---|---|
| Introduction / how-to | 1 | Single short instruction page (band: simple, unambiguous instructions) |
| Puzzles | ~100 | One puzzle per page (band requirement); 100 puzzles |
| Solutions (back-only) | ~9 | ~12 solution thumbnail grids per 8.5x11 page × 100 solutions |
| **Interior total (planning)** | **~110** | Closes to the advisory page budget |

- Final even-page-count enforcement and any pagination padding are handled at interior build,
  not here. Section sizes — not margins or cell sizes — are the adjustment lever if the count
  or budget changes; grid/type minimums (§5) SHALL NOT be reduced to fit a page target.

## 4. Section structure

1. **Introduction (1 page):** short, plain-language explanation of sudoku rules and how to
   use the book (one puzzle per page; solutions at the back). Reading level per band:
   sentences 6–18 words, 1–4 sentences per paragraph.
2. **Puzzles (~100 pages):** one 9x9 puzzle per page, oversized grid, ample white space,
   ordered by the within-easy-tier progression in §2. Each puzzle carries a stable index
   for cross-reference to its solution.
3. **Solutions (back-only, ~9 pages):** full solution grids grouped at the back, in puzzle-number
   order (see §6). No inline or per-page keys.

Front matter beyond the single introduction page (title page, copyright/legal, any AI-disclosure
statement) is finalized at interior build and metadata stages; this plan reserves the
introduction as the functional front-matter content page and treats standard title/legal pages
as build-stage additions.

## 5. Accessibility requirements (senior-large-print)

From the band profile in `age_bands.json` and the resolved design policy; these are targets
verified only at the accessibility gate (must PASS or WARNING before compliance).

- **Clue digits ≥ 16pt** (band body-type minimum; grid digits SHALL be at least this size and
  oversized where the grid allows). These are floors — the plan SHALL NOT specify type or grid
  sizes below the band minimums.
- **Oversized grid:** the 9x9 grid occupies a large share of the page for generous cell size and
  fine-motor accessibility.
- **High contrast:** black-on-white; avoid low-contrast greys and thin rules for grid lines.
- **Ample white space:** one puzzle per page, uncrowded layout.
- **One puzzle per page** (band requirement) — no two-up or multi-puzzle spreads.
- **Simple, unambiguous instructions** in the introduction.
- Interior is black-and-white high-contrast (derived colour policy); colour is not used, to
  preserve contrast.

## 6. Answer-key (solutions) format

- **Placement:** back-only (derived pedagogy; no inline micro-keys). The design does not
  authorize inline keys, so none are placed.
- **Format:** full completed solution grids rendered as compact thumbnail grids (all 81 cells
  filled), high-contrast, legible at trim.
- **Grouping:** by puzzle number, in the same order as the puzzle section, so a reader finds a
  solution by its puzzle index. Grouped in a single back-of-book section.

## 7. Seed namespace convention

- **Namespace:** `clr-2026-large-print-sudoku-for-seniors-easy-puzzles-with/puzzles/<index>`
  where `<index>` is the puzzle's 1-based position in the puzzle section.
- Every puzzle is reproducible deterministically from its seed within this namespace, so
  generators and verifiers can regenerate or check any single puzzle independently.
- Solutions inherit the same index as their puzzle (no separate seed namespace); a solution is
  derived from, and verified against, the puzzle at the same index.

## 8. Consistency check

Audience band `senior-large-print`, product family `puzzle-book`, trim `8.5x11`, B&W
high-contrast interior, `progressive` pedagogy, and back-only solutions are consistent across
`project.yaml` (`production.design` and updated `content_plan`), `notes/intake.md`, and
`brief/product-brief.md`. Planned puzzle count (100), page consumption (~110), and the
single easy difficulty tier are internally consistent (§3 closure). No cross-source
discrepancy found. No escalation condition (§ mission) is triggered: the page budget
accommodates 100 easy puzzles at band-minimum grid/type sizes, no conflicting puzzle types
exist, and all required config fields were present.

## 9. Open human decisions (carried from brief; not resolved here)

These remain open and are flagged, not decided, by this plan:

1. **Confirm content-volume + page budget:** accept advisory 100 puzzles / ~110 pages as the
   committed planning target, or set alternatives. (Currently recorded advisory in `project.yaml`.)
2. **Etsy fulfilment:** resolve how a paperback-only product is fulfilled on Etsy, or drop Etsy
   for this edition. (Etsy is typically digital-download.)
3. **AI-assistance disclosure requirement:** `rights.ai_assistance_disclosure_required` is
   `unknown` in `project.yaml`; must be resolved before the compliance gate.
4. **Series creation:** create the `senior-large-print` series (this = volume 1) now, or defer.

## 10. Quality rubric (self-assessment)

- **Audience Calibration — 5/5.** Grid/type minimums (≥16pt, oversized grid, high contrast,
  one-per-page) taken directly from the `senior-large-print` band profile; easy single tier
  matches the band's forgiving-difficulty guidance.
- **Page Budget Closure — 4/5.** 1 + ~100 + ~9 = ~110 closes to the advisory budget; docked one
  point because count/budget are advisory pending human confirmation and code-verified counts.
- **Difficulty Progression — 5/5.** Monotonic ramp defined entirely within the easy tier
  (higher→lower givens inside 36–45), never crossing into medium; `easy` is an approved label.
- **Seed Namespace Coverage — 5/5.** Deterministic per-puzzle namespace covers every puzzle and
  ties each solution to its puzzle index for independent regeneration/verification.
- **Answer-Key Policy Clarity — 5/5.** Back-only, full solution thumbnails, grouped by puzzle
  number; no inline keys, consistent with derived pedagogy.
- **Production Feasibility — 4/5.** One puzzle per page at band-minimum sizes fits 8.5x11 with
  margin; docked one point pending accessibility-gate verification of contrast/type/grid fit and
  final even-page-count handling at build.
