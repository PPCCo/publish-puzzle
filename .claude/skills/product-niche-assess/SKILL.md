---
name: product-niche-assess
description: >-
  Run the deterministic offline niche/market assessment for a project and register the assessment record so the niche gate has its material evidence.
argument-hint: "<project-id>"
user-invocable: true
effort: medium
model: '@bedrock-eus1/us.anthropic.claude-haiku-4-5-20251001-v1:0'
allowed-tools:
  - Read
  - Bash
  - AskUserQuestion
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
---

# /product-niche-assess

## Goal

Run the deterministic offline niche/market assessment for a project and register the assessment record (`niche/assessment-latest.json`) so the niche gate has its material evidence. This is an advisory, offline assessment from project config and conservative priors — the human niche gate remains the authority. No live market data is fetched.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, live market data, or completed external actions.

## Entry criteria

- A valid project ID matching the pattern `clr-YYYY-slug` is supplied.
- The project is in `NICHE_ASSESSMENT` (a product brief has been recorded).
- `project validate` passes and there are no unresolved blockers.

## Procedure

1. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py project status $ARGUMENTS` and confirm the state is `NICHE_ASSESSMENT` and a product brief artifact is registered.
2. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py niche $ARGUMENTS`. This deterministically writes `projects/<id>/niche/assessment-latest.json` (opportunity score, recommended differentiators, `human_inputs_required`, and a `PASS`/`REVIEW` decision). Treat the script `decision` as authoritative — do not override it with reasoning.
3. Confirm the file exists and its `decision` is one of `PASS`/`REVIEW` (the values the `NICHE_ASSESSMENT->NICHE_APPROVAL` gate report allows). If the record is missing or the decision is not allowed, stop and report it as a blocker with the relative path `niche/assessment-latest.json`.
4. If the assessment is not already a registered artifact, register it: `artifact register <id> niche/assessment-latest.json --type niche-assessment --stage NICHE_ASSESSMENT --actor claude-code`.
5. Report the opportunity score, recommended differentiators, and the `human_inputs_required` list verbatim — these are the questions the human niche-gate approver still owns; never treat them as answered.
6. This skill does NOT transition state or record the niche approval. Surface the next step (advance toward the niche gate) via **`AskUserQuestion`** (Recommended option first): **Continue to the niche gate** (`/product-run <id>`) / **Just show the assessment** / **Not now**.

## Required outputs

- `niche/assessment-latest.json` written and registered as a `niche-assessment` artifact.
- Reported opportunity score, differentiators, and `human_inputs_required`.
- Explicit statement that this is advisory/offline and the human niche gate is the authority.
- Next-step offer via `AskUserQuestion` (no state transition, no approval).

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
