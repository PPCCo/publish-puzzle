---
name: product-verify
description: >-
  Independently verify generated content by code for uniqueness, solvability, answer-key correctness, and difficulty accuracy without editing or regenerating content.
argument-hint: "<project-id> [--type <content-type>]"
user-invocable: true
effort: high
model: '@bedrock-eus1/us.anthropic.claude-sonnet-5'
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Skill
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
---

# /product-verify

## Goal

Independently verify generated content by code for uniqueness, solvability, answer-key correctness, and difficulty accuracy without editing or regenerating content.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- A generated content artifact and its exact hash are registered.
- Provenance record confirms seed, generator version, and content type.
- Verification has not already been run against the current artifact hash.

## Procedure

1. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py project status $ARGUMENTS` and confirm the artifact hash matches the registered generation output.
2. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py verify --project-id <id> [--type <content-type>]` with all arguments resolved from `$ARGUMENTS`.
3. Treat the script decision (PASS / FAIL / WARNING) as authoritative for each check dimension; do not override a FAIL with reasoning.
4. Confirm each check dimension was executed; record any `not-run` dimension explicitly as FAIL for gate purposes.
5. For puzzles: confirm uniqueness (no duplicate grids or clue sets within the artifact), solvability (every puzzle has at least one valid solution), solution correctness (answer key matches all valid solutions), and difficulty accuracy (measured difficulty metric matches the labeled tier).
6. For journal prompts: confirm uniqueness (no repeated prompt text), audience fit (language and theme match declared age/audience), and absence of unsafe or distressing content for the target audience.
7. For printables: confirm page-size compliance (US Letter or A4), DPI minimum, and that answer keys are grouped in a back-only section when applicable.
8. Record per-item verification results with item IDs, check dimension, result, and evidence; do not edit or regenerate any content item.
9. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py artifact list <id>` to confirm the verification record is linked to the correct artifact.

## Required outputs

- Verification report (per-item results for uniqueness, solvability, answer-key correctness, difficulty accuracy).
- Dimension result summary (PASS / FAIL / WARNING / not-run per dimension).
- List of failing item IDs with evidence for repair routing.
- Verification artifact registration receipt.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
