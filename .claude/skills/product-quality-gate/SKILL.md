---
name: product-quality-gate
description: >-
  Evaluate current structured review files against configured quality thresholds and emit a PASS, FAIL, or INCOMPLETE gate decision for the target stage.
argument-hint: "<project-id> [--stage <stage>]"
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

# /product-quality-gate

## Goal

Evaluate current structured review files against configured quality thresholds and emit a PASS, FAIL, or INCOMPLETE gate decision for the target stage.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Review JSON files exist for all required dimensions of the target artifact set.
- Each review references the current artifact hash.

## Procedure

1. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py project status $ARGUMENTS` to confirm stage and artifact hashes.
2. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py quality evaluate --project-id <id> [--stage <s>]` with all arguments resolved from `$ARGUMENTS`.
3. Confirm every review references the current artifact hash; flag any stale-hash review as invalid evidence and treat its dimension as `not-run`.
4. For each critical dimension (solvability, solution_correctness, originality, rights, accessibility, audience_fit), verify the score meets the higher configured threshold; a single critical dimension below threshold forces a FAIL gate decision.
5. Treat any dimension with status `not-run` as FAIL; do not substitute narrative confidence for a completed check.
6. Report open finding counts by severity (blocker, major, minor, info), per-dimension scores, weighted overall score, missing evidence dimensions, and current revision-cycle status.
7. Emit the final gate decision (PASS / FAIL / INCOMPLETE) and list all blocking finding IDs with their required next actions.
8. Do not reinterpret a FAIL as a conditional PASS; route incomplete evidence back to the responsible review or verification stage.

## Required outputs

- Machine-readable quality-gate JSON (decision, per-dimension scores, open finding counts, artifact hash, timestamp).
- Human-readable gate summary with rationale.
- Blocking finding IDs and prescribed next actions.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
