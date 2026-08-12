---
name: product-rights-check
description: >-
  Evaluate the rights ledger for all content, art, fonts, and tools used in a product and gate on completeness; never infer clearance from missing or absent evidence.
argument-hint: "<project-id>"
user-invocable: true
effort: high
model: '@bedrock-eus1/us.anthropic.claude-sonnet-5'
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Agent
  - Skill
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
---

# /product-rights-check

## Goal

Evaluate the rights ledger for all content, art, fonts, and tools used in a product and gate on completeness; never infer clearance from missing or absent evidence.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- A rights ledger exists for the project.
- All registered artifacts (content, coloring art, fonts, third-party clip art if any) have corresponding rights entries.

## Specialist delegation

Use these agents only for bounded assignments with exact input hashes, output paths, and acceptance tests:
- `rights-manager`

## Procedure

1. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py project status $ARGUMENTS` and confirm the artifact inventory is complete.
2. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py rights check --project-id <id>` with the project ID resolved from `$ARGUMENTS`.
3. Review the rights ledger for every component: generated puzzle/journal/printable content, coloring line art, cover art, fonts, clip art or decorative elements, and any third-party tools or data sources used in generation.
4. Flag any entry with status `unknown`, `unresolved`, `missing`, or `incompatible`; these are blockers and must not be cleared by assumption.
5. For coloring line art: confirm the `origination` field is `original` and the artist or generator provenance is documented; any entry without a confirmed origination record is a blocker.
6. For AI-generated content: record the tool, model version, and provider commercial terms; do not assert copyrightability conclusions — record only what the provider terms state and flag for human legal review if the terms are ambiguous.
7. For fonts: confirm each font license permits commercial print and/or digital distribution for the declared channels.
8. For third-party puzzle data (e.g., word lists, clue databases): confirm the source license is compatible with commercial publication and that the license is recorded in the rights ledger.
9. Delegate deep license compatibility analysis to `rights-manager` with exact artifact hash and ledger snapshot.
10. Emit a rights gate decision (CLEARED / BLOCKED / INCOMPLETE); route any BLOCKED or INCOMPLETE entry to human rights review before proceeding to build stages.

## Required outputs

- Rights gate decision (CLEARED / BLOCKED / INCOMPLETE).
- Rights ledger evaluation report (per-component status, evidence, and finding IDs for blockers).
- List of blocked or incomplete rights entries with required resolution actions.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
