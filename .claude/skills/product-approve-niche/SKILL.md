---
name: product-approve-niche
description: >-
  Grant or reject the niche gate against exact niche-assessment and product-brief hashes; on approval transition to PLANNING, on rejection return to NICHE_ASSESSMENT. Thin alias for /product-approve niche.
argument-hint: "<project-id>"
user-invocable: true
effort: medium
model: '@bedrock-eus1/us.anthropic.claude-haiku-4-5-20251001-v1:0'
allowed-tools:
  - Read
  - Bash
  - AskUserQuestion
  - Skill
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
---

# /product-approve-niche

This is the per-gate alias for the **niche** gate. All gate logic — mode
resolution (`auto_approve_gates`), the gate card, the packet's `review_files`
presentation, safety overrides, the interactive `AskUserQuestion` decision, the
`approval grant` recording bound to the niche SOURCE hashes (niche-assessment +
product-brief), and the transition (APPROVED → PLANNING, REJECTED →
NICHE_ASSESSMENT) — lives once in the parameterized **`product-approve`** skill.

## Procedure

Invoke `product-approve` with gate `niche` and the supplied project ID:
run the **`product-approve`** skill with arguments `niche $ARGUMENTS`, then
follow its procedure exactly. Do not duplicate or diverge from that logic here.

Resolve a project ID before changing project files. Do not invent human
approvals, credentials, prices, legal conclusions, or completed external actions.
Never silently skip a gate or treat `not-run` as `pass`.
