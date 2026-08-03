---
name: product-build-cover
description: >-
  Build the print cover wrap or digital cover meeting trim and bleed requirements, spine width derived from page count and paper stock, and channel thumbnail legibility.
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

# /product-build-cover

## Goal

Build the print cover wrap or digital cover meeting trim and bleed requirements, spine width derived from page count and paper stock, and channel thumbnail legibility.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Interior PDF is built and its final page count is confirmed (spine width depends on page count and paper stock).
- Cover brief, title typography, and cover art are approved and have rights records.
- Channel thumbnail size requirements are documented in the project plan.
- Trim size and bleed specifications are defined.

## Specialist delegation

Use these agents only for bounded assignments with exact input hashes, output paths, and acceptance tests:
- `art-director`
- `cover-designer`

## Procedure

1. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py project status $ARGUMENTS` and confirm the interior page count is final; do not calculate spine width from an estimated count.
2. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py build cover --project-id <id>` with the project ID resolved from `$ARGUMENTS`.
3. Calculate spine width using the confirmed page count and declared paper stock thickness formula from the channel print specification; record the formula, inputs, and result in the build log.
4. Confirm the full cover wrap (front, spine, back) meets the declared trim size and bleed (typically 0.125 in / 3 mm on all outer edges) with no live content inside the safety margin.
5. Confirm the cover art and title typography are readable at the channel's minimum thumbnail dimensions (e.g., 160 × 160 px equivalent); flag illegible spine text at narrow spine widths as a major finding.
6. Confirm color mode matches channel requirements (CMYK for offset print, RGB/sRGB for digital channels) and that art DPI meets the 300 DPI minimum for print.
7. Confirm AI-disclosure language required by the project plan is present on the cover or copyright page text, accurately reflecting the content generation method.
8. Delegate cover-art quality and brand-consistency review to `art-director`; delegate typography and legibility review to `cover-designer`.
9. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py artifact register` to register the cover PDF with its hash.
10. Queue preflight via `/product-build-proof`.

## Required outputs

- Cover wrap PDF with immutable hash.
- Build log (spine-width calculation, trim, bleed, color mode, DPI summary, thumbnail legibility check).
- Artifact registration receipt.
- Proof queue entry for `/product-build-proof`.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
