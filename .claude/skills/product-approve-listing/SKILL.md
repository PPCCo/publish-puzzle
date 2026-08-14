---
name: product-approve-listing
description: >-
  Grant or reject the listing gate against exact metadata and listing-kit SOURCE hashes, with truthful-claims review; no pricing/text/categories are submitted externally at this stage. On approval transition to FINAL_PROOF. Thin alias for /product-approve listing.
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

# /product-approve-listing

This is the per-gate alias for the **listing** gate. All gate logic lives once in
the parameterized **`product-approve`** skill. Listing specifics it already
encodes: include the truthful-claims outcome; state that NO pricing, text, or
categories are submitted externally at this stage (pricing is deferred to manual
upload); bind the metadata + metadata-validation + listing-kit SOURCE hashes the
packet reports. APPROVED → FINAL_PROOF; REJECTED → METADATA_AND_COMMERCIAL_PACKAGE.

## Procedure

Run the **`product-approve`** skill with arguments `listing $ARGUMENTS`, then
follow its procedure exactly. Do not duplicate or diverge from that logic here.

Resolve a project ID before changing project files. Do not invent human
approvals, credentials, prices, legal conclusions, or completed external actions.
Never silently skip a gate or treat `not-run` as `pass`.
