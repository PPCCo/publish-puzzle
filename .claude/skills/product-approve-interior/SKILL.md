---
name: product-approve-interior
description: >-
  Human-only: grant or reject the interior gate (content freeze) against exact verified-content and layout hashes; freezes those verified batches so later stages build only from the frozen set; on approval transition to VISUAL_DEVELOPMENT.
argument-hint: "<project-id> --approver <identity> --approver-role <role> --artifact <verified-content-hash> --artifact <layout-hash> --scope <text> [--decision APPROVED|REJECTED] [--exclusion <e>] [--notes <n>]"
user-invocable: true
disable-model-invocation: true
effort: high
allowed-tools:
  - Read
  - Bash
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-approve-interior

## Goal

Human-only: grant or reject the interior gate (content freeze) against exact verified-content and layout hashes; freezes those verified batches so later stages build only from the frozen set; on approval transition to VISUAL_DEVELOPMENT.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Project is in INTERIOR_APPROVAL.
- Content verification for all interior batches has a recorded PASS decision.
- Quality gate and accessibility check are current (no stale results).
- Verified-content artifact hash and layout artifact hash are both present in the project record.
- No open BLOCKER findings against interior content.

## Procedure

1. Run `project status <project-id>` and confirm the state is INTERIOR_APPROVAL.
2. Run `approval packet <project-id> --gate interior` to retrieve verified-content artifact hash, layout artifact hash, verification decision record, quality gate result, accessibility check result, and any open findings or accepted-risk notes.
3. Present to the approver: product title, format type (puzzle/coloring/journal/printable), page count, verified-content batch list with individual SHA-256 hashes, layout artifact hash, verification decision, quality gate outcome, accessibility outcome, open findings summary, and the consequence of approval (those exact hashes become the immutable frozen set for all downstream stages).
4. Require the approver to supply: approver identity, approver role, decision (APPROVED or REJECTED), scope statement covering the exact content batches, and any exclusions or notes. Do not infer or default these values.
5. Record the gate decision:
   ```
   python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py approval grant <project-id> \
     --gate interior \
     --approver <id> \
     --approver-role <role> \
     --artifact <verified-content-hash> \
     --artifact <layout-hash> \
     --scope "<scope>" \
     --decision APPROVED|REJECTED \
     [--exclusion "<e>"] \
     [--notes "<n>"]
   ```
6. On APPROVED: confirm to the approver that the listed artifact hashes are now frozen; any revision to interior content requires a new revision cycle and re-verification before the interior gate can be re-entered. Run `project transition <project-id> --to VISUAL_DEVELOPMENT`.
7. On REJECTED: state the specific finding that blocked approval and run `project transition <project-id> --to INTERIOR_APPROVAL` (or to the appropriate repair state as directed); do not freeze artifacts.

## Required outputs

- Interior gate approval record with decision, approver, role, scope, and frozen artifact hashes (on APPROVED).
- State transition to VISUAL_DEVELOPMENT (approved) or repair state (rejected).
- Written statement that the approved artifact hashes are frozen and immutable for downstream stages.
- Event log entry.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
