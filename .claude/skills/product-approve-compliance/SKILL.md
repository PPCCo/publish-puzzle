---
name: product-approve-compliance
description: >-
  Grant or reject the compliance gate against AI-disclosure evidence, accessibility PASS or WARNING result, rights clearance, and child-safety review; on approval transition to METADATA_AND_COMMERCIAL_PACKAGE.
argument-hint: "<project-id>"
user-invocable: true
effort: high
model: '@bedrock-eus2/us.anthropic.claude-opus-4-8'
allowed-tools:
  - Read
  - Bash
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-approve-compliance

## Goal

Grant or reject the compliance gate against AI-disclosure evidence, accessibility PASS or WARNING result, rights clearance, and child-safety review; on approval transition to METADATA_AND_COMMERCIAL_PACKAGE.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Project is in COMPLIANCE_APPROVAL.
- Accessibility gate result is PASS or WARNING (FAIL blocks this gate).
- Rights check is clean or all flagged items have documented resolutions.
- AI-disclosure statement is present if any content used generative tools.

## Procedure

1. Run `project status <project-id>` and confirm the state is COMPLIANCE_APPROVAL.
2. Run `approval packet <project-id> --gate compliance` to retrieve compliance packet hash, accessibility result, AI-disclosure record, rights clearance summary, child-safety result, and open findings.
3. Read `.claude/config/company.local.json` (falling back to `company.default.json`) to load `default_approver` and `auto_approve_gates`.
4. Present the **gate card**:

   ```
   ── COMPLIANCE GATE ─────────────────────────────────────────
   Product:        <working_title>
   Audience:       <audience>  |  Format: <book_type>

   Compliance checks
     Accessibility   <PASS|WARNING|FAIL>  (type <Xpt>, high_contrast: <true|false>)
     Rights          <PASS>  (<N> assets cleared, 0 blocked)
     AI disclosure   <PRESENT|MISSING>
     Child safety    <n/a|PASS>

   Open findings: <blocker>B  <major>M  <minor>m  <note>n
   ────────────────────────────────────────────────────────────
   ```

   If accessibility is FAIL: stop immediately. Do not present the approval prompt. State: "Accessibility gate FAIL — return to accessibility repair before compliance can proceed." Run `project transition <project-id>` to the accessibility repair state.

5. Show **file links**:

   ```
   Files at this gate
     accessibility/gate-latest.json        — accessibility audit result
     rights/ledger.json                    — rights clearance ledger
     rights/gate-latest.json               — rights gate summary
     project.yaml                          — AI disclosure field (rights.ai_assistance_disclosure_required)
   ```

6. Determine action based on `auto_approve_gates` (silent / auto / false — same logic as other gates).

7. **Interactive approval prompt** (skip in `silent` mode):

   ```
   ── APPROVE COMPLIANCE GATE? ───────────────────────────────
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
     --gate compliance \
     --approver <identity> \
     --approver-role <role> \
     --artifact <accessibility-gate-hash> \
     --artifact <rights-gate-hash> \
     --scope "<scope>" \
     --decision APPROVED|REJECTED \
     [--notes "<notes>"]
   ```
9. On APPROVED: run `project transition <project-id> --to METADATA_AND_COMMERCIAL_PACKAGE`.
10. On REJECTED: identify the specific non-compliance and run `project transition <project-id>` to the appropriate repair state. Escalate legal or safety findings — do not resolve autonomously.

## Publishing guide (show after every gate action)

```
── WHAT'S READY ────────────────────────────────────────────
  accessibility/gate-latest.json   ✓ Accessibility PASS (18pt, high contrast)
  rights/ledger.json               ✓ All assets rights-cleared
  rights/gate-latest.json          ✓ Rights gate PASS

── NEXT STEP ───────────────────────────────────────────────
  Run /product-run <project-id> to continue to metadata and listing build.
────────────────────────────────────────────────────────────
```

## Required outputs

- Compliance gate approval record with decision, approver, role, scope, and artifact hashes.
- WARNING items documented with accepted-risk notation.
- State transition to METADATA_AND_COMMERCIAL_PACKAGE (approved) or repair state (rejected).
- Publishing guide rendered inline.
- Event log entry.

## Stop conditions

- Stop on accessibility FAIL, invalid state, stale hashes, open blockers, or tool failure.
- Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, gate result, approver used, and next valid action.
