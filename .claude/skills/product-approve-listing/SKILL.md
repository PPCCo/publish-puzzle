---
name: product-approve-listing
description: >-
  Human-only: grant or reject the listing gate against exact metadata and listing-kit artifact hashes, truthful-claims review, and pricing recommendation; on approval transition to FINAL_PROOF.
argument-hint: "<project-id> --approver <identity> --approver-role <role> --artifact <metadata-hash> --artifact <listing-kit-hash> --scope <text> [--decision APPROVED|REJECTED] [--exclusion <e>] [--notes <n>]"
user-invocable: true
disable-model-invocation: true
effort: high
allowed-tools:
  - Read
  - Bash
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-approve-listing

## Goal

Human-only: grant or reject the listing gate against exact metadata and listing-kit artifact hashes, truthful-claims review, and pricing recommendation; on approval transition to FINAL_PROOF.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Project is in LISTING_APPROVAL.
- Metadata artifact (title, subtitle, description, keywords, categories, BISAC codes) is recorded with a current SHA-256 hash.
- Listing-kit artifact (channel-specific listing copy, bullet points, A+ or enhanced content if applicable) is recorded with a current SHA-256 hash.
- Pricing recommendation is present for each target channel and territory.
- Channel character-limit and keyword-policy compliance check is recorded.

## Procedure

1. Run `project status <project-id>` and confirm the state is LISTING_APPROVAL.
2. Run `approval packet <project-id> --gate listing` to retrieve the metadata artifact hash, listing-kit artifact hash, channel-limit compliance results, pricing recommendation, truthful-claims review outcome, and any open findings.
3. Present to the approver: product title, subtitle, format type, target channels and territories, metadata artifact hash, listing-kit artifact hash, full description and keyword list (with character counts against channel limits), BISAC category assignments, channel-limit compliance result for each channel, truthful-claims review outcome (flag any superlatives, unsupported claims, or comparison statements), pricing recommendation per channel and territory with rationale, and any open exclusions or risk notes.
4. Confirm that no pricing values, listing text, or category selections will be submitted to any external platform at this stage — this is a local approval of prepared artifacts only.
5. Require the approver to supply: approver identity, approver role, decision (APPROVED or REJECTED), scope statement covering the metadata and listing-kit artifacts reviewed, and any exclusions or notes. Do not infer or default these values.
6. Record the gate decision:
   ```
   python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py approval grant <project-id> \
     --gate listing \
     --approver <id> \
     --approver-role <role> \
     --artifact <metadata-hash> \
     --artifact <listing-kit-hash> \
     --scope "<scope>" \
     --decision APPROVED|REJECTED \
     [--exclusion "<e>"] \
     [--notes "<n>"]
   ```
7. On APPROVED: run `project transition <project-id> --to FINAL_PROOF`.
8. On REJECTED: identify the specific issue (false claim, limit violation, missing BISAC, pricing concern) and run `project transition <project-id>` to the appropriate repair state; do not approve stale or channel-non-compliant listing artifacts.

## Required outputs

- Listing gate approval record with decision, approver, role, scope, and exact artifact hashes.
- Truthful-claims review outcome documented in the gate record.
- Pricing recommendation acknowledged and recorded (not submitted externally).
- State transition to FINAL_PROOF (approved) or repair state (rejected).
- Event log entry.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
