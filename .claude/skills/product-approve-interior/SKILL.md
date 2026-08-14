---
name: product-approve-interior
description: >-
  Grant or reject the interior gate against the verified-content and verification-record SOURCE hashes; approval FREEZES the content source and transitions to VISUAL_DEVELOPMENT (the interior PDF is built afterward), rejection returns to CONTENT_GENERATION. Thin alias for /product-approve interior.
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

# /product-approve-interior

This is the per-gate alias for the **interior** gate. All gate logic lives once
in the parameterized **`product-approve`** skill. Interior specifics it already
encodes: approval binds and FREEZES the content SOURCE hashes only (content
batch + verification + content-plan); the interior PDF does **not** exist yet —
it is built afterward in LAYOUT_AND_FORMAT_BUILD from the frozen source, so this
gate never builds or waits on the interior PDF. APPROVED → VISUAL_DEVELOPMENT;
REJECTED → CONTENT_GENERATION.

## Procedure

Run the **`product-approve`** skill with arguments `interior $ARGUMENTS`, then
follow its procedure exactly. Do not duplicate or diverge from that logic here.

Resolve a project ID before changing project files. Do not invent human
approvals, credentials, prices, legal conclusions, or completed external actions.
Never build or wait on the interior PDF here; never silently skip a gate or treat
`not-run` as `pass`.
