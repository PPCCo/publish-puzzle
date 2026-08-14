# Series Implementation Plan — align the series layer with the product families

Status: PLAN (no code written yet)
Author: Framework design pass, 2026-08-12
Model discipline: all future skills/commands touched here pin Sonnet 5 or Haiku 4.5, never Opus.

## 1. Why this plan exists

The `/hi` router work surfaced that a puzzle book or coloring book should be able
to belong to a **series/set** (e.g. an easy → medium → hard Sudoku set, or
"Wild Wonders: My First Animal Library" across three coloring volumes). The
series layer already exists in code — but it was written for a **generic book
publisher** (fiction/nonfiction novels, audiobooks, epubs) and was **never
adapted to the puzzle/coloring/journal/printable product families** this repo
actually publishes.

So before the router can meaningfully answer `/hi series ...`, the series layer
must speak the same vocabulary as the product framework. This plan fixes that
mismatch and closes the integration gaps, **without weakening any per-product
human gate** (CLAUDE.md §5, rules 00/01/02).

## 2. What already works (do NOT rebuild)

`.claude/scripts/publishing_house/series.py` (544 lines) is substantially
complete and correct in shape:

- `init_series` — manifest-first, creates volume 1 by default.
- `add_book` — creates the planned volume at a position as its own project and
  writes a **bidirectional link** (manifest slot ↔ project `series` block).
- `link_book` — folds an existing standalone project into a slot.
- `list_series`, `series_status`, `series_milestone`, `sibling_context`.
- `sync_series_catalog` — **writes `catalog/series.json`** on every mutation
  (this is why the user referenced `@catalog/series.json`; it appears the moment
  the first series is created).
- Schema at `.claude/schemas/series.schema.json`, skill at
  `.claude/skills/product-series-new/SKILL.md` (pinned Sonnet 5 — good).
- CLI wired: `series init|list|status|add-book|link|context|milestone`.

The **linking model, gate independence, offline/deterministic contract, and
event logging are all correct.** Do not touch them beyond the enum/vocabulary
alignment and the integration hooks below.

## 3. The core defect: vocabulary mismatch

Two schemas describe the same real-world objects with **different, incompatible
enums**:

| Field | `project.schema.json` (product framework — CORRECT for this repo) | `series.schema.json` (grafted novel framework — WRONG here) |
|---|---|---|
| audience / band | `kids-4-8`, `kids-6-10`, `tween-8-12`, `teen-13-17`, `adult-general`, `senior-large-print` | `early-reader-6-8`, `middle-grade-9-12`, `teen-13-17`, `adult-general`, `adult-specialist` |
| product/book type | `puzzle-book`, `activity-book`, `coloring-book`, `guided-journal`, `workbook`, `planner`, `digital-printable` | `fiction`, `illustrated-fiction`, `nonfiction`, `picture-book`, `reference`, `encyclopedia`, `atlas`, `textbook`, `activity-book`, … |
| formats | `paperback`, `hardcover`, `digital-pdf` | `epub`, `fixed-layout-epub`, `paperback`, `hardcover`, `audiobook`, `read-along` |

`series.add_book()` passes the series-level `audience` / `book_type` / `formats`
straight into `init_project(...)`. Today, defaults are `book_type="nonfiction"`
and `formats=["epub"]` — **neither is a valid product-framework value**, so
creating a real puzzle/coloring volume through the series path would either be
rejected by `project.schema.json` or write a non-product project. This is the
gap that blocks "puzzles/coloring books as part of a series."

## 4. Changes (ordered, each independently testable)

### 4.1 Realign `series.schema.json` to the product vocabulary
- Replace the `audience` enum with the six product bands from
  `age_bands.json` profiles (single-source: derive/validate against that file so
  the two never drift again — mirror how `project` validates).
- Replace `book_type` with `product_type` (keep `book_type` as a deprecated
  alias for one release for backward compatibility) using the 7 product-family
  values from `project.schema.json`.
- Replace `formats` enum with `paperback`, `hardcover`, `digital-pdf`.
- Keep `position`, `working_title`, `topic`, `scope`, `assumes_prior_positions`,
  `shared_canon`, `progression` unchanged — they are family-agnostic and correct.
- Bump series schema to `schema_version: "1.1"`; keep a reader that accepts 1.0
  and migrates in memory (no destructive rewrite of an existing manifest).

### 4.2 Fix `series.py` defaults and pass-through
- `add_book`: default `product_type` from slot → manifest → **`"puzzle-book"`**
  (not `nonfiction`); default `formats` → **`["paperback"]`** (not `["epub"]`);
  default `audience` → manifest audience (already a valid product band after 4.1).
- Rename the internal `book_type` variable to `product_type` and pass it to
  `init_project` as `product_type=`. `init_project`'s signature in `project.py`
  uses `product_type` — confirm the call site matches (today `series.py` calls
  `init_project(..., book_type=resolved_type, ...)`; align to the real parameter
  name in `project.py`).
