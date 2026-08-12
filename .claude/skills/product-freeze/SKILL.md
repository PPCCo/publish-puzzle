---
name: product-freeze
description: >-
  Human-only: freeze the exact verified-content and layout artifact hashes at the interior gate so all later stages build only from the frozen set; a new revision cycle is required to change any frozen artifact.
argument-hint: "<project-id> --approver <identity> --approver-role <role> --artifact <verified-content-hash> --artifact <layout-hash> --scope <text>"
user-invocable: true
disable-model-invocation: true
effort: high
model: '@bedrock-eus2/us.anthropic.claude-opus-4-8'
allowed-tools:
  - Read
  - Bash
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
---

# /product-freeze

## Goal

Human-only: freeze the exact verified-content and layout artifact hashes at the interior gate so all later stages build only from the frozen set; a new revision cycle is required to change any frozen artifact.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Interior gate approval has been granted for this project (gate `interior` decision is APPROVED).
- Verified-content artifact hash and layout artifact hash are current and match the hashes recorded in the interior gate approval.
- No BLOCKER findings are open against the verified-content or layout artifacts.

## Procedure

1. Run `project status <project-id>` and confirm the interior approval is present and current.
2. Run `approval packet <project-id> --gate interior` to retrieve the interior gate approval record, exact verified-content artifact hash, exact layout artifact hash, verification decision, and any accepted-risk exclusions recorded at approval time.
3. Present the full artifact set to the approver: product title, format type (puzzle/coloring/journal/printable), verified-content batch list with individual SHA-256 hashes, layout artifact hash, interior gate approval ID and timestamp, verification decision, and quality/accessibility status at the time of interior approval.
4. Confirm that the hashes presented match those in the interior approval record exactly. If any hash differs, stop immediately — the interior gate approval is stale and the freeze cannot proceed.
5. Require the approver to confirm: approver identity, approver role, and explicit acknowledgment that the listed artifact hashes will be frozen and immutable for all downstream stages (cover, compliance, listing, release, and submission). Do not infer or default these values.
6. Record the freeze via the gate record and artifact freeze command:
   ```
   ${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py approval grant <project-id> \
     --gate interior \
     --approver <id> \
     --approver-role <role> \
     --artifact <verified-content-hash> \
     --artifact <layout-hash> \
     --scope "<scope confirming freeze>" \
     --decision APPROVED \
     [--notes "Content freeze confirmed. Artifacts immutable for downstream stages."]
   ```
   If the interior gate approval record already exists and is APPROVED, use the artifact freeze mechanism available in the CLI to mark the artifacts frozen rather than re-running a duplicate approval.
7. State clearly in the completion report that the frozen artifact set is now immutable: any modification to a frozen interior artifact (page content, puzzle grid, coloring plate, journal prompt, layout file) requires opening a new revision, re-running content verification, and re-entering the interior gate before downstream work can resume. Cover, compliance, listing, and release records that reference frozen hashes remain valid only if the frozen hashes are unchanged.

## Required outputs

- Freeze record identifying the frozen artifact hashes, approver, role, scope, and timestamp.
- Interior gate approval reference confirming the approval that authorized the freeze.
- Explicit written statement: frozen artifacts are immutable and a new revision is required to change them.
- Downstream dependency baseline: list of stages that must be re-executed if frozen artifacts are ever superseded.
- Event log entry.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
