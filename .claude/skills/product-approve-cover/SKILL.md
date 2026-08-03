---
name: product-approve-cover
description: >-
  Grant or reject the cover gate against exact cover artifact hashes, verifying channel thumbnail legibility, trim and format compliance, and rights clearance; on approval transition to LAYOUT_AND_FORMAT_BUILD.
argument-hint: "<project-id>"
user-invocable: true
effort: high
model: '@bedrock-eus2/us.anthropic.claude-opus-4-8'
allowed-tools:
  - Read
  - Bash
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-approve-cover

## Goal

Grant or reject the cover gate against exact cover artifact hashes, verifying channel thumbnail legibility, trim and format compliance, and rights clearance; on approval transition to LAYOUT_AND_FORMAT_BUILD.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Project is in COVER_APPROVAL.
- Cover PDF and cover-proof report are recorded with current SHA-256 hashes.
- Cover art originality confirmed (original-only; clearance recorded in rights ledger).
- Trim, bleed, and spine comply with target channel specs.

## Procedure

1. Run `project status <project-id>` and confirm the state is COVER_APPROVAL.
2. Run `approval packet <project-id> --gate cover` to retrieve cover artifact hashes, trim/bleed compliance, thumbnail legibility results, rights check, and open findings.
3. Read `.claude/config/company.local.json` (falling back to `company.default.json`) to load `default_approver` and `auto_approve_gates`.
4. Present the **gate card**:

   ```
   ── COVER GATE ──────────────────────────────────────────────
   Product:    <working_title>
   Trim:       <trim_size>  |  Spine: <spine_width_in>in
   Channels:   <channels>

   Evidence
     Cover PDF         <sha256 short>
     Cover proof       <sha256 short>  PASS
     Thumbnail legibility: <result per channel>
     Rights ledger     <sha256 short>  PASS  (fonts + cover art cleared)
     Originality:      ORIGINAL (AI-assisted, attestation recorded)

   Open findings: <blocker>B  <major>M  <minor>m  <note>n
   ────────────────────────────────────────────────────────────
   ```

5. Show **file links**:

   ```
   Files at this gate
     outputs/cover/cover-wrap.pdf          — full cover wrap PDF
     outputs/proof/cover-proof-report.json — proof report
     concepts/cover-art-direction.md       — art direction brief
     rights/ledger.json                    — rights clearance records
   ```

6. Determine action based on `auto_approve_gates` (silent / auto / false — same logic as other gates).

7. **Interactive approval prompt** (skip in `silent` mode):

   ```
   ── APPROVE COVER GATE? ────────────────────────────────────
   Default approver: <identity> (<role>)
   Default scope:    <scope>

   Press ENTER   → Approve with defaults
   Type REJECT   → Reject (you will be asked for a reason)
   Type CUSTOM   → Set a different approver, role, or scope
   ───────────────────────────────────────────────────────────
   ```

   Handle ENTER → APPROVED with defaults; REJECT → ask reason; CUSTOM → ask fields.

8. Record the gate decision:
   ```
   python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py approval grant <project-id> \
     --gate cover \
     --approver <identity> \
     --approver-role <role> \
     --artifact <cover-pdf-hash> \
     --artifact <cover-proof-hash> \
     --scope "<scope>" \
     --decision APPROVED|REJECTED \
     [--notes "<notes>"]
   ```
9. On APPROVED: run `project transition <project-id> --to LAYOUT_AND_FORMAT_BUILD`.
10. On REJECTED: state the specific defect and run `project transition <project-id> --to COVER_APPROVAL` or the directed repair state.

## Publishing guide (show after every gate action)

```
── WHAT'S READY ────────────────────────────────────────────
  outputs/cover/cover-wrap.pdf    ✓ Cover PDF (KDP full-wrap upload)
  concepts/cover-art-direction.md   Cover design brief

── NEXT STEP ───────────────────────────────────────────────
  Run /product-run <project-id> to continue to layout and format build.
────────────────────────────────────────────────────────────
```

## Required outputs

- Cover gate approval record with decision, approver, role, scope, and exact artifact hashes.
- Thumbnail legibility and trim compliance confirmed.
- State transition to LAYOUT_AND_FORMAT_BUILD (approved) or repair state (rejected).
- Publishing guide rendered inline.
- Event log entry.

## Stop conditions

- Stop on invalid state, stale artifact hashes, rights gap, or tool failure.
- Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, gate result, approver used, and next valid action.
