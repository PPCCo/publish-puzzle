---
name: product-run
description: >-
  Advance a project autonomously through valid stages between human gates, halting at each human gate to present the gate packet without granting approval.
argument-hint: "<project-id> [--until <STATE>]"
user-invocable: true
effort: high
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
  - Edit
  - Bash
  - Agent
  - Skill
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-run

## Goal

Advance a project autonomously through valid stages between human gates, halting at each human gate to present the gate packet without granting approval.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- A valid project ID matching the pattern `clr-YYYY-slug` is supplied.
- The project exists, validates cleanly, and is not currently blocked or awaiting a human gate.
- The user has supplied a finite stopping condition (`--until <STATE>`) or accepts the default maximum of three completed stages.

## Specialist delegation

Use these agents only for bounded assignments with exact input hashes, output paths, and acceptance tests:
- `product-content-generator` — produces puzzle grids, coloring page descriptions, journal prompts, or activity instructions as original content.
- `product-art-director` — specifies visual style, line-art density, and layout constraints for code-generated or verified original-only line art.
- `product-quality-reviewer` — verifies generated content against age-appropriateness, audience reading level, and safety criteria.
- `product-metadata-specialist` — builds KDP, Etsy, Gumroad, or generic channel listing metadata from approved product data.

## Procedure

1. Parse `$ARGUMENTS`; default to `--until human-gate` with a maximum of three completed stages; cap the requested stage count at five; reject unbounded execution with no stopping condition.
2. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py project validate $ARGUMENTS` and `project status $ARGUMENTS`; stop immediately on state divergence, stale artifact hashes, or unresolved blockers.
3. Begin the autonomous loop:
   a. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py project plan $ARGUMENTS` and read `autonomy_action`.
   b. If `autonomy_action` is `STOP_AT_GATE`: assemble and present the gate packet (design policy, product type, audience, formats, all produced artifact paths and hashes, validation results, open findings); then immediately render the publishing guide (see below); halt and wait for human review. Never approve, transition past, or simulate a gate approval.
   c. If `autonomy_action` is `BLOCKED`: report each blocker with its type and resolution; halt.
   d. If `autonomy_action` is `PROCEED`: delegate the recommended skill or agent with exact input hashes, output paths, acceptance criteria, and independence requirements. After completion, register produced artifacts with their hashes.
4. After each stage, run the applicable validator (`project validate $ARGUMENTS`) and quality gate (`python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py project next $ARGUMENTS`); reconcile any new findings before transitioning.
5. Transition state only through `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py project transition $ARGUMENTS --to <STATE>` after every blocker is cleared and every required check passes.
6. Re-read `state.json` and artifact hashes after every transition; never cache state across loop iterations.
7. Never invoke human-only gate-approval, freeze, release-authorization, listing-submission, or distribution skills.
8. Stop when the requested state or human-gate limit is reached, the stage cap is exhausted, a blocker cannot be resolved autonomously, or any required check is `not-run` and release policy requires it.
9. Write `projects/<id>/release/autonomous-run-latest.json` with completed stages, agents used, artifacts and hashes, validation decisions, stop reason, and next valid human action.

## Publishing guide (render at every STOP_AT_GATE)

After presenting the gate packet, always render a concise **"What's ready / Next steps"** section inline. Tailor to the gate:

**For all gates — "What's ready" table:**
Show the finalized artifacts produced up to and including this gate, with their paths relative to the project root and a one-line description. Mark frozen artifacts with ✓ FROZEN.

**For all gates — "Next step":**
One clear line: what the user should do right now (approve this gate, or the skill command to invoke).

**For gates niche / interior / cover / compliance / listing** — after the gate card, show:
```
── WHAT'S READY ────────────────────────────────────────────
  [path]   [description of artifact]
  ...
── NEXT STEP ───────────────────────────────────────────────
  Approve this gate to continue, or type REJECT.
  Invoke: /product-approve-<gate> <project-id>
────────────────────────────────────────────────────────────
```

**For the release gate** — additionally render a "Your Book Files" map showing exactly which files to use for each platform:
```
── YOUR BOOK FILES ─────────────────────────────────────────

FOR KDP UPLOAD
  Interior PDF       outputs/packages/kdp/print/interior.pdf
  Cover PDF          outputs/packages/kdp/print/cover.pdf
  Listing metadata   outputs/packages/kdp/listing.json
  Upload steps       outputs/packages/kdp/upload-checklist.md

FOR ETSY LISTING
  Printable PDF      outputs/packages/etsy/files/printable.pdf
  Listing data       outputs/packages/etsy/etsy-listing.json
  Listing steps      outputs/packages/etsy/listing-checklist.md

ADDITIONAL RESOURCES
  Launch guide       marketing/launch-guide.json
  Full metadata      metadata/book.json

── OPEN DECISIONS ──────────────────────────────────────────
  [list any unresolved human decisions: pricing, Etsy fulfilment, ISBN, series]
────────────────────────────────────────────────────────────
```

## Required outputs

- Bounded autonomous-run report (`autonomous-run-latest.json`) with completed stages, produced artifacts, and hashes.
- Validated state transitions for each completed stage.
- Explicit stop reason (gate reached, stage cap, blocker, or requested state reached).
- Gate packet presented at each human gate (niche, interior, cover, compliance, listing, or release).
- Next human decision or safe continuation command.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
