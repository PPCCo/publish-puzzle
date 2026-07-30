---
name: product-approve-compliance
description: >-
  Human-only: grant or reject the compliance gate against AI-disclosure evidence, accessibility PASS or WARNING result, rights clearance, and child-safety review; on approval transition to METADATA_AND_COMMERCIAL_PACKAGE.
argument-hint: "<project-id> --approver <identity> --approver-role <role> --artifact <compliance-packet-hash> --scope <text> [--decision APPROVED|REJECTED] [--exclusion <e>] [--notes <n>]"
user-invocable: true
disable-model-invocation: true
effort: high
allowed-tools:
  - Read
  - Bash
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-approve-compliance

## Goal

Human-only: grant or reject the compliance gate against AI-disclosure evidence, accessibility PASS or WARNING result, rights clearance, and child-safety review; on approval transition to METADATA_AND_COMMERCIAL_PACKAGE.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Project is in COMPLIANCE_APPROVAL.
- Accessibility gate result is recorded as PASS or WARNING (a FAIL blocks this gate; do not proceed).
- Rights check is recorded as clean, or all flagged items have documented resolutions.
- AI-disclosure statement is present if any content was produced or assisted by generative tools.
- Child-safety review is recorded if the product targets readers under 13 or depicts minors in any coloring art.

## Procedure

1. Run `project status <project-id>` and confirm the state is COMPLIANCE_APPROVAL.
2. Run `approval packet <project-id> --gate compliance` to retrieve the compliance packet hash, accessibility result, AI-disclosure record, rights clearance summary, child-safety review result, and any open findings or accepted-risk notes.
3. Present to the approver: product title, format type (puzzle/coloring/journal/printable), compliance packet artifact hash, accessibility result (PASS/WARNING) and outstanding warnings with their accepted-risk justifications, AI-disclosure statement text and scope, rights clearance status for all interior art, cover art, fonts, and third-party data, child-safety assessment outcome, and any open legal or regulatory flags that require human judgment.
4. Confirm that a FAIL on accessibility blocks this gate — do not proceed; return to the accessibility repair stage.
5. Require the approver to supply: approver identity, approver role, decision (APPROVED or REJECTED), scope statement covering the specific compliance evidence reviewed, and any exclusions (e.g., accepted WARNING items) or notes. Do not infer or default these values.
6. Record the gate decision:
   ```
   python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py approval grant <project-id> \
     --gate compliance \
     --approver <id> \
     --approver-role <role> \
     --artifact <compliance-packet-hash> \
     --scope "<scope>" \
     --decision APPROVED|REJECTED \
     [--exclusion "<e>"] \
     [--notes "<n>"]
   ```
7. On APPROVED: run `project transition <project-id> --to METADATA_AND_COMMERCIAL_PACKAGE`.
8. On REJECTED: identify the specific non-compliance (accessibility FAIL, missing AI disclosure, rights gap, child-safety concern) and run `project transition <project-id>` to the appropriate repair state; escalate legal or safety findings to qualified human reviewers rather than resolving them autonomously.

## Required outputs

- Compliance gate approval record with decision, approver, role, scope, and compliance packet hash.
- Documented resolution or accepted-risk notation for each WARNING item included in the approval scope.
- State transition to METADATA_AND_COMMERCIAL_PACKAGE (approved) or repair state (rejected).
- Event log entry.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
