---
name: product-status
description: >-
  Show a project's current lifecycle state, active hashes, approvals, unresolved findings, gate results, missing artifacts, and next valid actions.
argument-hint: "<project-id>"
user-invocable: true
effort: medium
model: '@bedrock-eus1/us.anthropic.claude-haiku-4-5-20251001-v1:0'
allowed-tools:
  - Read
  - Bash
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
---

# /product-status

## Goal

Show a project's current lifecycle state, active hashes, approvals, unresolved findings, gate results, missing artifacts, and next valid actions.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- A valid project ID matching the pattern `clr-YYYY-slug` is supplied.
- The project directory `projects/<id>/` exists under the repository root.

## Procedure

1. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py project status $ARGUMENTS`.
2. Do not infer completion from file presence alone; read the `state.json` lifecycle state authoritatively.
3. Highlight stale approvals, hash mismatches between recorded and on-disk artifact hashes, and any open blockers in a dedicated section.
4. Report each of the six human gate results (niche, interior, cover, compliance, listing, release) as PASS, FAIL, PENDING, or NOT-RUN — never treat NOT-RUN as PASS.
5. List missing required artifacts (e.g., line-art source files, interior PDF, cover PDF, compliance declaration, KDP/Etsy/Gumroad listing metadata) that are expected at the current stage.
6. List only state-valid next actions given the current 26-state lifecycle position.

## Required outputs

- Project ID, current lifecycle state, and product type (puzzle-book, activity-book, coloring-book, guided-journal, workbook, planner, or digital-printable).
- Active artifact list with recorded hashes and on-disk hash verification status.
- Approval and gate results for all six human gates that have been reached.
- Stale approvals, hash mismatches, and open blockers called out explicitly.
- Missing required artifacts for the current stage.
- Next valid commands or actions.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
