---
name: product-series-new
description: >-
  Create a product-series manifest from an approved plan and initialize volume 1; each volume is an independent project with its own full gate sequence.
argument-hint: "--series-id <id> --books-json <json-or-path>"
user-invocable: true
effort: high
model: '@bedrock-eus1/us.anthropic.claude-sonnet-5'
allowed-tools:
  - Read
  - Write
  - Bash
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
---

# /product-series-new

## Goal

Create a product-series manifest from an approved plan and initialize volume 1; each volume is an independent project with its own full gate sequence.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- The human has provided a series concept with at least two planned volumes.
- Each planned volume has a topic, audience band, product type, and formats.
- A series ID or series title is supplied; if no `--series-id` is given, the CLI assigns one.
- No external channel credential or platform listing is required at this stage.

## Procedure

1. Parse `$ARGUMENTS`; extract the `--series-id` and `--books-json` (inline JSON array or path to a JSON file) values exactly as provided.
2. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py series init $ARGUMENTS` to create the series manifest under `series/<series-id>/series.yaml` and initialize volume 1 as its own project.
3. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py series list` to confirm the series appears in the series registry.
4. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py series status <series-id>` to confirm the manifest is valid and volume 1 is linked.
5. Read the created `series/<series-id>/series.yaml` and the volume-1 `project.yaml` and `state.json`. Surface the engine-derived design policy for volume 1 (trim size, colour policy, line-art density, age-appropriate content constraints, visual density, and pedagogy) exactly as `product-new` does.
6. Confirm volume 1 carries a `series` back-reference (series_id, position, total_planned, prior_project_ids).
7. Explain the on-demand model: subsequent volumes are created when the human is ready with `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py series add-book <series-id> --position N`. An existing standalone project can be folded in with `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py series link <series-id> <project-id>`.
8. Emphasize: each volume is a fully independent project. The series manifest links them and provides shared context (shared visual system, recurring characters, terminology, and canon) but does NOT create a series-level niche, interior, cover, compliance, listing, or release gate that bypasses any individual volume's human gates.

## Sibling context

When working on any volume in the set, read its sibling context with `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py series context <project-id>` before generating content or layout. This returns read-only: what earlier volumes cover, what later volumes will cover, and the shared canon. Never write into a sibling project's files; cite a sibling's frozen artifact by hash if you rely on it.

## Required outputs

- New `series/<series-id>/series.yaml` manifest and series event log.
- Volume 1 project under `projects/<id>/` with a confirmed `series` back-reference.
- `catalog/series.json` roll-up entry.
- Engine-derived design policy surfaced for volume 1.
- Explanation of the on-demand model for volumes 2+.
- Next-stage recommendation for volume 1 (typically `product-run` or `product-plan`).

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
