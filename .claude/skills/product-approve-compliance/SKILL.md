---
name: product-approve-compliance
description: >-
  Grant or reject the compliance gate against AI-disclosure evidence, accessibility PASS or WARNING result, rights clearance, and child-safety review; on approval transition to METADATA_AND_COMMERCIAL_PACKAGE.
argument-hint: "<project-id>"
user-invocable: true
effort: medium
model: '@bedrock-eus1/us.anthropic.claude-sonnet-5'
allowed-tools:
  - Read
  - Bash
  - AskUserQuestion
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
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
3. Read `.claude/config/company.local.json` (falling back to `company.default.json`) to load `default_approver` and `auto_approve_gates`. Resolve the **effective mode for THIS gate (`compliance`)**: if `auto_approve_gates` is an object/map, use `auto_approve_gates["compliance"]` (default `"false"` if the key is absent); if it is a plain string (legacy), use that string for every gate. **Compliance is a human-decided gate:** a resolved mode of `"silent"` is downgraded to `"auto"` here — compliance is never recorded without a human confirmation. Also read `human_action.review_files` and `human_action.next_command` from the packet.
   Then load the project's `production.legal_defaults` from `project.yaml` (this was copied from company `legal_defaults` at init; fall back to company `legal_defaults` if the project block is absent). It carries the pre-filled `ai_disclosure` text, `rights_posture`, `originality_attestation_template`, and `child_safety_policy`. Present these as the **pre-filled decision** the human confirms; ask only about **deltas** (values the human wants to change) — do not re-collect posture that matches the defaults. These remain DEFAULTS, not clearances: never treat `default_asset_rights_status: "unknown-blocks-release"` as cleared, and always gate on the real accessibility/rights/child-safety evidence in the packet.
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

   Legal posture (pre-filled from production.legal_defaults — confirm or edit deltas)
     AI disclosure   "<ai_disclosure text, truncated>"
     Rights posture  line_art:<..>  fonts:<..>  word_lists:<..>  default_status:<..>
     Child safety    <policy line for this audience band, if a child band>

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

6. Act on the **resolved effective mode** (from step 3; `"silent"` was already downgraded to `"auto"`):
   - **`"auto"`** — show the gate card and the `review_files` list, then a single `AskUserQuestion` confirm (Approve recommended / Reject / Customize).
   - **`"false"`** — show the gate card and the `review_files` list, then collect the decision interactively (step 7). (If accessibility is FAIL, per step 4 you already stopped and never reach here.)
   - **Compliance safety override:** never present Approve as recommended (and never auto-confirm) if rights-gate or accessibility-gate is not PASS/WARNING, any child-safety flag is open, AI-disclosure is MISSING, or any open blocker/major finding exists — fall through to interactive and name the top risk. Escalate legal or safety findings; never resolve them autonomously. Never treat `not-run` as `pass`.

7. **Interactive decision** (skip in `silent` mode). List the `review_files` (relative paths) inline, then call **`AskUserQuestion`**:
   - Question: "Approve the compliance gate for <working_title>?"
   - Options: **Approve** (recommended only when `ready_for_human_review` is true and no open blocker/major; records APPROVED with `default_approver`), **Reject** (ask reason), **Customize** (ask approver identity, role, scope, decision).
   - Free-text "Other" is appended to the default scope. A selection is an explicit human decision; the `next_command` (`/product-approve-compliance <project-id>`) is the equivalent manual path. Escalate legal or safety findings — never resolve them autonomously.

8. Record the gate decision:
   ```
   ${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py approval grant <project-id> \
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
