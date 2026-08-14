---
name: product-resume
description: >-
  Reconstruct working context for an existing project and recommend the next valid action without repeating completed stages (read-only). Thin alias for /product-inspect --mode resume.
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

# /product-resume

Alias for the **resume** lens. All logic lives once in the parameterized
**`product-inspect`** skill (mode=resume reconstructs context from status + plan +
project.yaml + state.json + findings/approvals + event tail, detects hash
divergence before recommending work, and offers the next step via
`AskUserQuestion`).

## Procedure

Run the **`product-inspect`** skill with arguments `--mode resume $ARGUMENTS`,
then follow its procedure exactly. Do not duplicate or diverge from that logic
here. Strictly read-only: never replay completed stages unless a hash mismatch
invalidates them or the human requests a redo; never transition or approve; never
treat `not-run` as `pass`.
