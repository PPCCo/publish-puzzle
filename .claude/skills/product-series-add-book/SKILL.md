---
name: product-series-add-book
description: >-
  Add a volume to an existing product-series — create a planned slot as its own project, fold an existing project into a slot, or propose and build volumes from category research. Each volume keeps its own full six-gate sequence.
argument-hint: "--series-id <id> [--position N] | --project-id <id> | --from-research <category>"
user-invocable: true
effort: high
model: '@bedrock-eus1/us.anthropic.claude-sonnet-5'
allowed-tools:
  - Read
  - Write
  - Bash
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
---

# /product-series-add-book

## Goal

Add one or more volumes to an EXISTING product series. This skill covers three modes:

1. **Add a planned slot** — create the next planned volume as its own independent project and link it.
2. **Fold in an existing project** — attach a standalone project to a planned series slot.
3. **From research** — propose a series plan from a category's research backlog, let the human choose, then create the volumes and record the promotions.

Each volume created or linked is a fully independent project carrying its own complete lifecycle and its own six human gates (niche, interior, cover, compliance, listing, release). This skill NEVER creates a series-level gate, freeze, approval, or release that bypasses any volume's per-product human gates.

## Arguments

Use the invocation arguments as `$ARGUMENTS`. Determine the mode from the flags present:

- `--series-id <id>` with `--position N` (and optional `--product-type`, `--audience`, `--formats`) → **mode 1** (add planned slot).
- `--series-id <id>` with `--project-id <id>` and `--position N` → **mode 2** (fold in existing project via `series link`).
- `--from-research <category>` → **mode 3** (propose from research; may create a new series or add to an existing `--series-id`).

Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions. Resolve the series ID (and, for mode 2, the project ID) before changing any files.

## Entry criteria

- The named series already exists (`series/<series-id>/series.yaml`). Confirm with `series status <series-id>` before acting. For mode 3 with no existing series, the human first approves creating one via `/product-series-new`.
- For mode 1, the target position is a planned slot in the manifest that has no project yet.
- For mode 2, the project to fold in exists, is a real independent project, and its product_type/audience are compatible with the series plan.
- For mode 3, the category has a research pipeline (`research/pipeline/<category>/pipeline.json`) with candidate entries.
- No external channel credential or platform listing is required at this stage.

## Procedure

### Mode 1 — add a planned volume slot

1. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py series status <series-id>` and confirm the requested `--position` is a planned, still-uncreated slot.
2. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py series add-book <series-id> --position N` (pass through any `--product-type`, `--audience`, `--formats`, `--created-by` provided). This creates the volume as its own project under `projects/<id>/` and links it to the slot.
3. Read the new volume's `project.yaml` and `state.json`. Surface the engine-derived design policy (trim, colour policy, line-art density, visual density, pedagogy, age-appropriate constraints) exactly as `product-new` does.
4. Confirm the volume carries a `series` back-reference (series_id, position, total_planned, prior_project_ids).

### Mode 2 — fold in an existing project

1. Run `series status <series-id>` and confirm the `--position` slot is planned and uncreated.
2. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py series link <series-id> --position N --project-id <project-id>`.
3. Confirm the project now carries the `series` back-reference and the manifest slot now names the project. Do NOT modify any other content of the folded-in project; linking must not reset or advance its state.

### Mode 3 — propose and build from research

1. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py series suggest-from-research <category>`. This is READ-ONLY: it groups candidate pipeline entries into proposed series plans and returns ready-to-run `series init` payloads. It creates nothing and promotes nothing.
2. Present the proposed series (title, audience, product_type, and the ordered volume list with each `source_product_id`) to the human with **AskUserQuestion**. Offer the concrete choices: which proposed series to build (if more than one), and whether to create a new series or add these volumes to an existing `--series-id`. Do not proceed until the human selects.
3. Only after the human's explicit selection:
   - New series: hand the chosen `series_init_payload` to `/product-series-new` (or run `series init --title ... --premise ... --audience ... --product-type ... --books-json <array>`), stripping the non-schema `source_product_id` key from each book before passing `--books-json`.
   - Existing series: for each chosen volume, run `series add-book <series-id> --position N` with its product_type/audience.
4. For each created volume, record the research promotion: `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py research promote <category> --product-id <source_product_id> --project-id <created-project-id>`. Promotion is backlog bookkeeping only — it flips the pipeline entry to `promoted` and records the project id; it grants no gate.
5. Surface each created volume's engine-derived design policy and confirm each carries a `series` back-reference.

### All modes

6. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py series list` and `series status <series-id>` to confirm the series registry and manifest are consistent.
7. Emphasize: each volume is a fully independent project. The series manifest links volumes and shares context (visual system, recurring elements, terminology, canon) but does NOT create a series-level niche, interior, cover, compliance, listing, or release gate. Every volume must pass its own six human gates.

## Sibling context

Before generating content or layout for any volume, read its sibling context with `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py series context <project-id>`: read-only what earlier volumes cover, what later volumes will cover, and the shared canon. Never write into a sibling project's files; cite a sibling's frozen artifact by hash if you rely on it.

## Required outputs

- The created or linked volume(s) under `projects/<id>/`, each with a confirmed `series` back-reference.
- Updated `series/<series-id>/series.yaml` manifest with the newly filled slot(s) and a series event.
- Refreshed `catalog/products.json` and `catalog/series.json` roll-ups.
- For mode 3: recorded research promotions for each created volume, and a clear note of which candidates were proposed but not built.
- Engine-derived design policy surfaced for each new volume.
- Next-stage recommendation for each new volume (typically `product-run` or `product-plan`).

## Stop conditions

- Stop on invalid project or series state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or a tool failure that prevents a required check.
- In mode 3, stop and wait if the human has not selected a proposal via AskUserQuestion; never auto-create volumes or promote research from a suggestion alone.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the series, each volume added and its current stage, agents used, files and hashes created or changed, validation/gate results, any research promotions recorded, unresolved findings, and the next valid action per volume.
