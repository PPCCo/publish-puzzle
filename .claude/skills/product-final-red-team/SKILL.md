---
name: product-final-red-team
description: >-
  Perform an independent final adversarial audit across the whole product before final gates, relying on no producer assurance and cross-checking all artifact hashes and gate evidence.
argument-hint: "<project-id>"
user-invocable: true
effort: xhigh
model: '@bedrock-eus2/us.anthropic.claude-opus-4-8'
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Agent
  - Skill
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-final-red-team

## Goal

Perform an independent final adversarial audit across the whole product before final gates, relying on no producer assurance and cross-checking all artifact hashes and gate evidence.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Release-candidate artifacts exist for all required components (interior, cover, digital bundle if applicable).
- All upstream quality gate reports and verification records are present.
- Project is at FINAL_PROOF or FINAL_APPROVAL stage.

## Specialist delegation

Use these agents only for bounded assignments with exact input hashes, output paths, and acceptance tests:
- `quality-lead`

## Procedure

1. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py project status $ARGUMENTS` in a fresh independent agent context; accept no prior session's assumptions.
2. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py artifact list <id>` and reconstruct the full artifact inventory; confirm every declared artifact has a registered hash.
3. Reconstruct the promised product from: project brief, cover design, title, difficulty labels, page/puzzle count, audience claims, and metadata; identify any gap between promise and content.
4. Cross-check exact hashes across interior PDF, cover, digital bundle, answer-key placement (back-only), provenance records, rights ledger, accessibility report, and metadata artifact.
5. Independently verify that every quality gate report is current (references the release-candidate hash, not a prior revision hash) and that no gate shows `not-run` or `INCOMPLETE`.
6. Spot-check: at least 10% of puzzle/coloring/printable items for solvability, solution correctness, and difficulty label accuracy; all coloring line art for origination flags; all printable pages for DPI and page-size compliance.
7. Search for placeholders (e.g., `TODO`, `TBD`, `FIXME`, `[INSERT]`), accidental personal data, stale page counts or difficulty counts in metadata, missing answer keys, and cross-format count inconsistencies.
8. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py quality evaluate --project-id <id>` and `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py audit accessibility --project-id <id>` independently; do not reuse cached reports.
9. Write blocker and major findings without repairing them; issue a residual-risk statement covering any findings below blocker threshold.
10. Recommend PASS only when: all critical dimension thresholds are met with current-hash evidence, no blocker findings are open, and the declared product matches the built artifacts.

## Required outputs

- Independent final audit report with finding IDs, severity, and evidence.
- Cross-artifact hash discrepancy report.
- Residual-risk statement.
- PASS or FAIL recommendation with full rationale.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
