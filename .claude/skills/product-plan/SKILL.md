---
name: product-plan
description: >-
  Show the deterministic recommended next action, gate, blockers, missing artifacts, and producing skill or agent for a project.
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

# /product-plan

## Goal

Show the deterministic recommended next action, gate, blockers, missing artifacts, and producing skill or agent for a project.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- A valid project ID matching the pattern `clr-YYYY-slug` is supplied.
- The project directory `projects/<id>/` exists and contains a readable `state.json`.

## Procedure

1. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py project plan $ARGUMENTS`.
2. Read the `autonomy_action` field from the plan output and treat it as authoritative:
   - `PROCEED` — the next stage is fully autonomous; report the recommended skill or agent and exact CLI command.
   - `STOP_AT_GATE` — a human gate (niche, interior, cover, compliance, listing, or release) is required. Assemble the packet (`approval packet <id> --gate <gate>`) and present the gate name, the packet location, the packet's `human_action.review_files` (relative paths to open), and the `human_action.next_command`. Then offer the next action via **`AskUserQuestion`** — e.g. "Prepare/decide the <gate> gate now" (invokes the matching approval skill, where the human decides) vs "Just show status" (stay read-only). Never record an approval from this skill.
   - `BLOCKED` — one or more blockers prevent progress; list each blocker with its type (missing artifact, failed validation, stale hash, rights ambiguity, unsafe content flag) and the resolution action.
3. Report the target state the plan recommends transitioning to, and the full list of required artifacts that must be produced or verified at that stage.
4. Identify the producing skill or agent (e.g., `product-generate`, `product-build-interior`, `product-build-cover`) that would execute the recommended action.
5. Do not execute the recommended action — this skill is read-only planning only.

## Required outputs

- Current lifecycle state and `autonomy_action` value.
- Recommended next action with the exact CLI command or skill invocation.
- Human gate notice if `autonomy_action` is `STOP_AT_GATE`, including gate name, gate packet path, the packet's `review_files`, and the `next_command`.
- Blocker list with resolution steps if `autonomy_action` is `BLOCKED`.
- Missing artifacts required at the next stage.
- Producing skill or agent for the recommended action.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
