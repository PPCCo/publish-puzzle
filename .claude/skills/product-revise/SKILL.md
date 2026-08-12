---
name: product-revise
description: >-
  Apply bounded, evidence-linked repairs to open verification and review findings and re-verify, respecting the 3-cycle and 5-repair convergence limits.
argument-hint: "<project-id> [finding IDs]"
user-invocable: true
effort: high
model: '@bedrock-eus1/us.anthropic.claude-sonnet-5'
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
  - Edit
  - Bash
  - Agent
  - Skill
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
---

# /product-revise

## Goal

Apply bounded, evidence-linked repairs to open verification and review findings and re-verify, respecting the 3-cycle and 5-repair convergence limits.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Project is in REVISION or a permitted repair stage.
- Open findings reference the current artifact hash.
- Revision cycle count is below the configured limit (maximum 3 cycles).
- Repair count within the current cycle is below the configured limit (maximum 5 repairs).

## Procedure

1. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py project status $ARGUMENTS` and confirm revision stage and cycle/repair counters.
2. Read open findings filtered to the finding IDs in `$ARGUMENTS` (or all open findings if none specified); group by compatible repair scope (e.g., solvability failures, duplicate items, difficulty mislabeling, DPI defects).
3. For each finding group, apply the minimum targeted repair that satisfies the acceptance test recorded in the finding; never overwrite the reviewed artifact — create a new revision.
4. Record each repaired item as `fixed-awaiting-verification` with: finding ID, repair description, item ID, change summary, and new artifact hash.
5. Increment the repair counter; if the limit of 5 repairs would be exceeded within the current cycle, stop and escalate to a human-approval stage.
6. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py verify --project-id <id>` against the revised artifact to confirm repairs resolved findings without introducing new failures.
7. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py quality evaluate --project-id <id>` to confirm quality thresholds are still met.
8. If the same finding re-fails after repair, do not attempt a third repair for that item in this cycle; record as `stagnant` and escalate.
9. On cycle completion, increment the revision cycle counter; if the maximum of 3 cycles is reached and blockers remain, halt and file an escalation finding.
10. Register the revised artifact and update the finding-resolution map.

## Required outputs

- Revised content artifact with new immutable hash.
- Finding-resolution map (finding ID, status, repair description, new hash).
- Updated revision cycle and repair counters.
- Re-verification result linked to the revised artifact hash.
- Escalation record for any stagnant or limit-exceeded findings.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
