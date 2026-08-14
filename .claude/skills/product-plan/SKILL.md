---
name: product-plan
description: >-
  Show the deterministic recommended next action, gate, blockers, missing artifacts, and producing skill or agent for a project (read-only). Thin alias for /product-inspect --mode plan.
argument-hint: "<project-id>"
user-invocable: true
effort: medium
model: '@bedrock-eus1/us.anthropic.claude-haiku-4-5-20251001-v1:0'
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - AskUserQuestion
  - Skill
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
---

# /product-plan

Alias for the **plan** lens. All logic lives once in the parameterized
**`product-inspect`** skill (mode=plan reads `autonomy_action` authoritatively and
handles PROCEED / STOP_AT_GATE / BLOCKED, offering the next step via
`AskUserQuestion`).

## Procedure

Run the **`product-inspect`** skill with arguments `--mode plan $ARGUMENTS`, then
follow its procedure exactly. Do not duplicate or diverge from that logic here.
Strictly read-only planning: never execute the recommended action, never record an
approval; never treat `not-run` as `pass`.
