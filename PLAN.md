# Implementation Plan — Puzzle / Coloring / Journal / Printable Publishing House (`pub-clr`)

## Source references

This plan is derived from two source sets. Section headings below cite the specific files they draw from.

**Research docs** (`/Users/qaiser.abbas/Dev/my-repos/pub-clr/research/`):
- `2-mega-coloring-book.md` — 4 product families, coloring IP architecture, 13-phase pipeline, 6 gates, standards list.
- `3-mega-puzzle.md` — "code generates, code verifies" principle, puzzle-empire directory, 6 gates, acceptance criteria.
- `3b-KDP-12-Puzzle-Types.md` — 12 puzzle types with market data, per-type generators/validators, specialist agents, bold-and-easy param table, mixed-book category, catalog roadmap.
- `3c-KDP-Puzzle-Book-Publishing-Workflow.md` — 10-step KDP workflow, page-count/PDF export specs, proof-copy QC checklist, 90-day launch plan, 7 validation gates.

**Reference framework** (`/Users/qaiser.abbas/Dev/my-repos/bk-pub/`):
- `.claude/CLAUDE.md` — constitution structure to mirror.
- `.claude/config/workflow_states.json`, `quality_gates.json`, `age_bands.json` — config patterns.
- `.claude/scripts/publishing_house/*` — Python backbone (design_policy.py, project.py, state.py, cli.py, paths.py, util.py, etc.).
- `.claude/agents/**`, `.claude/skills/**` — agent/skill contract formats.
- `.claude/hooks/**`, `.claude/patterns/**`, `.claude/rules/**`, `.claude/schemas/**`, `.claude/standards/**`, `.claude/workflows/**` — layer patterns.
- `FRAMEWORK_MANIFEST.md`, `FRAMEWORK_INVENTORY.json`, `ARCHITECTURE.md`, `OPERATOR_GUIDE.md` — top-level doc patterns.

## 0. Architecture decision (recommendation)

**Build `pub-clr` as a STANDALONE framework that clones `bk-pub`'s architecture — do NOT merge into `bk-pub`.**

Rationale (objective):
- `bk-pub` is a prose/narrative pipeline centered on research → drafting → fact-checking → multi-review → revision, with claim-source graphs, continuity managers, and factuality auditors. Puzzle/coloring/journal/printable production replaces that entire content core with **deterministic algorithmic generation + code verification** (puzzles), **original line-art generation + visual QA** (coloring), and **structured prompt/section architecture** (journals/printables).
- The lifecycle state machines barely overlap in the middle. Merging forces conditional branching per product family across every state, gate, quality dimension, and agent — doubling `bk-pub`'s surface area and destabilizing a working 285-file system.
- The research docs themselves assume a separate framework.
- Digital printables are Etsy/Gumroad-native (not KDP); puzzle books need a physical proof-copy QC gate `bk-pub` doesn't have.

**What is reused (by cloning the pattern, not importing):** the deterministic Python backbone (`ph_cli.py` + `publishing_house/` package), SHA-256 artifact-integrity model, human-gate enforcement, hooks, schema-driven validation, patterns library, rights/compliance posture, and the metadata/pricing/marketing/listing layer.

A separate `BK_PUB_ENHANCEMENTS.md` will capture the small set of genuinely reusable improvements to flow back into `bk-pub`.

---

## 1. Product families & domain model

_Source: `research/2-mega-coloring-book.md` (family taxonomy A–D), `research/3b-KDP-12-Puzzle-Types.md` (12-type table)._

Four product families, routed by a `product-family-classifier`:

- **A. Puzzle & activity books** — 12 KDP types (sudoku, word search, crossword, mazes, logic/Kakuro/KenKen, dot-to-dot, cryptograms, picture/spot-the-difference, fill-in, jumbles, number search, coloring-hybrid). Code-generated + code-verified.
- **B. Coloring books** — bold & easy, grayscale, kids, large-print/senior, themed. Original AI line-art only + vectorization + visual QA + closed-region/line-weight validation.
- **C. Guided journals & workbooks** — gratitude, habit trackers, recovery, caregiver logs; structured prompt/section architecture with duplicate-prompt checking.
- **D. Digital printables & templates** — Etsy/Gumroad-native planners, Canva packs, hyperlinked GoodNotes PDFs.

