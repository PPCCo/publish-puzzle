---
name: product-standards-refresh
description: >-
  Re-read active config, rules, and standards files and summarize the operative design policy for a project without modifying any artifact.
argument-hint: "[project-id]"
user-invocable: true
effort: medium
model: '@bedrock-eus1/us.anthropic.claude-haiku-4-5-20251001-v1:0'
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-standards-refresh

## Goal

Re-read active config, rules, and standards files and summarize the operative design policy for a project without modifying any artifact.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Run from the repository root.
- A project ID is optional; if supplied, the project-specific policy overlay is also summarized.

## Procedure

1. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py framework validate` to confirm the framework is internally consistent before reading policy files.
2. Glob `.claude/config/` for all active configuration files; read each one and note its version or last-modified marker.
3. Glob `.claude/rules/` for all rule files applicable to the product domain (puzzle-book, activity-book, coloring-book, guided-journal, workbook, planner, digital-printable); read each one.
4. Glob `.claude/standards/` for all standards files covering: content safety (kids-4-8, kids-6-10, tween-8-12, teen-13-17, adult-general, senior-large-print), original-only line-art policy, KDP/Etsy/Gumroad/generic channel requirements, paperback/hardcover/digital-pdf format specifications, and accessibility requirements.
5. If a project ID is supplied in `$ARGUMENTS`, additionally read `projects/<id>/project.yaml` and surface how the engine-derived design policy (trim, colour policy, line-art density, visual density, pedagogy) is derived from the framework standards for that product type and audience band.
6. Summarize the operative policy in plain language: which rules are active, which standards apply to which product types and audience bands, any channel-specific constraints, and any known expiry dates or review-due markers on time-sensitive standards.
7. Do not modify any config, rule, standards, project, or artifact file during this skill.

## Required outputs

- Framework validate result (pass or list of violations).
- Summary of active config, rules, and standards with file paths and version markers.
- Channel-specific constraints for KDP, Etsy, Gumroad, and generic channels currently in effect.
- Audience-band content safety rules currently in effect.
- Original-only line-art policy statement.
- If a project ID was supplied: the engine-derived design policy for that project and which standards govern it.
- Any time-sensitive standards with known expiry or review-due dates.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
