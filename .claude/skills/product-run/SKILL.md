---
name: product-run
description: >-
  Advance a project autonomously through valid stages between human gates, halting at each human gate to present the gate packet without granting approval.
argument-hint: "<project-id> [--until <STATE>]"
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
  - AskUserQuestion
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
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
- `commercial-writer` — builds KDP, Etsy, Gumroad, or generic channel listing metadata, keywords, and copy from approved product data.

## Procedure

1. Parse `$ARGUMENTS`; default to `--until human-gate` with a maximum of three completed stages; cap the requested stage count at five; reject unbounded execution with no stopping condition.
2. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py project validate $ARGUMENTS` and `project status $ARGUMENTS`; stop immediately on state divergence, stale artifact hashes, or unresolved blockers.
3. Begin the autonomous loop:
   a. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py project plan $ARGUMENTS` and read `autonomy_action`.
   b. If `autonomy_action` is `STOP_AT_GATE`: assemble and present the gate packet (design policy, product type, audience, formats, all produced artifact paths and hashes, validation results, open findings); render the publishing guide (see below); then follow "Gate decision (at every STOP_AT_GATE)" below. For an auto-approvable craft/quality gate with no safety override, invoke its approval skill (which records per `auto_approve_gates` policy) and continue; for a human-decided gate (compliance, release), a gate whose resolved mode is `false`, or any safety override, halt and let the human decide. Never fabricate a human decision or bypass a safety override.
   c. If `autonomy_action` is `BLOCKED`: report each blocker with its type and resolution; halt.
   d. If `autonomy_action` is `PROCEED`: delegate the recommended skill or agent with exact input hashes, output paths, acceptance criteria, and independence requirements. After completion, register produced artifacts with their hashes.
4. After each **transition**, run `project validate $ARGUMENTS` once (not after every intra-stage action). Do **not** re-run the full quality gate (`project next`) here if the stage's own skill already ran it — trust the recorded `reviews/quality-gate-latest.json` decision and reconcile from it. Only run `project next` yourself when no current quality-gate record exists for the stage. Reconcile any new findings before the next transition. (Safety rule unchanged: never treat a `not-run` required check as `pass` — if a required gate is genuinely `not-run`, run it.)
5. Transition state only through `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py project transition $ARGUMENTS --to <STATE>` after every blocker is cleared and every required check passes.
6. Re-read `state.json` and artifact hashes after every transition; never cache state across loop iterations.
7. You MAY invoke a craft/quality gate's approval skill (niche, interior, cover, listing) when its resolved `auto_approve_gates` mode auto-approves and no safety override applies — the approval skill records per policy and you continue. Never auto-decide the compliance or release gates, and never invoke freeze, release-authorization, listing-submission, or distribution skills autonomously; those halt for a human. Never fabricate a human decision or override a safety stop.
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
── TO REVIEW ───────────────────────────────────────────────
  [the packet's human_action.review_files, relative paths]
── NEXT STEP ───────────────────────────────────────────────
  A gate decision is needed (see the interactive prompt).
  Equivalent manual command: [the packet's human_action.next_command.command]
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

## Gate decision (at every STOP_AT_GATE)

First resolve the gate's effective `auto_approve_gates` mode (per-gate map value for this gate, or the legacy string; default `"false"`), then:

- **If the resolved mode auto-approves this gate** (`"silent"` or `"auto"`) **and no safety override applies** (the packet's `ready_for_human_review` is true and there is no open blocker/major finding; for compliance/release the gate's own safety conditions also hold): invoke the matching `/product-approve-<gate>` (or `/product-release-authorize`) skill, which records the approval per policy, then **continue the autonomous loop to the next stage**. Do not present the "Not now" stop for an auto-approved gate.
- **Otherwise** (resolved mode is `"false"`, the gate is human-decided — compliance/release — or a safety override triggered): present the interactive decision below and halt until the human decides. Compliance and release are never auto-approved silently; they always require a human confirmation.

### Interactive decision

After the gate packet and publishing guide, read the packet's `human_action.review_files` and `human_action.next_command`, then present the decision via **`AskUserQuestion`** rather than telling the user to re-type a command:

- Question: "The <gate> gate is ready for your decision on <working_title>. How do you want to proceed?"
- Options:
  - **Approve <gate>** — recommended **only** when the packet's `ready_for_human_review` is true (no open blocker or major finding); this invokes the matching `/product-approve-<gate>` (or `/product-release-authorize`) skill to record the decision. When not ready, do not mark it Recommended and name the top risk in the option description.
  - **Reject** — record a rejection (you will collect a reason) via the same approval skill.
  - **Not now** — stop and leave the project at the gate; the user can decide later with `next_command`.
- Recording still goes through the approval skill and binds the exact artifact hashes; `product-run` itself never writes an approval record directly. The `silent`/`auto`/`false` behavior is decided inside the approval skill from `auto_approve_gates`; `product-run` only decides whether to invoke it and continue (auto-approved, no override) or to halt for a human (human-decided gate, mode `false`, or safety override).
- The `next_command` slash form is always shown as the equivalent manual path for headless use.

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
