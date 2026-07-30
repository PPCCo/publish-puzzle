---
name: product-new
description: >-
  Create a new puzzle, coloring, journal, or printable project with a resolved engine-derived design policy and initial content plan.
argument-hint: "--topic <t> --audience <a> --product-type <pt> --formats <f> [--working-title <wt>]"
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

## Entry criteria

- The human has supplied a topic, audience band, product type, and at least one format.
- Valid audience values: `kids-4-8`, `kids-6-10`, `tween-8-12`, `teen-13-17`, `adult-general`, `senior-large-print`.
- Valid product types: `puzzle-book`, `activity-book`, `coloring-book`, `guided-journal`, `workbook`, `planner`, `digital-printable`.
- Valid formats: `paperback`, `hardcover`, `digital-pdf` (one or more, comma-separated).
- No external account, channel credential, or platform listing is required at this stage.

## Procedure

1. Parse `$ARGUMENTS` without inventing missing human decisions. The human supplies the topic, audience band, product type, and formats — do not substitute defaults for these human-input points.
2. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py project init --topic <t> --audience <a> --product-type <pt> --formats <f> [--project-id <id>] [--working-title <wt>]` using the exact values from `$ARGUMENTS`.
3. Read the created `project.yaml` and `state.json`. Surface the engine-derived design policy written under the `production` and `design` blocks: trim size, colour interior flag, colour policy, line-art density, age-appropriate content constraints, reading level, visual density, and pedagogy. Report these derived values explicitly — they are determined deterministically by the design-policy engine from `audience` + `product_type` + age band; no human picks them per product.
4. Confirm the assigned project ID follows the pattern `clr-YYYY-slug` and the initial lifecycle state is `DISCOVERY`.
5. Create a concise intake note under `projects/<id>/notes/intake.md` listing: supplied arguments; engine-derived design policy with its recorded rationale and source; the six human gate points (niche approval, interior approval, cover approval, compliance approval, listing approval, release approval); decisions still required from the human; and the next valid command.
6. Register the intake note as an artifact if it is non-template.

## Required outputs

- New `projects/<id>/` directory with `project.yaml`, `state.json`, and initial event log.
- Catalog entry for the new project.
- Intake note surfacing the engine-derived design policy and all six human gate points.
- Confirmed project ID (pattern `clr-YYYY-slug`) and `DISCOVERY` state.
- Next-stage recommendation (typically `product-run` or `product-plan`).

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
