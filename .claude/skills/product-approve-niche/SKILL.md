---
name: product-approve-niche
description: >-
  Human-only: grant or reject the niche gate against exact niche-assessment and product-brief hashes; on approval transition to PLANNING, on rejection return to NICHE_ASSESSMENT.
argument-hint: "<project-id> --approver <identity> --approver-role <role> --artifact <assessment-hash> --artifact <brief-hash> --scope <text> [--decision APPROVED|REJECTED] [--exclusion <e>] [--notes <n>]"
user-invocable: true
disable-model-invocation: true
effort: high
allowed-tools:
  - Read
  - Bash
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-approve-niche

## Goal

Human-only: grant or reject the niche gate against exact niche-assessment and product-brief hashes; on approval transition to PLANNING, on rejection return to NICHE_ASSESSMENT.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Project is in NICHE_APPROVAL.
- Niche assessment artifact is recorded and hash is current.
- Product brief artifact is recorded and hash is current.
- Demand signals, competition analysis, and format viability findings are present in the assessment.

## Procedure

1. Run `project status <project-id>` and confirm the state is NICHE_APPROVAL.
2. Run `approval packet <project-id> --gate niche` to retrieve the current assessment and brief artifacts, their SHA-256 hashes, viability scores, risk flags, and any open findings.
3. Present to the approver: niche title, target audience, format type (puzzle/coloring/journal/printable), demand tier, competition density, differentiation rationale, safety and child-safety flags, rights exposure notes, and exact artifact hashes for both the assessment and the brief.
4. Require the approver to supply: approver identity, approver role, decision (APPROVED or REJECTED), scope statement, and any exclusions or notes. Do not infer or default these values.
5. Record the gate decision:
   ```
   python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py approval grant <project-id> \
     --gate niche \
     --approver <id> \
     --approver-role <role> \
     --artifact <assessment-hash> \
     --artifact <brief-hash> \
     --scope "<scope>" \
     --decision APPROVED|REJECTED \
     [--exclusion "<e>"] \
     [--notes "<n>"]
   ```
6. On APPROVED: run `project transition <project-id> --to PLANNING`.
7. On REJECTED: run `project transition <project-id> --to NICHE_ASSESSMENT` and state the corrective action required before resubmission.

## Required outputs

- Niche gate approval record with decision, approver, role, and scope.
- Exact artifact hashes recorded against the gate.
- State transition to PLANNING (approved) or NICHE_ASSESSMENT (rejected).
- Event log entry.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
