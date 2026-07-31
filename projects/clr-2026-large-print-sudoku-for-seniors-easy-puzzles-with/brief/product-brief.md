# Product Brief — Large Print Sudoku for Seniors: Easy Puzzles with Solutions

- **Project ID:** clr-2026-large-print-sudoku-for-seniors-easy-puzzles-with
- **Lifecycle stage:** DISCOVERY (→ NICHE_ASSESSMENT)
- **Creator role:** acquisitions-editor
- **Created:** 2026-07-31
- **Status:** DRAFT — pre-niche-gate. No approval granted or implied.
- **Intended schema:** discovery product brief (markdown; supporting artifact for the niche gate)
- **Source artifacts (read-only):**
  - `projects/clr-2026-large-print-sudoku-for-seniors-easy-puzzles-with/project.yaml`
  - `projects/clr-2026-large-print-sudoku-for-seniors-easy-puzzles-with/notes/intake.md`
  - `.claude/config/age_bands.json` (band `senior-large-print`)

> This brief specifies audience, product family, formats, engine-derived craft
> constraints, advisory planning targets, positioning, channel intent, and the
> open human decisions needed before the niche gate. It does not mutate state,
> project.yaml, approvals, or register artifacts.

---

## 1. Product identity

- **Working title:** Large Print Sudoku for Seniors: Easy Puzzles with Solutions
- **Product family / type:** `puzzle-book` (sudoku)
- **Series context:** Advisory — pipeline marks this as `senior-large-print` series, position 1 (volume 1 of a proposed easy → medium set). Series **not** created; creation is an open human decision (see §9).
- **One-sentence description:** A large-print sudoku puzzle book of easy, forgiving
  puzzles for seniors, one puzzle per page at high contrast, with a back-of-book
  solutions section.

## 2. Audience specification

- **Audience band:** `senior-large-print` (from `age_bands.json`).
- **Age range:** age_min 55, age_max open (null).
- **Reading level (instructional/prompt text only, not grids):** sentences 6–18 words;
  paragraphs 1–4 sentences; technical terms ≤ 20 per 1000 words; default word budget 0–3000.
- **Sub-audience notes:** Accessibility-first band. Design must accommodate reduced
  visual acuity and fine-motor limitations: oversized grids, high contrast, ample white space.

## 3. Format targets

- **Formats:** `paperback` only (human-committed). No digital-PDF, hardcover, or other
  edition is in scope for this brief.
- **Trim size:** `8.5x11` recommended (engine-derived); candidate set `8.5x11`, `8x10`.
  Rationale (derived): large-print band favours large grids and type. See §5.
- Format scope is subject to human confirmation (see §9).

## 4. Channel targets (intent only)

- **Intended channels:** `kdp` and `etsy` (recorded at project init as default `sales_channels`).
  This is **channel intent for planning**, not a listing, submission, or account action.
- **Channel-specific notes (advisory, to be verified at listing stage):**
  - KDP: 8.5x11 paperback is a standard KDP trim; back-only solutions and even page
    count are enforced at build, not here.
  - Etsy: typically a digital-download marketplace; a paperback-only product may need
    a fulfilment decision at listing stage. Flagged as an open channel question, not resolved here.
- No external write, price commit, or submission is performed or authorized.

## 5. Engine-derived craft constraints (DERIVED — cited, not chosen here)

All values below are derived by `publishing_house.design_policy.derive_design` from
`audience` + `book_type` + numeric age band, per rule 20-design-policy, and recorded
under `production.design` in `project.yaml`. They are cited here, not invented or overridden.

| Field | Derived value | Provenance (field_source) |
|---|---|---|
| Trim size | `8.5x11` (candidates `8.5x11`, `8x10`) | `audience:senior-large-print` |
| Colour interior | `false` — black-and-white high-contrast | `audience:senior-large-print` |
| Colour policy (print) | text = black-and-white-high-contrast; images = black-and-white | `default_colour_policy` |
| Tone register | `calm-clear` | `audience:senior-large-print` |
| Visual density | `medium` | `book_type:puzzle-book` |
| Emotional intensity ceiling | `gentle` | `audience:senior-large-print` |
| Pedagogy | `progressive` (difficulty front-to-back; solutions **back-only**) | `book_type:puzzle-book` |
| Binding hint | `paperback` | `audience:senior-large-print` |
| Paper hint | `white` | `audience:senior-large-print` |

No design-policy parameter required for this brief was missing from `age_bands.json`
or the resolved design policy; no open design-policy question is raised.

## 6. Accessibility expectations (senior-large-print)

From the band profile in `age_bands.json` (formally verified only at the accessibility gate):

