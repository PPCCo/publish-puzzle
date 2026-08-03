---
name: product-approve-interior
description: >-
  Grant or reject the interior gate (content freeze) against exact verified-content and layout hashes; freezes those verified batches so later stages build only from the frozen set; on approval transition to VISUAL_DEVELOPMENT.
argument-hint: "<project-id>"
user-invocable: true
effort: high
model: '@bedrock-eus2/us.anthropic.claude-opus-4-8'
allowed-tools:
  - Read
  - Bash
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
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
3. Read `.claude/config/company.local.json` (falling back to `company.default.json`) to load `default_approver` and `auto_approve_gates`.
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

6. Determine action based on `auto_approve_gates`:
   - **`"silent"`** — record approval immediately with defaults; skip prompt.
   - **`"auto"`** — show gate card + interactive prompt; wait for response.
   - **`"false"`** — show gate card + interactive prompt with pre-filled defaults displayed.

7. **Interactive approval prompt** (skip in `silent` mode):

   ```
   ── APPROVE INTERIOR GATE? ─────────────────────────────────
   Default approver: <identity> (<role>)
   Default scope:    <scope>

   Press ENTER   → Approve and freeze content with defaults
   Type REJECT   → Reject (you will be asked for a reason)
   Type CUSTOM   → Set a different approver, role, or scope
   ───────────────────────────────────────────────────────────
   ```

   Handle ENTER → APPROVED with defaults; REJECT → ask reason; CUSTOM → ask fields.

8. Record the gate decision:
   ```
   python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py approval grant <project-id> \
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
