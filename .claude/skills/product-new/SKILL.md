---
name: product-new
description: >-
  Create a new puzzle, coloring, journal, or printable project with a resolved engine-derived design policy and initial content plan.
argument-hint: "<category> <PRODUCT_ID>  |  --topic <t> --audience <a> --product-type <pt> --formats <f> [--working-title <wt>]"
user-invocable: true
effort: high
allowed-tools:
  - Read
  - Write
  - Bash
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-new

## Goal

Create a new puzzle, coloring, journal, or printable project with a resolved engine-derived design policy and initial content plan.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

There are **two invocation forms**:

- **Pipeline-sourced** — `/product-new <category> <PRODUCT_ID>` (two bare positional
  args, no leading `--`): pull an already-researched candidate from the category
  pipeline. **No research is performed here.** Follow **Procedure A**, then the
  standard Procedure.
- **Direct** — `/product-new --topic <t> --audience <a> --product-type <pt> --formats
  <f>`: the human supplies every input point directly. Follow the standard Procedure.

## Entry criteria

- The human has supplied a topic, audience band, product type, and at least one format
  (direct form), **or** a `<category> <PRODUCT_ID>` pair whose pipeline entry supplies
  them (pipeline-sourced form).
- Valid audience values: `kids-4-8`, `kids-6-10`, `tween-8-12`, `teen-13-17`, `adult-general`, `senior-large-print`.
- Valid product types: `puzzle-book`, `activity-book`, `coloring-book`, `guided-journal`, `workbook`, `planner`, `digital-printable`.
- Valid formats: `paperback`, `hardcover`, `digital-pdf` (one or more, comma-separated).
- No external account, channel credential, or platform listing is required at this stage.

## Procedure A — pipeline-sourced (`<category> <PRODUCT_ID>`)

Run these steps first when the invocation is a bare `<category> <PRODUCT_ID>` pair, then
continue into the standard Procedure at step 2. **Perform no research in this skill** —
the pipeline was built by `/research`.

- **A0.** Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py research show <category> --product-id <PRODUCT_ID>`.
  - If it returns `not-found`: STOP and list the available `available_ids`; suggest
    `/research --status "<category>"` or picking a listed ID.
  - If the entry `status` is already `promoted`: STOP and point to the existing project
    `promoted_project_id`; do not create a duplicate.
- **A1.** Map the entry to `project init` **human-input points only**: `--topic`
  (working_title or a topic phrase), `--audience`, `--product-type`, `--formats`, and
  `--working-title`. Do **not** pass any craft literals (trim, difficulty, counts,
  style) to `project init` — those are engine-derived at init (rule 20). Product types
  narrower than the `project init` enum (`activity-book`→`puzzle-book`,
  `workbook`/`planner`→`guided-journal`) map to the nearest valid init type and the
  original intent is recorded in the intake note.
- **A2.** After `project init` (standard Procedure step 2) and the intake note (step 5),
  write a **"Pipeline-sourced context (advisory — not human-committed craft values)"**
  block into the intake note capturing the entry's `difficulty`, `cover_style`,
  `interior_style_notes`, `seo`, `positioning`, `series_grouping`, `evidence_refs`, and
  `open_questions`. Label each item with its `confidence` and `evidence_ref`. State
  explicitly that these are advisory inputs for later stages, **not** approved craft
  values.
- **A3.** Flip the pipeline entry to `promoted` and record the new project id:
  `ph_cli.py research promote <category> --product-id <PRODUCT_ID> --project-id <clr-YYYY-slug>`.
- **A4.** If the entry's `series_grouping.is_series` is true, surface
  `/product-series-new` as a suggested next step — do **not** auto-create the series.

## Procedure

1. Parse `$ARGUMENTS` without inventing missing human decisions. The human supplies the topic, audience band, product type, and formats — do not substitute defaults for these human-input points. (Pipeline-sourced form: these values come from the pipeline entry via Procedure A, which is still human-input data — no research is done in this skill.)
2. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py project init --topic <t> --audience <a> --product-type <pt> --formats <f> [--project-id <id>] [--working-title <wt>]` using the exact values from `$ARGUMENTS`.
3. Read the created `project.yaml` and `state.json`. Surface the engine-derived design policy written under the `production` and `design` blocks: trim size, colour interior flag, colour policy, line-art density, age-appropriate content constraints, reading level, visual density, and pedagogy. Report these derived values explicitly — they are determined deterministically by the design-policy engine from `audience` + `product_type` + age band; no human picks them per product.
4. Confirm the assigned project ID follows the pattern `clr-YYYY-slug` and the initial lifecycle state is `DISCOVERY`.
5. Create a concise intake note under `projects/<id>/notes/intake.md` listing: supplied arguments; engine-derived design policy with its recorded rationale and source; the six human gate points (niche approval, interior approval, cover approval, compliance approval, listing approval, release approval); decisions still required from the human; and the next valid command.
6. Register the intake note as an artifact if it is non-template.

## Required outputs

- New `projects/<id>/` directory with `project.yaml`, `state.json`, and initial event log.
- Catalog entry for the new project.
- Intake note surfacing the engine-derived design policy and all six human gate points (plus the advisory pipeline-context block for the pipeline-sourced form).
- Confirmed project ID (pattern `clr-YYYY-slug`) and `DISCOVERY` state.
- For the pipeline-sourced form: the pipeline entry flipped to `promoted` with the new project id recorded (`research promote`).
- Next-stage recommendation (typically `product-run` or `product-plan`).

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
