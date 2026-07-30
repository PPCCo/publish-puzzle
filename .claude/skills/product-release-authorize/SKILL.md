---
name: product-release-authorize
description: >-
  Human-only: record a two-person, time-limited release authorization bound to exact release-candidate artifact hashes, channels, products, territories, and operation scope; enables prepared submission dry-runs only and never performs live publication or commits external spend.
argument-hint: "<project-id> --approver <id1> --approver <id2> --channel <c> --product <p> --territory <t> --artifact <hash> --operation submit [--expires-at <ISO>] [--maximum-external-spend 0.0] [--currency USD]"
user-invocable: true
disable-model-invocation: true
effort: high
allowed-tools:
  - Read
  - Bash
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-release-authorize

## Goal

Human-only: record a two-person, time-limited release authorization bound to exact release-candidate artifact hashes, channels, products, territories, and operation scope; enables prepared submission dry-runs only and never performs live publication or commits external spend.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Project is in RELEASE_AUTHORIZATION.
- Final proof is current and recorded.
- Red-team review is current and recorded.
- All five upstream gates (niche, interior, cover, compliance, listing) have APPROVED decisions with non-stale artifact hashes.
- Release-candidate package artifacts exist for every requested channel with current SHA-256 hashes.
- Two distinct human approvers are available and identified.

## Procedure

1. Run `project status <project-id>` and confirm the state is RELEASE_AUTHORIZATION.
2. Run `approval packet <project-id> --gate listing` and verify that all upstream gate decisions are APPROVED and that no artifact hash has changed since those approvals.
3. Resolve and display the release-candidate package manifest for each requested channel: artifact path, SHA-256 hash, channel format spec compliance, product type, target territories, and permitted operation.
4. Present the full release packet to both approvers: product title, format type, release-candidate artifact hash(es), channels, products, territories, operation (submit), expiry, maximum-external-spend (must default to 0.0), and currency. Explicitly state: no funds are committed, no live network call is made, and no external account action is performed by this authorization.
5. Collect the two distinct approver identities, confirm they are not the same person, and confirm each has reviewed the release packet.
6. Record the release authorization:
   ```
   python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py approval release-authorize <project-id> \
     --approver <id1> \
     --approver <id2> \
     --channel <channel> \
     --product <product> \
     --territory <territory> \
     --artifact <release-candidate-hash> \
     --operation submit \
     --maximum-external-spend 0.0 \
     --currency USD \
     [--expires-at <ISO-timestamp>]
   ```
   Repeat `--channel`, `--product`, `--territory`, and `--artifact` flags as needed for multiple channels or territories.
7. Run `approval release-verify <project-id> --channel <channel> --operation submit --hash <release-candidate-hash>` and confirm the authorization is valid before proceeding.
8. On valid authorization: run `project transition <project-id> --to READY_FOR_SUBMISSION`.
9. If verification fails: do not transition; report the exact mismatch (stale hash, missing approver, expired authorization, or scope gap) and the required corrective action.

## Required outputs

- Release authorization record with both approver identities, channels, products, territories, artifact hashes, operation scope, expiry, and maximum-external-spend of 0.0.
- Release-verify confirmation output.
- State transition to READY_FOR_SUBMISSION.
- Explicit statement that no live publication, external spend, or account action has been performed.
- Event log entry.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