- Large-print body type **≥ 16pt** and oversized grids.
- High contrast; avoid low-contrast greys and thin rules.
- One puzzle per page with ample white space.
- Simple, unambiguous instructions.
- Visuals per spread target 0–2 (grids are the primary visual; decorative art minimal).

These are targets. The accessibility gate (contrast, grid/cell legibility, large-print
fit) must PASS or WARNING before compliance approval; this brief does not assert compliance.

## 7. Content specification

- **Puzzle types:** sudoku (single type). `project.yaml` `content_plan.puzzle_types` is
  currently empty and will be set at the content-plan stage.
- **Difficulty range:** easy / forgiving (advisory, pipeline). Consistent with the band's
  forgiving-difficulty guidance. Actual measured difficulty must match the `easy` label
  and be **code-verified** at generation/verification; the label is not asserted here.
- **Difficulty progression:** `progressive` front-to-back within the easy tier (derived).
- **Solutions / answer-key format:** full solutions grouped **back-only** (derived pedagogy).
- **Page-count target:** ~110 pages — **advisory** planning target (pipeline), not committed.
- **Content-volume target:** 100 puzzles — **advisory** planning target (pipeline), not committed.
  Any `[N]` count used in a title or metadata must equal a code-verified puzzle count.

> Content-volume and page-budget targets are advisory only because no competition-analyst
> landscape report with evidence-based page-count constraints is on file for this project;
> these figures originate from the `/research` pipeline entry and require human confirmation
> (see §9). They are directionally reasonable for the band and product type but are not
> treated as validated constraints.

## 8. Positioning, rights, and originality

### Positioning hypothesis (advisory — explicit uncertainty)

- Positioning: high-contrast, oversized-grid large-print sudoku for seniors, easy tier,
  with clearly-signposted back-of-book solutions.
- **Unverified claims (direction only, NOT fact):** The "senior-care bulk-purchase demand"
  and "large-print rising / +45% YoY" claims are **vendor-sourced hypotheses** (intake
  evidence refs F-002, F-006, F-017, F-024 marked `verified:false`). No sales figures,
  market size, or demand levels are asserted as verified. These inform direction, not the
  business case.

### Rights and originality commitments

Stated as commitments to be enforced and evidenced, not as clearances already granted.
`project.yaml` records `rights.originals_only: true` and `ai_assistance_disclosure_required: unknown`.

- Puzzle content **SHALL** be generated deterministically by code and independently
  verified by code (uniqueness, solvability, correct answer keys, difficulty accuracy).
- Sudoku uses digits 1–9 only; **no third-party word list or reference data** is required,
  so there is no external word-list rights dependency to clear for this product.
- Any interior or cover art **SHALL** be original and carry an originality attestation in
  the rights ledger before the interior gate; none is committed by this brief.
- **AI-assistance disclosure requirement is currently `unknown`** in `project.yaml` and
  must be resolved before the compliance gate. Not asserted here as either required or not.
- Fonts and any other assets must be rights-cleared and recorded in the rights ledger at
  the relevant gate. This brief does not assert font or asset clearance.

## 9. Open human decisions (required before niche-gate lock)

1. **Confirm content-volume + page budget:** accept advisory 100 puzzles / ~110 pages as the
   planning target, or set alternatives.
2. **Confirm format scope:** keep `paperback` only, or add digital-PDF / other editions.
3. **Series creation decision:** create the `senior-large-print` series now (this = volume 1)
   via `/product-series-new`, or defer.
4. **Confirm channel intent + Etsy fulfilment:** confirm `kdp` + `etsy`; resolve how a
   paperback-only product is fulfilled on Etsy (or drop Etsy for this edition).
5. **Resolve AI-assistance disclosure requirement** (`unknown` in `project.yaml`) before compliance.

## 10. Consistency check

The niche-opportunity/pipeline context (`notes/intake.md`), the resolved design policy
(`project.yaml` `production.design`), and this brief agree on: audience band
`senior-large-print`; product family `puzzle-book`; channels `kdp` + `etsy`; format
`paperback`; trim `8.5x11`; B&W high-contrast interior; progressive/back-only pedagogy.
No cross-source discrepancy found.

## 11. Niche-gate submission note (prepared, not submitted)

- **Gate:** `niche` (human-gated; no approval inferred or granted).
- **Supporting evidence:** `notes/intake.md`; `project.yaml` (`production.design`);
  `.claude/config/age_bands.json`.
- **Gate question posed to the approver:** Is this niche/positioning validated enough to
  lock the brief and advance to niche assessment, given that the demand claims (F-002,
  F-006, F-017, F-024) are vendor-sourced and unverified, and that content-volume, page
  budget, format scope, series creation, and Etsy fulfilment remain open human decisions?
- Artifact registration and gate-packet assembly are performed by the appropriate skill/agent,
  not by this brief. Hashes are recorded at registration time.
