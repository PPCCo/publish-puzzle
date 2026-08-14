---
name: product-approve-cover
description: >-
  Grant or reject the cover gate against the cover SOURCE (art-direction) hash — not the downstream cover PDF/proof — verifying thumbnail legibility, trim/format compliance, and rights clearance; on approval transition to LAYOUT_AND_FORMAT_BUILD. Thin alias for /product-approve cover.
argument-hint: "<project-id>"
user-invocable: true
effort: medium
model: '@bedrock-eus1/us.anthropic.claude-sonnet-5'
allowed-tools:
  - Read
  - Bash
  - AskUserQuestion
  - Skill
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
---

# /product-approve-cover

This is the per-gate alias for the **cover** gate. All gate logic lives once in
the parameterized **`product-approve`** skill. Cover specifics it already
encodes: bind the cover SOURCE hash(es) the packet reports (art-direction), NOT
the cover PDF or proof (those are downstream build outputs, intentionally
excluded from the binding so a later re-render cannot invalidate the approval).
APPROVED → LAYOUT_AND_FORMAT_BUILD; REJECTED → VISUAL_DEVELOPMENT.

## Procedure

Run the **`product-approve`** skill with arguments `cover $ARGUMENTS`, then
follow its procedure exactly. Do not duplicate or diverge from that logic here.

Resolve a project ID before changing project files. Do not invent human
approvals, credentials, prices, legal conclusions, or completed external actions.
Never silently skip a gate or treat `not-run` as `pass`.
