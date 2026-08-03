---
name: product-submit
description: >-
  Human-only: create a local submission dry-run or record a human-performed submission outcome for a prepared, release-authorized package; performs no autonomous network write, live publication, login, upload, or account action.
argument-hint: "<project-id> --channel <channel> --mode dry-run|record-manual [--status submitted|accepted|published|rejected|withdrawn|unknown] [--evidence <path-or-id>]"
user-invocable: true
disable-model-invocation: true
effort: medium
model: '@bedrock-eus1/us.anthropic.claude-haiku-4-5-20251001-v1:0'
allowed-tools:
  - Read
  - Bash
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-submit

## Goal

Human-only: create a local submission dry-run or record a human-performed submission outcome for a prepared, release-authorized package; performs no autonomous network write, live publication, login, upload, or account action.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Project is in READY_FOR_SUBMISSION.
- A valid release authorization exists for the specified channel, product, territory, and operation.
- Release-candidate artifact hashes match the authorized hashes exactly.
- Release authorization has not expired.

## Procedure

1. Run `project status <project-id>` and confirm the state is READY_FOR_SUBMISSION.
2. Run `approval release-verify <project-id> --channel <channel> --operation submit --hash <release-candidate-hash>` and confirm the authorization is valid, non-expired, and covers the specified channel, product, territory, and artifact hash. Do not proceed if verification fails.
3. For mode `dry-run`:
   a. Run `submission dry-run <project-id> --channel <channel>` with any additional channel-specific flags to generate and store the submission request payload locally.
   b. Present the dry-run output to the human for review: payload structure, metadata field mapping, artifact paths, pricing fields, territory scope, and any channel-specific warnings.
   c. Do not transmit the payload to any external endpoint. Do not log in, upload files, or accept any platform terms.
4. For mode `record-manual`:
   a. Require the human to supply externally obtained evidence: platform submission ID, submission timestamp, status, and optionally a screenshot path or confirmation reference. Do not invent these values.
   b. Record the outcome only from the evidence provided:
      ```
      python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py submission record <project-id> \
        --channel <channel> \
        --status <submitted|accepted|published|rejected|withdrawn|unknown> \
        [additional evidence flags as available]
      ```
   c. Mark the project state as PUBLISHED only when the human provides explicit platform evidence of live publication; never infer publication from a dry-run result or submission record alone.
5. Do not call live endpoints, store credentials, accept platform terms, purchase identifiers, or create external accounts at any point.

## Required outputs

- Dry-run payload stored locally with artifact and channel details (dry-run mode).
- Submission record with human-supplied evidence, platform ID, timestamp, and status (record-manual mode).
- Release-verify confirmation output.
- Explicit statement that no live network write or account action was performed.
- Event log entry.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
