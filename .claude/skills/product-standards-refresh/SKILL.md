---
name: product-standards-refresh
description: >-
  Re-read active config, rules, and standards files and summarize the operative design policy for a project without modifying any artifact (read-only). Thin alias for /product-inspect --mode standards.
argument-hint: "[project-id]"
user-invocable: true
effort: medium
model: '@bedrock-eus1/us.anthropic.claude-haiku-4-5-20251001-v1:0'
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Skill
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
---

# /product-standards-refresh

Alias for the **standards** lens. All logic lives once in the parameterized
**`product-inspect`** skill (mode=standards runs `framework validate`, reads
config/rules/standards, and summarizes the operative policy; a project ID is
optional and adds the project overlay).

## Procedure

Run the **`product-inspect`** skill with arguments `--mode standards $ARGUMENTS`,
then follow its procedure exactly. Do not duplicate or diverge from that logic
here. Strictly read-only: modify no config, rule, standards, project, or artifact
file; never treat `not-run` as `pass`.
