---
name: product-build-proof
description: >-
  Produce a pre-flight proof report for the built interior and cover PDFs covering trim, bleed, margins, DPI, color mode, and font embedding without modifying approved content.
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

# /product-build-proof

## Goal

Produce a pre-flight proof report for the built interior and cover PDFs covering trim, bleed, margins, DPI, color mode, and font embedding without modifying approved content.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Interior PDF and cover PDF are built and registered with exact hashes.
- Print channel specification (trim, bleed, color mode, DPI, page count parity) is documented.

## Specialist delegation

Use these agents only for bounded assignments with exact input hashes, output paths, and acceptance tests:
- `prepress-specialist`

## Procedure

1. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py project status $ARGUMENTS` and confirm the interior and cover artifact hashes are current.
2. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py build proof --project-id <id>` with the project ID resolved from `$ARGUMENTS`.
3. For the interior PDF: verify trim size matches the channel specification; verify bleed extends at least 0.125 in (3 mm) on all exterior pages where bleed is declared; verify all content is within the safety margin; verify even page count.
4. For the cover PDF: verify the full wrap dimensions (front + spine + back + bleed) match the channel template calculated from the confirmed page count and paper stock; verify no live text or art is within the bleed zone.
5. Check image resolution: flag any raster image below 300 DPI as a major finding; flag any image below 200 DPI as a blocker.
6. Check color mode: confirm interior PDF matches the channel requirement (grayscale or CMYK as declared); confirm cover PDF matches the channel requirement (CMYK for print); flag RGB images in a print-only PDF as a major finding.
7. Check font embedding: confirm all fonts are fully embedded; flag any unembedded or subset-only font as a major finding.
8. Check for PDF/X compliance if required by the channel; record the PDF version and any compliance warnings.
9. Do not modify any approved content artifact to resolve a preflight finding; raise each finding so it is resolved through the appropriate revision workflow.
10. Delegate deep preflight analysis to `prepress-specialist` with exact artifact hashes; record all `not-run` checks explicitly.

## Required outputs

- Pre-flight proof report (per-check results: trim, bleed, margins, DPI, color mode, font embedding, page count, PDF/X compliance if applicable).
- Structured findings for all FAIL and WARNING items with severity and remediation guidance.
- Overall preflight decision (PASS / FAIL) with finding IDs.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