- Validate the manifest against the 1.1 schema; keep the existing
  `validate_file_data` gate on both the manifest and the child project.

### 4.3 CLI surface (`cli.py`)
- `series init` / `add-book`: rename `--book-type` → `--product-type` (accept
  `--book-type` as a hidden deprecated alias for one release), and constrain
  `choices=` to the product `PRODUCT_TYPES` list already defined in `cli.py`.
- `series init`: change `--audience` default from `middle-grade-9-12` to
  `adult-general` (a valid product band) and constrain choices to the six bands.
- No new top-level command needed.

### 4.4 Series-aware planner + status (integration the router needs)
Today `planner.py` and `project.py` are **series-blind** (`grep -c series
planner.py` → 0). Add read-only awareness so `/hi` and `project plan` can say
"next volume in the set":
- `project_status(...)`: when `project.yaml` has a `series` block, include a
  compact `series` summary (series_id, position, total_planned) in the status
  payload. Read-only; no new state.
- `plan_next(...)`: when a product reaches a terminal/near-terminal state
  (e.g. `RELEASE_AUTHORIZATION`+ or `PUBLISHED`) **and** it is in a series with
  an **uncreated next slot**, append an advisory `series_next` block:
  `{ series_id, next_position, next_working_title, suggested_command: "series add-book <id> --position N" }`.
  This is advisory only — it never auto-creates a volume and never bypasses a
  gate. Guarded so non-series projects are unaffected.
