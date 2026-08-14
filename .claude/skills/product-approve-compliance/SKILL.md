---
name: product-approve-compliance
description: >-
  Grant or reject the HUMAN-DECIDED compliance gate against AI-disclosure, accessibility (PASS/WARNING; FAIL blocks), rights clearance, and child-safety evidence, with legal_defaults pre-filled for confirmation; on approval transition to METADATA_AND_COMMERCIAL_PACKAGE. Thin alias for /product-approve compliance.
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

# /product-approve-compliance

This is the per-gate alias for the **compliance** gate. All gate logic lives once
in the parameterized **`product-approve`** skill. Compliance specifics it already
encodes: this gate is HUMAN-DECIDED — a resolved mode of `"silent"` is downgraded
to `"auto"` (never recorded without a human confirmation); `production.legal_defaults`
is loaded and presented as the pre-filled posture the human confirms (ask only
about deltas); `default_asset_rights_status: "unknown-blocks-release"` is NOT
clearance; if accessibility is FAIL the gate short-circuits and routes to the
accessibility repair state before any prompt; legal/safety findings are escalated,
never resolved autonomously. APPROVED → METADATA_AND_COMMERCIAL_PACKAGE;
REJECTED → RIGHTS_CLEARANCE (or the directed repair state).

## Procedure

Run the **`product-approve`** skill with arguments `compliance $ARGUMENTS`, then
follow its procedure exactly. Do not duplicate or diverge from that logic here.

Resolve a project ID before changing project files. Do not invent human
approvals, credentials, prices, legal conclusions, or completed external actions.
Never auto-record compliance without an explicit human decision; never treat a
FAIL/`not-run` accessibility or rights result as `pass`; escalate legal/safety
findings.
