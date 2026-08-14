# Intake — Easy Sudoku for Adults: Relaxing Puzzles with Full Solutions

**Project ID:** `clr-2026-easy-sudoku-for-adults-relaxing-puzzles-with-ful`
**State:** DISCOVERY · **Edition:** 1 · **Created:** 2026-08-14

## Supplied arguments (human-input points)

- Source: research pipeline `sudoku-puzzles`, candidate `adult-easy` (priority 1, confidence high)
- Topic / working title: "Easy Sudoku for Adults: Relaxing Puzzles with Full Solutions"
- Audience band: `adult-general`
- Product type: `puzzle-book`
- Formats: `paperback`, `digital-pdf`

## Engine-derived design policy (deterministic — not human-picked)

Source: `publishing_house.design_policy.derive_design` · config `.claude/config/design_policy.json` + `.claude/config/age_bands.json`

- **Trim size:** `8.5x11` (recommended); candidates `8.5x11`, `6x9`, `7x10`
  - Rationale: `audience:adult-general`
- **Colour interior:** `false` (black-and-white print interior; digital may be colour)
  - Rationale: adult-general puzzle/journal — B&W interior standard, colour only where it carries meaning
- **Tone register:** neutral · **Visual density:** medium (`book_type:puzzle-book`)
- **Emotional-intensity ceiling:** moderate
- **Pedagogy:** progressive (grids lead; difficulty front-to-back; solutions back-only)
- **Reading level:** adult-general (age_min 18); sentence target 8–26 words
- **Binding hint:** paperback · **Paper hint:** white

## Legal / rights defaults (pre-filled DEFAULTS — not clearances)

`production.legal_defaults` seeded from company config: AI-disclosure text, rights posture
(line art original-only; fonts licensed; word lists original/public-domain;
`default_asset_rights_status = unknown-blocks-release`), originality-attestation template,
release-scope defaults (US; kdp/etsy; prepare-package + dry-run only; max spend 0),
child-safety policy. **Edit per project in `project.yaml` if needed.** These are defaults the
human confirms as deltas at the compliance and release gates — not approvals.

## Six human gate points

1. **niche** approval · 2. **interior** approval · 3. **cover** approval ·
4. **compliance** approval (human-only) · 5. **listing** approval · 6. **release** authorization (human-only, 2 approvers)

## Pipeline-sourced context (advisory — NOT human-committed craft values)

All items below are advisory inputs for later stages, not approved craft values.

- **Difficulty** (conf high): tier `easy`, spread "single-tier easy" [F-001, F-009]
- **Puzzle count target:** 200 (advisory) [F-001]
- **Page budget target:** 150 (advisory) [F-007]
- **Trim preference:** `6x9` (advisory) — NOTE: engine derived `8.5x11` as recommended; engine is authoritative (rule 20). 6x9 is in the candidate set. [F-007]
- **Interior style notes:** clean high-contrast grids, back-only answer key with numbered puzzles [advisory]
- **Positioning:** entry point of a difficulty-tiered series; low-competition tail via 'easy/relaxing' framing [F-009, F-016]
- **SEO** (conf med): title pattern "Easy Sudoku for Adults: [N] Puzzles to [Benefit]"; keywords "easy sudoku for beginners", "sudoku puzzle book for adults", "sudoku with solutions"; category Humor & Entertainment > Puzzles & Games > Sudoku [F-011, F-012]
- **Series grouping:** `is_series = true`, slug `adult-difficulty-tier`, position 1 of Easy/Medium/Hard/Expert
- **Evidence refs:** F-001, F-009, F-011, F-012, F-007, F-016
- **Open questions:** Confirm live BSR/price via manual Amazon tier before committing price band (surfaces at listing gate).

## Decisions still required from the human

- Confirm/edit trim (engine `8.5x11` vs pipeline `6x9` preference) via a recorded revision if a change is wanted.
- Confirm objectives, constraints, and content-plan counts at the niche/brief stage.
- All six human gates above.
- Price band (open question) — deferred to listing gate.

## Next valid action

Run `product-plan` / `product-run` for the deterministic next step from `DISCOVERY`.
If pursuing the difficulty-tiered set, consider `/product-series-new` (series is advisory, not auto-created).