`product_type` (top-level) drives the state machine variant; `book_type` (sub-type) drives the design-policy engine.

---

## 2. Target directory layout (`pub-clr/.claude/`)

_Source: `bk-pub/.claude/` layout (agents, config, hooks, mcp, patterns, rules, schemas, scripts, skills, standards, templates, workflows); research directory proposals in `research/2-mega-coloring-book.md` and `research/3-mega-puzzle.md`._

Mirrors `bk-pub` structure, domain-adapted. `pub-clr/.claude/settings.json` already exists and is correct (points at `ph_cli.py`, Sydney TZ, external writes disabled) — reused as-is.

```
.claude/
├── CLAUDE.md                     # constitution, rewritten for this domain
├── README.md
├── settings.json                 # EXISTS — keep
├── settings.local.example.json   # EXISTS — keep
├── agents/                       # ~22 agents (see §4)
├── commands/                     # short slash aliases (see §7)
├── config/
│   ├── product_families.json     # A/B/C/D definitions + classifier hints
│   ├── puzzle_types.json         # 12 types: market data, generator, validator, agent, price tier
│   ├── difficulty_bands.json     # beginner/easy/medium/hard/expert curves per type
│   ├── age_bands.json            # kids / teen / adult / senior-large-print
│   ├── design_policy.json        # trim/margins/bleed/font per product_type + book_type
│   ├── bold_and_easy_specs.json  # per-type font/grid/path params (doc 3b table)
│   ├── quality_gates.json        # domain dimensions (see §6)
│   ├── workflow_states.json      # per-product-family state variants (see §5)
│   ├── formats.json              # KDP paperback / PDF / Etsy digital / Gumroad
│   └── platforms/                # kdp.json, etsy.json, gumroad.json, ebay.json
├── hooks/                        # cloned from bk-pub (session_start, pre_tool_policy,
│                                 #   post_tool_audit, subagent_event, stop_audit, hooklib)
├── mcp/                          # read-mostly server adapted to this domain
├── patterns/                     # cloned + 2 new (code-verify-loop, originals-only)
├── rules/                        # renumbered + domain rules (see §8)
├── schemas/                      # cloned reusable + new domain schemas (see §9)
├── scripts/
│   ├── ph_cli.py                 # entry point (cloned)
│   └── publishing_house/         # Python package (see §3)
├── skills/                       # ~40 skills (see §7)
├── standards/                    # contracts + templates (see §10)
├── templates/                    # project/brief/puzzle-spec/etc starter files
└── workflows/                    # JS fan-out/fan-in (see §11)
```

Top-level docs (like `bk-pub`): `README.md`, `ARCHITECTURE.md`, `OPERATOR_GUIDE.md`, `EXTENSION_GUIDE.md`, `PLATFORM_ADAPTERS.md`, `FRAMEWORK_MANIFEST.md`, `FRAMEWORK_INVENTORY.json`, `SECURITY.md`, `pyproject.toml`, `requirements.txt`, `.mcp.json`, `.env.example`, `Makefile`, `catalog/products.json`, `projects/.gitkeep`, `tests/`.

---

## 3. Python backend (`publishing_house/` package)

_Source: `bk-pub/.claude/scripts/publishing_house/*` (cloned modules); `research/3-mega-puzzle.md` + `research/3b-KDP-12-Puzzle-Types.md` (generator/validator lists, "code verifies" rule); `research/3c-KDP-Puzzle-Book-Publishing-Workflow.md` (PDF export spec, even-page rule, back-only solutions, spine-width math)._

**Cloned largely unchanged from `bk-pub`:** `util.py`, `errors.py`, `paths.py` (adapt project-id prefix), `state.py`, `artifacts.py`, `approvals.py`, `events.py`, `quality.py`, `rights.py`, `planner.py`, `catalog.py`, `gate_packet.py`, `doctor.py`, `validation.py`, `metadata_audit.py`, `packages.py`, `submission.py`, `series.py`, `cli.py` (adapt subcommands), `markdown.py`.

**Adapted:** `project.py` (project-id `clr-<year>-<slug>`; product_type field; design derivation), `design_policy.py` (new book_type overrides: puzzle/coloring/journal/planner/printable; trim defaults 8.5x11, grayscale-interior default for puzzles, always-color for coloring covers).

