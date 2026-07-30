---
name: product-generate
description: >-
  Deterministically generate puzzle, journal, or printable content from a seed by code and register it as an immutable artifact with full provenance.
argument-hint: "<project-id> --type <content-type> --count <n> --difficulty <d> [--seed <s>]"
user-invocable: true
effort: high
allowed-tools:
  - Read
  - Write
  - Bash
  - Agent
  - Skill
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-generate

## Goal

Deterministically generate puzzle, journal, or printable content from a seed by code and register it as an immutable artifact with full provenance.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Project exists and is in a generation-permitted stage (e.g., CONTENT_DRAFT or REVISION).
- Content type, count, difficulty label, and target audience are specified in the project plan.
- A seed value is provided or will be auto-assigned and recorded; the same seed must reproduce the same output.
- Coloring line art is designated as original; no tracing or third-party IP sources are permitted.

## Specialist delegation

Use these agents only for bounded assignments with exact input hashes, output paths, and acceptance tests:
- `puzzle-designer`
- `puzzle-generator`
- `journal-prompt-writer`
- `printable-designer`

## Procedure

1. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py project status $ARGUMENTS` and confirm the stage permits generation.
2. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py project plan $ARGUMENTS` to confirm type, count, difficulty, and audience targets.
3. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py generate --project-id <id> --type <content-type> --count <n> --difficulty <d> [--seed <s>]` with all arguments resolved from `$ARGUMENTS`.
4. Record the seed (auto-assigned or caller-supplied), generator version, content type, difficulty label, and timestamp in a provenance record alongside the artifact.
5. For coloring line art: confirm the origination flag is set to `original`; reject any asset flagged as traced or sourced from a third-party reference image.
6. For printables: confirm page size (US Letter or A4) and DPI meet configured minimums before registration.
7. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py artifact register` to register the generated artifact with its hash.
8. Do not assert solvability, uniqueness, or difficulty accuracy; queue independent verification via `/product-verify`.
9. Delegate bounded sub-generation tasks to specialist agents where content type warrants it; each delegation must include exact output path, content schema, and acceptance test.

## Required outputs

- Generated content artifact with immutable hash.
- Provenance record (seed, generator version, content type, difficulty label, timestamp, origination flag).
- Artifact registration receipt.
- Verification queue entry pointing to `/product-verify`.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
