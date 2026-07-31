# Intake Note — clr-2026-large-print-sudoku-for-seniors-easy-puzzles-with

**Created:** 2026-07-31 · **Lifecycle state:** DISCOVERY · **Source:** pipeline (`/research` category `sudoku-puzzles`, PRODUCT_ID `senior-large-print-easy`)

## 1. Supplied arguments (human-input points)

These are the only human-committed inputs. All craft values below are engine-derived, not human-picked.

| Input | Value |
|---|---|
| Topic | large print sudoku for seniors, easy puzzles with solutions |
| Audience band | `senior-large-print` |
| Product type | `puzzle-book` |
| Formats | `paperback` |
| Working title | Large Print Sudoku for Seniors: Easy Puzzles with Solutions |

## 2. Engine-derived design policy (deterministic — no human picks these per product)

Derived by `publishing_house.design_policy.derive_design` from `audience` + `book_type` + numeric age band. Source config: `.claude/config/design_policy.json`, `.claude/config/age_bands.json`. Recorded under `production.design` in `project.yaml`.

| Derived field | Value | Provenance / rationale |
|---|---|---|
| Trim size | `8.5x11` (candidates: `8.5x11`, `8x10`) | `audience:senior-large-print` — large grids/type |
| Colour interior | `false` (black-and-white high-contrast) | `audience:senior-large-print` — colour avoided to preserve contrast |
| Colour policy | print interior text = black-and-white-high-contrast; images = black-and-white | single-sourced from `default_colour_policy` |
| Tone register | `calm-clear` | `audience:senior-large-print` |
| Reading level | band `senior-large-print`, age_min 55; body type ≥ 16pt; sentences 6–18 words | age band profile |
| Visual density | `medium` | `book_type:puzzle-book` |
| Emotional intensity ceiling | `gentle` | `audience:senior-large-print` |
| Pedagogy approach | `progressive` (difficulty front-to-back, solutions back-only) | `book_type:puzzle-book` |
| Binding hint | `paperback` | `audience:senior-large-print` |
| Paper hint | `white` | `audience:senior-large-print` |

Accessibility guidance (from band profile): large-print type (≥16pt body) and oversized grids; high contrast, avoid low-contrast greys and thin rules; one puzzle per page with ample white space; simple, unambiguous instructions.

## 3. Pipeline-sourced context (advisory — NOT human-committed craft values)

The following come from the `/research` pipeline entry. They are **advisory inputs for later stages only**, not approved craft values. Each is labelled with confidence and evidence ref. Any concrete count/difficulty must be re-derived and code-verified before use in metadata or listings.

- **Difficulty:** tier `easy`, spread "easy, forgiving" — advisory (pipeline). Evidence: F-002, F-024 (large-print rising; +45% YoY figure unverified).
- **Puzzle count target:** 100 — advisory only (pipeline). Not a committed content count; content plan sets this at brief/plan stage.
- **Page budget target:** ~110 pages — advisory only (pipeline).
- **Trim preference:** `8.5x11` — advisory (pipeline, confidence med, F-007); consistent with engine-derived trim above.
- **Positioning:** "High-contrast, oversized-grid large print; senior-care bulk-purchase demand cited." Evidence: F-006 (med) — bulk-purchase claim is an *unverified* vendor assertion.
- **Interior style notes:** senior-large-print band requires high contrast and oversized grids per house rules (advisory).
- **SEO title pattern:** "Large Print Sudoku Puzzle Book for Seniors: [N] Puzzles with Solutions" (F-011, med). `[N]` must equal a code-verified puzzle count before use.
- **SEO keyword ideas:** "large print sudoku for seniors", "brain games for seniors", "sudoku with solutions" (F-012, med) — generic, rights-safe; validate against channel tag limits at listing.
- **SEO categories:** "Humor & Entertainment > Puzzles & Games > Sudoku" (advisory).
- **Series grouping:** `is_series = true`, series_slug `senior-large-print`, position 1, set "Easy/Medium large print" (advisory). See §6 next steps.
- **Evidence refs:** F-002, F-005, F-006, F-007, F-011, F-012, F-017, F-024. Several are `verified:false` / vendor-sourced — treat direction, not exact figures, as reliable.
- **Open questions (pipeline):** Confirm accessibility gate contrast/type-size targets at project init. → Engine has set ≥16pt body and oversized-grid/high-contrast targets; the accessibility gate will formally verify these before compliance.

## 4. Six human gate points (none granted; cannot be inferred)

1. **Niche approval** — validates the opportunity/positioning before brief lock.
2. **Interior approval** — approves interior content + layout (and originality attestation for any art).
3. **Cover approval** — approves the cover design.
4. **Compliance approval** — AI-disclosure, accessibility (must PASS/WARNING), rights, child-safety, channel policy.
5. **Listing approval** — approves listing/metadata copy.
6. **Release approval** — authorizes release; requires **2 distinct approvers** and exact-hash binding.

Each requires an explicit `/approve-*`, `/content-freeze`, or `/release-authorize` invocation bound to exact artifact hashes. No approval is implied by this note.

## 5. Decisions still required from the human

- Confirm the advisory puzzle count (100) and page budget (~110) as the planning target, or set alternatives.
- Confirm formats stay `paperback` only (pipeline declared paperback; no digital-pdf added).
- Decide whether to create the series (`senior-large-print`, this = volume 1) now or later — see §6.
- Provide/confirm channel intent (project init recorded `kdp`, `etsy` as default sales_channels).

## 6. Next valid action

- Deterministic next step (`project plan`): stage **DISCOVERY → NICHE_ASSESSMENT**, autonomy `PROCEED` (non-gate). Recommended skill: `product-brief`; agents: `market-scout`, `acquisitions-editor`.
- Typical command: `/product-run <id>` (bounded autonomous advance, halting at the niche human gate) or `/product-plan <id>`.
- **Series:** the pipeline entry marks this as a series (position 1). Consider `/product-series-new` to create the `senior-large-print` series manifest. Not auto-created.

Pipeline entry `sudoku-puzzles / senior-large-print-easy` has been flipped to `promoted` with this project id recorded.