- Add a thin `series recommend <series-id>` CLI verb (wraps `series_status` +
  `series_milestone`) returning the single "next actionable volume" (first
  planned-but-uncreated slot, else the lowest-position created volume not yet at
  target state, with that volume's `plan_next`). The router calls this for
  `/hi series <id>` and `/hi series <topic>`.

### 4.5 Research → series bridge (a series as a research output)

A series is a natural **output of research**: a category research pass
(`research/pipeline/<category>/pipeline.json`) often produces a laddered set of
related products (e.g. easy → medium → hard Sudoku, or an animal-library across
volumes) that ship together. Support turning that backlog into a series plan —
**human-gated, never automatic.**

- **Read-only suggestion helper** (`series.py`): given a category, group its
  `pipeline.json` candidate entries into a proposed series plan (ordered by the
  recorded difficulty/progression, same audience/product family) and return a
  ready-to-run `series init --books-json <...>` payload. It **suggests only** —
  it does not create the series, does not promote pipeline entries, and does not
  mutate research state.
- **Promotion linkage.** When a human accepts the suggestion and runs the create
  flow, each volume created via `series add-book` should call the existing
  `research promote <category> --product-id … --project-id …` so the backlog
  entry is marked promoted and linked to the real project. Wire this as an
  explicit step in the skill (4.7), not as a silent side effect of `add_book`
  (keep `add_book` research-agnostic; the skill orchestrates the promotion).
- Guardrails: no network, no auto-create, research remains authoritative for its
  own promoted/candidate flags (rule 18 network carve-out untouched).

### 4.7 New skill: `product-series-add-book` (how a book joins a series)

`product-series-new` creates a series + volume 1. There is **no skill** for the
common "add the next volume" or "fold an existing product into a set" flows, or
for turning a research backlog into a series. Add one skill that documents and
drives all three, pinned to **Sonnet 5**
(`@bedrock-eus1/us.anthropic.claude-sonnet-5`), read/write + `ph_cli.py *` tools,
`user-invocable: true`. It performs no external writes and creates no gate.

Modes (parsed from `$ARGUMENTS`):

1. **Add a planned volume** — `--series-id <id> --position N`
   → `series add-book <id> --position N [--product-type … --audience … --formats …]`.
   Then surface the new volume's engine-derived design policy, confirm the
   bidirectional link (manifest slot ↔ project `series` block), read
   `series context <new-project-id>` so the volume knows what earlier volumes
   cover, and recommend the volume's `project plan` next step. Each volume keeps
   its own full six-gate sequence — say so explicitly.
2. **Fold in an existing product** — `--series-id <id> --position N --project-id <existing>`
   → `series link <id> --position N --project-id <existing>`. Verify the project
   is not already linked elsewhere; write only the link (never touch the
   product's state, freezes, or approvals).
3. **Create a series from research** — `--from-research <category>`
   → call the 4.5 suggestion helper, present the proposed volume plan to the
   human via AskUserQuestion (Recommended = the ordered ladder as-is; alternates
   = adjust count / audience), then on acceptance run `series init` and, per
   created volume, `research promote`. Stop and hand to `/product-series-new`
   if the human wants to review volume-1 design policy in depth.

Skill contract mirrors `product-series-new`: resolve ids before writing, never
invent approvals/prices/legal conclusions, stop on invalid state or stale
hashes, and emphasize that the series manifest links volumes but creates **no
series-level gate** that bypasses any volume's human gates (rule 02).

CLI note: expose a thin `series suggest-from-research <category>` verb (read-only)
that returns the proposed `--books-json` payload, so the skill and the `/hi`
router share one deterministic source.

### 4.6 Catalog schemas + product↔series cross-linking (requested)

Today both catalogs are **unvalidated and disconnected**:
- `products.json` = `{schema_version, products: list_projects()}` (built by
  `sync_catalog` in `project.py`); series-blind.
- `series.json` = `{schema_version, series: list_series()}` (built by
  `sync_series_catalog` in `series.py`); does not reference member projects
  beyond the project_id already inside each slot.
- Neither has a JSON Schema; nothing validates them before write.

Changes:
- **Add `.claude/schemas/products-catalog.schema.json`** and
  **`.claude/schemas/series-catalog.schema.json`** (2020-12). Validate each
  catalog against its schema inside `sync_catalog` / `sync_series_catalog`
  before the atomic write (rule 18: validate JSON before writing). Bump both
  catalogs to `schema_version "1.1"`.
- **Cross-link products → series.** In `sync_catalog`, for each product read its
  `project.yaml` `series` block (if any) and add a compact
  `series: { series_id, position, total_planned }` field to that product's
  catalog entry. Products not in a series omit the field. This lets the router
  answer "`/hi <series-id>` → which products are in it" directly from
  `products.json` (the user's example), and answer "is this product part of a
  set?" from a single product entry.
- **Cross-link series → products.** In `sync_series_catalog`, each series entry
  already exposes `created_books`; additionally surface a
  `member_project_ids: [...]` array (from the manifest slots) and a per-slot
  `{position, project_id|null, state|null}` roll-up so the router can render a
  series' membership + progress without opening every project.
- **Keep the two catalogs consistent.** Any mutation that creates/links a volume
  (`series add-book`, `series link`) already calls `sync_series_catalog`; also
  call `sync_catalog` in the same operations so `products.json` picks up the new
  `series` back-reference in the same transaction. Add a `catalog rebuild` path
  that regenerates BOTH catalogs (extend the existing `catalog rebuild` verb to
  rebuild products **and** series, then verify cross-links resolve both ways).
- **Referential-integrity check.** Add a read-only `catalog verify` CLI verb (or
  fold into `framework validate`) that asserts: every `member_project_ids` entry
  in `series.json` exists in `products.json`; every product `series.series_id`
  exists in `series.json`; positions are unique per series. The router surfaces
  any drift instead of guessing.

Tests: catalogs validate against their new schemas; a product in a series shows
the `series` field in `products.json`; a series shows resolved
`member_project_ids` in `series.json`; `catalog verify` fails loudly on a broken
link and passes on a consistent pair.

## 5. Explicitly OUT of scope (guardrails)

- No series-level niche/interior/cover/compliance/listing/release gate. Each
  volume keeps its own six human gates (CLAUDE.md §5, rule 02). `series_milestone`
  stays pure reporting.
- No cross-volume freeze or approval propagation.
- No network, no clock reads inside deterministic modules, no external writes.
- No destructive rewrite of an existing `series.yaml`; migrations are in-memory
  or additive.

## 6. Tests to add (rule 18 requires coverage for state/gates/generators)

1. `add_book` for each `product_type` produces a schema-valid child project with
   the correct product-band audience and product formats.
2. Series schema 1.1 rejects novel-only enums (`epub`, `nonfiction`,
   `middle-grade-9-12`) and accepts product enums.
3. 1.0 → 1.1 in-memory migration reads an old manifest without loss.
4. `plan_next` emits `series_next` only for in-series projects with an uncreated
   next slot, and never changes `all_forward_options` or blockers.
5. `series_milestone` still reports (never grants) after the changes.
6. `sync_series_catalog` writes a `catalog/series.json` whose entries carry the
   product audience/type vocabulary.
7. `series suggest-from-research <category>` returns a schema-valid
   `--books-json` payload from a fixture pipeline and mutates nothing (no
   promote, no series created).
8. The `product-series-add-book` skill's three modes each produce the expected
   CLI calls and never emit a transition/approve/freeze/external-write verb.

## 7. Sequencing

Do 4.1 → 4.2 → 4.3 first (makes series usable for products at all), verify with a
throwaway 2-volume Sudoku series in a scratch dir, then 4.6 (catalog schemas +
cross-links — the router reads these directly), then 4.4 (planner/status hooks),
then 4.7 (`product-series-add-book` skill — the add-book/link/from-research
flows), and 4.5 (research→series bridge, which the skill's mode 3 depends on).
The **`/hi` router plan depends on 4.4 and 4.6** for its `/hi <series-id>`
membership answers and "next volume" recommendation, and routes to the 4.7 skill
for add-book/link/from-research.