**New domain modules:**
- `generators/` package:
  - `sudoku_gen.py`, `wordsearch_gen.py`, `numbersearch_gen.py`, `maze_gen.py`, `crossword_gen.py`, `logic_puzzle_gen.py` (Kakuro/KenKen), `dot_to_dot_gen.py`, `cryptogram_gen.py`, `picture_puzzle_gen.py`, `fillin_gen.py`, `jumble_gen.py`
  - `journal_prompt_gen.py`, `tracker_grid_gen.py`, `calendar_gen.py`
  - `line_art_prompt_builder.py` (builds original-art prompts; NO scraping)
- `validators/` package:
  - `sudoku_uniqueness_check.py`, `wordsearch_solvability_check.py`, `crossword_grid_check.py`, `maze_solvability_check.py`, `dot_to_dot_clarity_check.py`, `cryptogram_decode_check.py`, `picture_puzzle_diff_check.py`, `jumble_uniqueness_check.py`
  - `duplicate_check.py` (cross-catalog puzzle dedupe), `print_spec_check.py` (per-type trim/DPI/bleed/font), `line_weight_check.py`, `closed_region_check.py`, `prompt_duplicate_check.py`, `font_size_accessibility_check.py`
- `layout/` package:
  - `pdf_interior_builder.py` (ReportLab; even-page enforcement, back-only solutions, front matter), `cover_builder.py` (spine width from page count, KDP calculator math), `digital_planner_linker.py` (hyperlinked tabs)
- `proof.py` — proof-copy QC checklist state (new gate)

**Tool-boundary principle preserved:** Claude does judgment/theming/copy; Python does generation, verification, hashing, state, builds. Every generator has a matching validator; a puzzle is never "done" until its validator passes (independently re-solves for uniqueness).

---

## 4. Agents (~22, in departments)

_Source: `bk-pub/.claude/agents/**` (department layout + agent contract, e.g. `editorial/book-architect.md`); `research/3b-KDP-12-Puzzle-Types.md` (specialist agents: clue-quality-agent, quote-clearance-agent, image-diff-agent, hybrid-balance-agent); `research/3-mega-puzzle.md` (QA agent must never be the generating pass)._


