---
name: product-status
description: >-
  Show a project's current lifecycle state, active hashes, approvals, six-gate results, unresolved findings, missing artifacts, and next valid actions (read-only). Thin alias for /product-inspect --mode status.
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

# /product-status

Alias for the **status** lens. All logic lives once in the parameterized
**`product-inspect`** skill (mode=status reports the six-gate results, artifact
hash verification, stale approvals, open blockers, missing artifacts, and offers
the next step via `AskUserQuestion`).

## Procedure

Run the **`product-inspect`** skill with arguments `--mode status $ARGUMENTS`,
then follow its procedure exactly. Do not duplicate or diverge from that logic
here. Strictly read-only: never transition, approve, freeze, generate, build, or
package; never treat `not-run` as `pass`.
