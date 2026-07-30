---
name: product-approve-cover
description: >-
  Human-only: grant or reject the cover gate against exact cover artifact hashes, verifying channel thumbnail legibility, trim and format compliance, and rights clearance; on approval transition to LAYOUT_AND_FORMAT_BUILD.
argument-hint: "<project-id> --approver <identity> --approver-role <role> --artifact <cover-print-hash> --artifact <cover-thumbnail-hash> --scope <text> [--decision APPROVED|REJECTED] [--exclusion <e>] [--notes <n>]"
user-invocable: true
disable-model-invocation: true
effort: high
allowed-tools:
  - Read
  - Bash
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-approve-cover

## Goal

Human-only: grant or reject the cover gate against exact cover artifact hashes, verifying channel thumbnail legibility, trim and format compliance, and rights clearance; on approval transition to LAYOUT_AND_FORMAT_BUILD.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Project is in COVER_APPROVAL.
- Cover print artifact and cover thumbnail artifact are recorded with current SHA-256 hashes.
- Cover art originality has been confirmed (original-only; no third-party licensed or AI-generated imagery without explicit clearance record).
- Trim size, bleed, and color profile comply with the target channel's print specifications.
- Rights check for all cover text, fonts, and graphic elements is recorded.

## Procedure

1. Run `project status <project-id>` and confirm the state is COVER_APPROVAL.
2. Run `approval packet <project-id> --gate cover` to retrieve cover print artifact hash, cover thumbnail artifact hash, trim/bleed specification compliance result, color profile result, channel thumbnail legibility result, rights check record, and any open findings.
3. Present to the approver: product title, format type, trim size, cover print artifact hash, cover thumbnail artifact hash, thumbnail legibility result for each target channel (e.g., KDP, IngramSpark), trim and bleed compliance result, spine width calculation (if applicable), color profile (CMYK/RGB) compliance, font rights and art rights clearance records, and any open exclusions or risk notes.
4. Require the approver to supply: approver identity, approver role, decision (APPROVED or REJECTED), scope statement covering the specific cover artifacts and channels reviewed, and any exclusions or notes. Do not infer or default these values.
5. Record the gate decision:
   ```
   python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py approval grant <project-id> \
     --gate cover \
     --approver <id> \
     --approver-role <role> \
     --artifact <cover-print-hash> \
     --artifact <cover-thumbnail-hash> \
     --scope "<scope>" \
     --decision APPROVED|REJECTED \
     [--exclusion "<e>"] \
     [--notes "<n>"]
   ```
6. On APPROVED: run `project transition <project-id> --to LAYOUT_AND_FORMAT_BUILD`.
7. On REJECTED: state the specific defect (legibility failure, trim non-compliance, rights gap, or art originality concern) and run `project transition <project-id> --to COVER_APPROVAL` or the directed repair state; do not approve stale or unchecked cover variants.

## Required outputs

- Cover gate approval record with decision, approver, role, scope, and exact artifact hashes.
- Thumbnail legibility and trim compliance confirmation.
- Rights clearance summary included in the record.
- State transition to LAYOUT_AND_FORMAT_BUILD (approved) or repair state (rejected).
- Event log entry.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