- **executive/**: `publisher-in-chief` (orchestrator), `portfolio-project-manager`, `human-collaboration-facilitator`
- **discovery/**: `niche-research-analyst` (stacking formula: type×theme×audience; BSR/review-density validation, avoid-list), `market-competitive-analyst`, `product-family-classifier`, `catalog-roadmap-strategist`
- **content/**: `puzzle-designer` (selects type/difficulty curve, drives generators), `coloring-art-director` (original line-art briefs, style), `journal-architect` (prompt/section flow), `printable-template-designer` (planners/Canva/GoodNotes)
- **quality/**: `puzzle-qa-auditor` (independent — never the generating pass; consumes validator output), `visual-qa-reviewer` (line weight, closed regions, legibility), `content-qa-reviewer` (prompt uniqueness, progression), `clue-quality-agent` (crossword), `image-diff-agent` (picture puzzles), `hybrid-balance-agent` (mixed books), `independent-red-team-final-auditor`
- **compliance/**: `compliance-officer` (AI disclosure, platform policy), `ip-clearance-officer` (originals-only, trademark), `quote-clearance-agent` (cryptograms), `accessibility-claims-reviewer` (ties "large print" claims to measured output)
- **production/**: `interior-layout-engineer`, `cover-designer`, `proof-qc-inspector`
- **commercial/**: `title-seo-metadata-strategist`, `pricing-strategy-manager`, `marketing-content-manager`, `post-launch-analytics-specialist`

Each agent follows `bk-pub`'s exact contract: YAML frontmatter (name, description, effort, tools, skills, memory, background, color) + Mission / Invoke when / Inputs / Outputs / Procedure / Quality rubric (0–5) / Prohibited / Escalate / Completion contract.

---

## 5. Workflow states (per product family)

_Source: `bk-pub/.claude/config/workflow_states.json` (state-machine + human_gate_to_state pattern); `research/2-mega-coloring-book.md` + `research/3-mega-puzzle.md` (6 human gates); `research/3c-KDP-Puzzle-Book-Publishing-Workflow.md` (proof-copy QC as a hard gate, Etsy/Gumroad digital path)._

`workflow_states.json` keeps `bk-pub`'s discovery/gate/release scaffolding but swaps the content core. Shared human gates preserved as SCREAMING_SNAKE states.

Core sequence (puzzle/coloring variant):
```
DISCOVERY → CONCEPT_AND_NICHE → NICHE_APPROVAL(gate1)
→ CONTENT_GENERATION → SOLVABILITY_VERIFICATION (puzzles) / VISUAL_QA (coloring) / CONTENT_QA (journals)
→ INTERIOR_LAYOUT → INTERIOR_QA_APPROVAL(gate2)
→ COVER_DESIGN → COVER_APPROVAL(gate3)
→ COMPLIANCE_CLEARANCE → COMPLIANCE_APPROVAL(gate4)
→ METADATA_AND_PRICING → LISTING_APPROVAL(gate5)
→ PROOF_COPY_QC  (physical, KDP paperback only)
→ PLATFORM_PACKAGING → RELEASE_AUTHORIZATION
→ READY_FOR_SUBMISSION → SUBMISSION → PUBLISHED → MONITORING
+ MARKETING_POLICY_APPROVAL(gate6) → post-launch
+ PAUSED / CANCELLED / ERROR
```

Six human gates (from research, mapped to states): niche, interior QA, cover, compliance, listing/pricing, marketing/post-launch. Digital-printables variant skips PROOF_COPY_QC and routes packaging to Etsy/Gumroad adapters.

---

## 6. Quality gate dimensions (`quality_gates.json`)

_Source: `bk-pub/.claude/config/quality_gates.json` (dimension list, thresholds, revision caps); `research/3-mega-puzzle.md` (solvability/uniqueness), `research/3b-KDP-12-Puzzle-Types.md` (difficulty calibration, duplicate-freedom), `research/2-mega-coloring-book.md` (accessibility claims tied to validators)._

Replace `bk-pub`'s factuality/pedagogy/continuity with domain dimensions:
`solvability`, `uniqueness`, `difficulty_calibration`, `duplicate_freedom`, `legibility_print`, `line_art_quality`, `closed_region_integrity`, `prompt_uniqueness`, `logical_progression`, `audience_fit`, `accessibility_claims`, `ip_clearance`, `ai_disclosure`, `production_readiness`, `metadata_quality`, `commercial_integrity`, `originality`.
Critical dimensions (min 4.5): `solvability`, `uniqueness`, `ip_clearance`, `accessibility_claims`. Same 0 blockers / 0 majors / weighted-overall thresholds and revision-cycle caps as `bk-pub`.

---

## 7. Skills (~40) & commands

_Source: `bk-pub/.claude/skills/**` (SKILL.md contract, e.g. `book-new/SKILL.md`; human-only `disable-model-invocation` pattern) and `bk-pub/.claude/commands/**`; `research/3b-KDP-12-Puzzle-Types.md` (per-type + `/build-mixed-book` + `/apply-bold-and-easy` commands)._

**Lifecycle skills** (mirroring `book-*` → `product-*`): `product-doctor`, `product-new`, `product-classify`, `niche-research`, `concept-workshop`, `approve-niche`(human), `generate-puzzles`, `generate-coloring`, `generate-journal`, `generate-printable`, `verify-solvability`, `visual-qa`, `content-qa`, `interior-layout`, `approve-interior`(human), `cover-design`, `approve-cover`(human), `compliance-check`, `ip-clearance`, `quote-clearance`, `accessibility-check`, `approve-compliance`(human), `metadata-seo`, `pricing`, `approve-listing`(human), `proof-qc`, `package-kdp`, `package-etsy`, `package-gumroad`, `release-authorize`(human), `submit`(human), `marketing-kit`, `approve-marketing`(human), `analytics`, `status`, `run`(bounded autonomous), `resume`, `standards-refresh`, `delete-project`.

**Per-type generator skills / commands**: `/generate-sudoku`, `/generate-wordsearch`, `/generate-crossword`, `/generate-maze`, `/generate-logic-puzzle`, `/generate-dot-to-dot`, `/generate-cryptogram`, `/generate-picture-puzzle`, `/generate-numbersearch`, `/build-mixed-book`, `/apply-bold-and-easy`.

Each generator command calls generator + validator in sequence and refuses to report success until the validator passes. Human-only skills carry `disable-model-invocation: true`.

---

## 8. Rules (path-aware policy `.md`)

_Source: `bk-pub/.claude/rules/**` (numbered policy rules 00–21); domain rules from `research/3-mega-puzzle.md` (code-verify), `research/2-mega-coloring-book.md` (originals-only, accessibility claims), `research/3b-KDP-12-Puzzle-Types.md` (quote clearance), `research/3c-KDP-Puzzle-Book-Publishing-Workflow.md` (print/layout)._

Clone governance/workflow-state/approval/artifact/security/python/metadata/marketing rules; add domain rules:
- `puzzle-generation.md` (code-generates-code-verifies; never freehand a grid)
- `originals-only-art.md` (no tracing/deriving copyrighted images or characters)
- `accessibility-claims.md` (every "large print"/"dementia-friendly" claim enforced by validator, not asserted)
- `print-and-layout.md` (even pages, back-only solutions, per-type font floors)
- `quote-clearance.md`, `platform-kdp.md`, `platform-etsy.md`, `platform-gumroad.md`, `ai-disclosure.md`.

---

## 9. Schemas (JSON Schema 2020-12, `additionalProperties:false`)

_Source: `bk-pub/.claude/schemas/**` (reused schemas + JSON Schema 2020-12 conventions); new domain schemas from `research/3-mega-puzzle.md` + `research/3b-KDP-12-Puzzle-Types.md` (puzzle-spec/solution/solvability), `research/2-mega-coloring-book.md` (coloring/journal/printable specs), `research/3c-KDP-Puzzle-Book-Publishing-Workflow.md` (proof-qc-report)._

Reuse: state, artifact, approval, release-authorization, review, finding, source-record, rights-record, metadata, platform-package, quality-gate, event, marketing-plan.
New: `product-brief.schema.json`, `niche-analysis.schema.json`, `puzzle-spec.schema.json`, `puzzle-solution.schema.json`, `solvability-report.schema.json`, `coloring-page-brief.schema.json`, `visual-qa-report.schema.json`, `journal-structure.schema.json`, `printable-spec.schema.json`, `design-record.schema.json`, `proof-qc-report.schema.json`, `bold-and-easy-spec.schema.json`, `compliance-report.schema.json`.

---

## 10. Standards & templates

_Source: `bk-pub/.claude/standards/**` (contracts + template files); standards lists in `research/2-mega-coloring-book.md` and `research/3-mega-puzzle.md` (puzzle-quality, coloring-line-art, print-and-layout, brand-style, compliance checklists); `research/3b-KDP-12-Puzzle-Types.md` (bold-and-easy-specs)._

Contracts: agent, review, artifact, approval, rights, metadata, release, marketing (cloned) + `puzzle-quality-standards.md`, `coloring-line-art-standards.md`, `content-structure-standards.md`, `print-and-layout-standards.md`, `bold-and-easy-specs.md`, `brand-style-guide.md`, and compliance checklists (ai-disclosure, ip/source-art, accessibility-claims, platform-policy, quote-clearance, review-solicitation), each with a "verify against current platform policy" note.
Templates: `project.yaml`, `product-brief.yaml`, `niche-analysis.yaml`, `puzzle-spec.yaml`, `coloring-brief.yaml`, `journal-structure.yaml`, `printable-spec.yaml`, `review.json`, `finding.json`, `approval.json`, `rights-record.json`, `metadata.json`, `proof-checklist.md`.

---

## 11. Workflows (JS fan-out/fan-in)

_Source: `bk-pub/.claude/workflows/**` (fan-out/fan-in `agent()`/`pipeline()` pattern, gate-stopping autonomous loop); `research/3b-KDP-12-Puzzle-Types.md` (mixed-book balance, crossword clue review)._

Clone the pattern; domain variants: `autonomous-run-loop.js` (gate-stopping), `niche-opportunity-scan.js`, `puzzle-playtest-review.js` (per-type solvability + difficulty fan-out), `coloring-visual-review.js` (per-page QA), `content-multi-review.js`, `crossword-clue-review.js`, `mixed-book-balance.js`, `final-red-team.js`, `title-selection.js`, `metadata-channel-audit.js`, `marketing-asset-fanout.js`, `compliance-fanout.js`.

---

## 12. Build order (execution phases)

1. **Scaffold**: directories, `.mcp.json`, `pyproject.toml`, `requirements.txt`, `.env.example`, `Makefile`, `catalog/`, `projects/.gitkeep`.
2. **Python core (clone+adapt)**: `util, errors, paths, state, artifacts, approvals, events, quality, rights, planner, validation, catalog, gate_packet, doctor, project, design_policy, cli, ph_cli`.
3. **Config**: all `config/*.json` (states, quality_gates, puzzle_types, difficulty_bands, age_bands, design_policy, bold_and_easy_specs, product_families, formats, platforms/*).
4. **Schemas** (all §9).
5. **Generators + validators** (all §3) — the load-bearing "code verifies" core. Real, working algorithms.
6. **Layout builders**: `pdf_interior_builder`, `cover_builder`, `digital_planner_linker`, `proof`.
7. **Hooks** (clone), **MCP server** (adapt), **patterns**, **rules**, **standards**, **templates**.
8. **Agents** (all §4).
9. **Skills + commands** (all §7).
10. **Workflows** (§11).
11. **Top-level docs** + `FRAMEWORK_MANIFEST.md` / `FRAMEWORK_INVENTORY.json`.
12. **Tests**: unit tests for each generator's validator (e.g. sudoku uniqueness, word-search word-presence, maze solvability, duplicate detection, even-page enforcement, line-weight/closed-region for a sample SVG). Run `python3 .claude/scripts/ph_cli.py --help` and `doctor`; run a full dry-run project (`product-new` → generate → verify → layout → package) to prove end-to-end.
13. **`BK_PUB_ENHANCEMENTS.md`**: reusable improvements to flow back to `bk-pub` (e.g. proof-copy QC gate, per-type accessibility-claim validators, code-verify-loop pattern, product-family classifier concept).

---

## 13. Non-negotiable principles baked in (from research)

_Source: shared "Non-Negotiable Principles" sections in `research/2-mega-coloring-book.md` and `research/3-mega-puzzle.md`; `bk-pub/.claude/CLAUDE.md` §11 (external side effects)._

- Puzzles generated by code, independently verified by code before shipping (unique solution, difficulty fit, no duplicates).
- Original art/content only; no tracing/deriving copyrighted material.
- Every marketing/accessibility claim enforced by a validator, not asserted.
- Hard stop at every human gate; no autonomous continuation during gate review.
- Compliance is first-class; AI-disclosure checkbox is a standard pipeline step.
- Quality/differentiation over volume; steer away from the avoid-list.
- No fake/incentivized/review-swap tactics.
- External writes disabled by default; packaging only, no autonomous publish/spend.
- Build for reuse: a new title needs a new config, not new code.

---

## 14. Additional research artifacts to encode

- **Catalog build-order roadmap** (`research/3b-KDP-12-Puzzle-Types.md`): encode into `config/puzzle_types.json` + the `catalog-roadmap-strategist` agent — start Sudoku / Bold-&-Easy Word Search → themed word search + kids mazes → number search + cryptograms → crossword / logic / picture puzzles → fill-in/jumbles as bonus → mixed books after 5–10 titles. Stored as `docs/workflows/catalog-roadmap.md`.
- **90-day launch plan** (`research/3c-KDP-Puzzle-Book-Publishing-Workflow.md`): encode into the `marketing-content-manager` agent + `marketing-kit` skill — no ads until indexing (~5–10 days), publish 3 launch volumes together, $5–$10/day manual-targeted ads afterward, prune keywords < 0.5% CTR. Stored as `docs/workflows/launch-plan.md`.
- **Reference calibration examples** (`research/3c`): the 3 worked examples (senior word search, kids maze, adult sudoku) become fixtures in `tests/` and price/royalty defaults in `config/design_policy.json` + `platforms/kdp.json`.

---

## 15. Assumptions & open points

- Image generation for coloring line-art: the framework builds prompts + validates outputs, but actual image-model API wiring is left as a documented connector boundary (external write, disabled by default) unless you specify an API to integrate.
- Crossword clue generation quality is gated by `clue-quality-agent`; framework flags crossword as "advanced" and routes beginners to sudoku/word-search first.
- Exact platform rules (KDP/Etsy) are captured as checklists with "verify current policy" notes, not hardcoded law.
