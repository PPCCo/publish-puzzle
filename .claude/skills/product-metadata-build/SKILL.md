---
name: product-metadata-build
description: >-
  Produce accurate, channel-valid product metadata with truthful AI-disclosure and no misleading claims, using only counts and attributes verified in the built artifacts.
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

# /product-metadata-build

## Goal

Produce accurate, channel-valid product metadata with truthful AI-disclosure and no misleading claims, using only counts and attributes verified in the built artifacts.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Built interior PDF is registered with a confirmed page count and puzzle/item count.
- Rights gate has been cleared.
- Accessibility audit result (PASS or WARNING) is recorded.
- Channel metadata schema and character limits are documented in the project plan.

## Specialist delegation

Use these agents only for bounded assignments with exact input hashes, output paths, and acceptance tests:
- `metadata-specialist`
- `keyword-strategist`

## Procedure

1. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py project status $ARGUMENTS` and confirm the artifact inventory is complete and hashes are current.
2. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py artifact list <id>` to confirm the verified page count, puzzle/item count, difficulty distribution, and page size from the registered interior artifact; use only these verified counts in metadata — do not use planned or estimated values.
3. Draft product title, subtitle, and description using only claims supported by the artifact: puzzle type, count, difficulty labels (only those confirmed by verification), target audience, and page size.
4. Include truthful AI-disclosure language as required by the project plan and applicable channel policy; do not invent, minimize, or omit disclosure.
5. Do not include misleading marketing claims (e.g., "hundreds of puzzles" if the verified count is lower, "expert difficulty" if difficulty verification did not pass for all expert-labeled items).
6. Delegate keyword research and channel-specific category selection to `keyword-strategist` with a confirmed attribute summary; delegate metadata schema validation to `metadata-specialist`.
7. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py audit metadata --project-id <id>` to validate the drafted metadata against channel rules (title length, description length, keyword count limits, required fields, prohibited terms).
8. Resolve all validation errors; treat WARNING-level items as findings requiring a decision, not silent acceptance.
9. Register the final metadata artifact with its hash; the metadata artifact must reference the interior and cover artifact hashes it describes.
10. Do not set a price, publish, or submit the listing; record the metadata artifact as ready for the listing-kit or submission workflow.

## Required outputs

- Metadata artifact (title, subtitle, description, keywords, category, AI-disclosure, page count, item count, difficulty summary, page size, channel fields) with immutable hash.
- Metadata validation report from `audit metadata` (PASS / FAIL, finding IDs).
- Verified attribute summary (source artifact hashes for all counts used).

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
