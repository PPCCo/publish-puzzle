---
name: product-build-digital
description: >-
  Assemble a digital printable bundle of PDFs and linked pages meeting DPI minimums and US Letter or A4 print-at-home requirements for each declared page format.
argument-hint: "<project-id>"
user-invocable: true
effort: high
model: '@bedrock-eus1/us.anthropic.claude-sonnet-5'
allowed-tools:
  - Read
  - Write
  - Bash
  - Agent
  - Skill
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-build-digital

## Goal

Assemble a digital printable bundle of PDFs and linked pages meeting DPI minimums and US Letter or A4 print-at-home requirements for each declared page format.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Content artifact has passed `/product-verify` and `/product-quality-gate` at the required stage.
- Page size (US Letter and/or A4) and DPI targets are declared in the project plan.
- Rights records for all fonts, art, and content are cleared.
- Digital distribution channel and bundle format (PDF, ZIP, linked download page) are specified.

## Specialist delegation

Use these agents only for bounded assignments with exact input hashes, output paths, and acceptance tests:
- `printable-designer`
- `prepress-specialist`

## Procedure

1. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py project status $ARGUMENTS` and confirm content hash matches the approved artifact.
2. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py build digital --project-id <id>` with the project ID resolved from `$ARGUMENTS`.
3. Confirm every page in the bundle targets the declared page size (US Letter: 8.5 × 11 in; A4: 210 × 297 mm); flag any page with a mismatched size as a blocker.
4. Confirm all raster art (coloring line art, puzzle grids, decorative frames) is embedded at 300 DPI minimum; flag any image below 300 DPI as a major finding.
5. Confirm coloring pages have adequate white space and line weight for print-at-home ink usage; heavy fill areas that would drain ink excessively are a minor finding.
6. Confirm answer keys are present in the bundle in a back-only section or as a clearly separated document section; they must not appear adjacent to the corresponding puzzle pages.
7. Confirm fonts are embedded in the PDF; no subset-only embedding that omits glyphs present in the content.
8. For linked download pages: confirm all URLs resolve, file sizes are within declared maximums, and download links reference the registered artifact hashes.
9. Delegate page-spec compliance review to `prepress-specialist` and digital layout quality review to `printable-designer`, each with exact page hash range.
10. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py artifact register` to register the digital bundle with its hash.

## Required outputs

- Digital printable bundle (PDF or ZIP) with immutable hash.
- Build log (page count, page size compliance, DPI summary, font embedding status, answer key placement).
- Artifact registration receipt.
- Download link verification record (if applicable).

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
