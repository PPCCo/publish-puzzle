---
name: product-accessibility-audit
description: >-
  Audit contrast, grid and cell legibility, large-print compliance, alt text and decorative designation, and printable DPI and page size for all product artifacts.
argument-hint: "<project-id>"
user-invocable: true
effort: high
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Agent
  - Skill
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-accessibility-audit

## Goal

Audit contrast, grid and cell legibility, large-print compliance, alt text and decorative designation, and printable DPI and page size for all product artifacts.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Built or near-final artifacts (interior PDF, digital bundle, cover) are registered with exact hashes.
- Large-print or accessible-edition requirements are declared in the project plan if applicable.

## Specialist delegation

Use these agents only for bounded assignments with exact input hashes, output paths, and acceptance tests:
- `accessibility-auditor`

## Procedure

1. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py project status $ARGUMENTS` and confirm artifact hashes are current.
2. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py audit accessibility --project-id <id>` with the project ID resolved from `$ARGUMENTS`.
3. Evaluate contrast ratios for all puzzle grids, coloring-page instruction text, journal prompt text, and printable body text against WCAG AA minimums (4.5:1 for normal text, 3:1 for large text and UI components).
4. Evaluate grid and cell legibility: minimum cell size for sudoku, word search, and crossword grids at declared trim size; minimum font size for clue numbers and labels; line weight sufficient for monochrome printing.
5. For large-print editions (if declared): verify all body text meets the configured large-print minimum point size and that cell sizes are enlarged proportionally.
6. Evaluate all coloring line art and decorative page elements: confirm each is tagged as `decorative` (no alt text required) or `informational` (alt text required and present).
7. For printable PDFs: confirm each page meets declared DPI minimum (typically 300 DPI for print) and targets US Letter (8.5 × 11 in) or A4 (210 × 297 mm) as declared in the project plan.
8. For digital PDF bundles: confirm reflowable or fixed-layout designation is consistent, text is selectable where required, and reading order is logical.
9. Classify each check as PASS, WARNING, FAIL, or not-run; a gate may advance with WARNING status, but must not advance with FAIL or not-run.
10. Write structured remediation findings for each FAIL and WARNING; route FAIL findings to `/product-revise`; update accessibility metadata only with evidence from this audit.

## Required outputs

- Accessibility audit report (per-check results: contrast, legibility, large-print, alt text, DPI, page size).
- Structured remediation findings for FAIL and WARNING items.
- Gate decision (PASS / WARNING / FAIL) with rationale.
- Accessibility metadata recommendation based on audit evidence.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
