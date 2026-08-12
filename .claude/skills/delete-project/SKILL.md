---
name: delete-project
description: >-
  Remove a project's working directory only after confirming it is not frozen, approved, or published and after explicit human confirmation.
argument-hint: "<project-id> --confirm"
user-invocable: true
effort: medium
model: '@bedrock-eus1/us.anthropic.claude-haiku-4-5-20251001-v1:0'
allowed-tools:
  - Read
  - Bash
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
---

# /delete-project

## Goal

Remove a project's working directory only after confirming it is not frozen, approved, or published and after explicit human confirmation.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

- `<project-id>` (required) — the project to delete, matching pattern `clr-YYYY-slug`. If missing or unresolvable, STOP and ask; never guess a project ID.
- `--confirm` (required) — explicit human confirmation flag. Absent this flag, the skill MUST halt before removing anything. Never infer deletion consent from a vague phrase such as "yes" or "ok".

## Entry criteria

- A project ID matching the pattern `clr-YYYY-slug` is supplied.
- The `--confirm` flag is present in `$ARGUMENTS`.
- The project directory `projects/<id>/` exists.
- The human has explicitly asked to delete this specific project.

## Refuse-and-escalate conditions (STOP — do not delete)

Stop and escalate to the human when any of these hold:

- The project `state.json` current state is any post-interior-approval state: `INTERIOR_APPROVED`, `COVER_IN_PROGRESS`, `COVER_APPROVED`, `COMPLIANCE_IN_PROGRESS`, `COMPLIANCE_APPROVED`, `LISTING_IN_PROGRESS`, `LISTING_APPROVED`, `RELEASE_AUTHORIZED`, `PUBLISHED`, or any frozen state. Deleting provenance of an approved or published product destroys the record of what was distributed. Require a second explicit human instruction naming the release consequence.
- The project has any recorded approval artifact under `projects/<id>/approvals/`.
- The project ID resolves to more than one directory or does not match the resolved directory.
- `project status` fails to run.
- The `--confirm` flag is absent.
- The request is ambiguous about which project or reads as hypothetical.

## Procedure

1. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py project status <project-id>` and read `projects/<id>/project.yaml` and `projects/<id>/state.json`. Record the current lifecycle state and whether any approvals exist.
2. Check all refuse-and-escalate conditions. If any hold, STOP and report exactly why; delete nothing.
3. Confirm `--confirm` is present in `$ARGUMENTS`; if absent, halt and instruct the human to re-invoke with `--confirm`.
4. Present the blast radius to the human before deleting: the project directory path, file count, the `catalog/books.json` entry that will be dropped, and what will NOT be touched (framework config/rules/standards, other projects, `.claude/logs/` audit logs).
5. Remove the project directory using a targeted non-recursive-force approach: `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py project transition <project-id> --to DELETED --actor cli` if the CLI supports a DELETED terminal state, otherwise move the directory to `projects/.trash/<project-id>-deleted/` using a single `mv`. Never use `rm -rf`.
6. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py catalog rebuild` to remove the project from `catalog/books.json` via the CLI; do not hand-edit catalog files.
7. Confirm: the project directory is absent from `projects/`, the catalog entry is gone, and `project status <project-id>` reports the project as absent or deleted.

## Required outputs

- Confirmation that the project was not in a frozen, approved, or published state before deletion.
- Project directory removed or tombstoned.
- `catalog/books.json` rebuilt without the deleted entry.
- Audit record of the deletion (project ID, prior state, timestamp, deletion method).

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
