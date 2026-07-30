---
name: product-doctor
description: >-
  Check the local framework, model pin, dependencies, and optional production tools without making changes.
argument-hint: ""
user-invocable: true
effort: medium
allowed-tools:
  - Read
  - Bash
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-doctor

## Goal

Check the local framework, model pin, dependencies, and optional production tools without making changes.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Run from the repository root.
- No project ID is required; this skill checks the framework environment, not a specific project.

## Procedure

1. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py doctor $ARGUMENTS`.
2. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py framework validate`.
3. Report required failures (Python version, schema files, CLI availability, model pin) separately from optional-tool warnings (PDF renderers, image processors, barcode generators, KDP/Etsy/Gumroad CLI tools).
4. Do not mark a missing optional production tool (e.g., a PDF compositor or line-art renderer) as a passed validation; report it as an optional-tool warning with its release impact.
5. Do not make any changes to configuration, dependencies, or framework files during this check.

## Required outputs

- Environment diagnostics: Python version, framework schema status, CLI availability, and model pin.
- Required failures listed with corrective commands.
- Optional-tool warnings listed with release-impact statement for each missing tool.
- Framework validate result (pass or list of violations).

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
