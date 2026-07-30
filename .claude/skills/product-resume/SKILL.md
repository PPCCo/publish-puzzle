---
name: product-resume
description: >-
  Reconstruct working context for an existing project and recommend the next valid action without repeating completed stages.
argument-hint: "<project-id>"
user-invocable: true
effort: medium
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-resume

## Goal

Reconstruct working context for an existing project and recommend the next valid action without repeating completed stages.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- A valid project ID matching the pattern `clr-YYYY-slug` is supplied.
- The project directory `projects/<id>/` exists.

## Procedure

1. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py project status $ARGUMENTS` to get the authoritative lifecycle state.
2. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py project plan $ARGUMENTS` to get the deterministic next-action recommendation.
3. Read `projects/<id>/project.yaml` for product type, audience, formats, channels, and engine-derived design policy (trim size, colour policy, visual density, pedagogy).
4. Read `projects/<id>/state.json` for current state, completed transitions, and recorded artifact hashes.
5. Glob `projects/<id>/findings/` and `projects/<id>/approvals/` to identify open findings and recorded human gate approvals.
6. Read the most recent entries in the event log (`python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py event tail $ARGUMENTS`) to understand what was last executed.
7. Detect repository/state divergence: verify on-disk artifact hashes against recorded hashes; flag any mismatch before recommending work.
8. Summarize: what is complete and authoritative, what gate approvals are recorded, what open findings remain, and what the next bounded action is.
9. Do not replay completed stages unless they are explicitly invalidated by a hash mismatch or the human requests a redo.

## Required outputs

- Recovery summary: completed stages, recorded approvals, open findings.
- Validated current lifecycle state and product design policy (product type, audience, formats, channels).
- Next bounded action with exact CLI command or skill invocation.
- Human gate notice if the project is at a gate boundary (niche, interior, cover, compliance, listing, or release).
- List of any hash mismatches or state divergences detected.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
