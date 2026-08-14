---
name: product-brief
description: >-
  Turn the intake/niche context into a structured product brief (audience, product family, formats, difficulty range, page and content-volume targets, channel intent) and register it so DISCOVERY can advance to NICHE_ASSESSMENT.
argument-hint: "<project-id>"
user-invocable: true
effort: medium
model: '@bedrock-eus1/us.anthropic.claude-sonnet-5'
allowed-tools:
  - Read
  - Write
  - Bash
  - Agent
  - AskUserQuestion
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
---

# /product-brief

## Goal

Produce a precise, internally consistent product brief that specifies audience band, product-type, format targets, channel targets, difficulty range, difficulty-progression structure, page-count target, content-volume target, and design-policy parameters — then register it as an artifact so the DISCOVERY stage can advance to NICHE_ASSESSMENT. The brief is grounded in the engine-derived design policy (rule 20) plus the advisory pipeline context in the intake note; it does not invent craft literals.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- A valid project ID matching the pattern `clr-YYYY-slug` is supplied.
- The project is in `DISCOVERY`, `project validate` passes, and an intake note is registered.

## Procedure

1. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py project status $ARGUMENTS` and confirm the state is `DISCOVERY`. Read `projects/<id>/project.yaml` (engine-derived `production.design`) and `projects/<id>/notes/intake.md` (supplied arguments + advisory pipeline context: difficulty, counts, positioning, SEO, series grouping).
2. Delegate the brief authoring to the **`acquisitions-editor`** agent with exact inputs and an explicit acceptance test:
   - Inputs: the project.yaml design block (authoritative craft policy — rule 20), the intake note's advisory pipeline context (labelled advisory, NOT approved craft values), and `.claude/config/age_bands.json` for the audience band.
   - Output path: `projects/<id>/notes/product-brief.md` (structured brief with every field from the acquisitions-editor output contract, or an explicit open-question flag per missing field).
   - Acceptance: every required brief field has a value or a documented open question; design-policy parameters are derived from the engine policy + age band (never hand-picked); the difficulty range and progression match the advisory plan (e.g. "single-tier easy" → single tier, no required intra-section gradient); rights/originality commitments stated affirmatively; competitive positioning sourced from the intake context; no live-market claims invented.
   - Independence: the acquisitions-editor authors the brief; it does NOT record any gate approval or transition state.
3. Read the returned brief. Confirm consistency with the engine-derived design policy and the intake audience/product-type/formats. Reconcile any discrepancy before registering (the engine policy wins on craft; rule 20).
4. Register the brief: `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py artifact register <id> notes/product-brief.md --type product-brief --stage DISCOVERY --actor claude-code`.
5. Report the brief's difficulty range/progression, page and content-volume targets, and any open questions the human still owns. Do NOT set `content_plan` literals in `project.yaml` here — those are populated at PLANNING by the content-architect from this brief.
6. This skill does NOT transition state or record an approval. Offer the next step via **`AskUserQuestion`** (Recommended option first): **Continue to niche assessment** (`/product-run <id>`, which runs `product-niche-assess` next) / **Review the brief first** (show the relative path `notes/product-brief.md`) / **Not now**.

## Required outputs

- `notes/product-brief.md` registered as a `product-brief` artifact.
- Difficulty range/progression, page and content-volume targets, and open questions reported.
- Confirmation the brief is consistent with the engine-derived design policy (rule 20).
- Next-step offer via `AskUserQuestion` (no state transition, no approval).

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- If the acquisitions-editor cannot fill a required field and no human-approved default exists, record it as an open question in the brief rather than inventing a value.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
