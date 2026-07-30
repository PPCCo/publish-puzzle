---
name: product-build-interior
description: >-
  Assemble the print interior PDF from approved content and layout, enforcing even page count, back-only answer key placement, and correct trim and bleed settings.
argument-hint: "<project-id>"
user-invocable: true
effort: high
allowed-tools:
  - Read
  - Write
  - Bash
  - Agent
  - Skill
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-build-interior

## Goal

Assemble the print interior PDF from approved content and layout, enforcing even page count, back-only answer key placement, and correct trim and bleed settings.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Content artifact has passed `/product-verify` and `/product-quality-gate` at the required stage.
- Layout templates, fonts, and grid specifications are approved and have rights records.
- Trim size, bleed, margins, paper type, and page-count parity requirement are defined in the project plan.
- Coloring line art origination is confirmed original.

## Specialist delegation

Use these agents only for bounded assignments with exact input hashes, output paths, and acceptance tests:
- `layout-engineer`
- `coloring-line-artist`

## Procedure

1. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py project status $ARGUMENTS` and confirm content hash matches the approved artifact.
2. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py build interior --project-id <id>` with the project ID resolved from `$ARGUMENTS`.
3. Confirm the interior PDF is assembled in the correct page order: front matter, content pages (puzzles / coloring pages / journal prompts / printable pages), then answer keys grouped together in a back-only section.
4. Verify even page count (required for print binding); if the count is odd, add a declared blank page and record it in the build log.
5. Confirm trim size, bleed (typically 0.125 in / 3 mm), and safety-margin settings match the declared channel print specification.
6. Confirm all coloring line art pages use the approved line-weight settings and are embedded as vector or high-resolution raster at 300 DPI minimum.
7. Confirm all puzzle grids, clue sets, and journal prompt pages are paginated correctly with no truncated content.
8. Delegate coloring line art quality inspection to `coloring-line-artist` with exact page hash range; delegate layout integrity review to `layout-engineer`.
9. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py artifact register` to register the interior PDF with its hash.
10. Queue preflight via `/product-build-proof` before final approval.

## Required outputs

- Print interior PDF with immutable hash.
- Build log (page count, answer key section page range, blank-page insertions, DPI summary).
- Artifact registration receipt.
- Proof queue entry for `/product-build-proof`.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
