---
name: product-approve-interior
description: >-
  Grant or reject the interior gate (content freeze) against exact verified-content and layout hashes; freezes those verified batches so later stages build only from the frozen set; on approval transition to VISUAL_DEVELOPMENT.
argument-hint: "<project-id>"
user-invocable: true
effort: medium
model: '@bedrock-eus1/us.anthropic.claude-haiku-4-5-20251001-v1:0'
allowed-tools:
  - Read
  - Bash
  - AskUserQuestion
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
---

# /product-approve-interior

## Goal

Grant or reject the interior gate (content freeze) against exact verified-content and layout hashes; freezes those verified batches so later stages build only from the frozen set; on approval transition to VISUAL_DEVELOPMENT.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Project is in INTERIOR_APPROVAL.
- Content verification for all interior batches has a recorded PASS decision.
- Quality gate is current with zero open blockers.
- Verified-content artifact hash and interior-PDF hash are both present in the project record.

## Procedure

1. Run `project status <project-id>` and confirm the state is INTERIOR_APPROVAL.
2. Run `approval packet <project-id> --gate interior` to retrieve artifact hashes, verification decision, quality gate result, and open findings.
3. Read `.claude/config/company.local.json` (falling back to `company.default.json`) to load `default_approver` and `auto_approve_gates`. Resolve the **effective mode for THIS gate (`interior`)**: if `auto_approve_gates` is an object/map, use `auto_approve_gates["interior"]` (default `"false"` if the key is absent); if it is a plain string (legacy), use that string for every gate. Also read `human_action.review_files` and `human_action.next_command` from the packet.
4. Present the **gate card**:

   ```
   ── INTERIOR GATE ───────────────────────────────────────────
   Product:    <working_title>
   Format:     <book_type>  |  Pages: <page_count>
   Puzzles:    <item_count> verified  |  Verification: PASS
   Quality:    <weighted_overall>/5.0  |  <blocker>B <major>M <minor>m

   Evidence
     Content batch     <sha256 short>  PASS  [frozen on approval]
     Verification      <sha256 short>  PASS
     Interior PDF      <sha256 short>
     Quality gate      <sha256 short>  PASS

   ⚠ Approval freezes the content batch — revisions need a new cycle.
   ────────────────────────────────────────────────────────────
   ```

5. Show **file links**:

   ```
   Files at this gate
     content/puzzles/sudoku-batch.json    — generated puzzle content (frozen on approval)
     verification/content-verification-latest.json  — code verification record
     outputs/interior/interior.pdf        — interior PDF
     reviews/quality-gate-latest.json     — quality gate result
   ```

6. Act on the **resolved effective mode** (from step 3):
   - **`"silent"`** — record approval immediately with `default_approver`; skip the prompt; print the confirmation and the `review_files` list.
   - **`"auto"`** — show the gate card and the `review_files` list, then a single `AskUserQuestion` confirm (Approve recommended / Reject / Customize).
   - **`"false"`** — show the gate card and the `review_files` list, then collect the decision interactively (step 7).
   - **Safety override (applies to every mode):** if the packet's `ready_for_human_review` is false, or any open blocker or major finding exists, do NOT auto-approve regardless of mode — fall through to the interactive path (step 7) and name the top risk. Never treat `not-run` as `pass`.

7. **Interactive decision** (skip in `silent` mode). List the `review_files` (relative paths) inline, then call **`AskUserQuestion`**:
   - Question: "Approve the interior gate for <working_title>? (Approval freezes the content batch.)"
   - Options: **Approve** (recommended only when `ready_for_human_review` is true and no open blocker/major; records APPROVED and freezes with `default_approver`; note that approval freezes content), **Reject** (ask reason), **Customize** (ask approver identity, role, scope, decision).
   - Free-text "Other" is appended to the default scope. A selection is an explicit human decision; the `next_command` (`/product-approve-interior <project-id>`) is the equivalent manual path.

8. Record the gate decision:
   ```
   ${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py approval grant <project-id> \
     --gate interior \
     --approver <identity> \
     --approver-role <role> \
     --artifact <verified-content-hash> \
     --artifact <interior-pdf-hash> \
     --scope "<scope>" \
     --decision APPROVED|REJECTED \
     [--notes "<notes>"]
   ```
9. On APPROVED: confirm that the listed hashes are now **frozen** — no further content changes without a new revision cycle. Run `project transition <project-id> --to VISUAL_DEVELOPMENT`.
10. On REJECTED: state the specific blocker and run `project transition <project-id> --to INTERIOR_APPROVAL` or the directed repair state.

## Publishing guide (show after every gate action)

```
── WHAT'S READY ────────────────────────────────────────────
  content/puzzles/sudoku-batch.json   ✓ FROZEN — 100 puzzles, code-verified
  outputs/interior/interior.pdf       ✓ FROZEN — 202-page print-ready interior

── NEXT STEP ───────────────────────────────────────────────
  Run /product-run <project-id> to continue to cover design.
────────────────────────────────────────────────────────────
```

## Required outputs

- Interior gate approval record with decision, approver, role, scope, and frozen artifact hashes (on APPROVED).
- State transition to VISUAL_DEVELOPMENT (approved) or repair state (rejected).
- Explicit confirmation that approved hashes are frozen.
- Publishing guide rendered inline.
- Event log entry.

## Stop conditions

- Stop on invalid state, stale artifact hashes, open blockers, or tool failure.
- Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, gate result, approver used, frozen hashes (on APPROVED), and next valid action.
