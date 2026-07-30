---
name: product-marketing-guide
description: >-
  Produce per-channel manual upload and launch step guides verified against current official platform documentation; performs no external writes, spend, posting, or live account actions.
argument-hint: "<project-id> --channel <kdp|etsy|gumroad|generic>"
user-invocable: true
effort: high
allowed-tools:
  - Read
  - Write
  - Bash
  - WebSearch
  - WebFetch
  - Agent
  - Skill
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-marketing-guide

## Goal

Produce per-channel manual upload and launch step guides verified against current official platform documentation; performs no external writes, spend, posting, or live account actions.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Project ID resolves to a product with a completed and registered listing kit (output of `product-listing-kit`) for the requested channel.
- The channel package has been prepared locally (output of `product-package`) and its manifest hash is current.
- No unresolved blocking findings exist for the requested channel in the project event log.
- Channel is one of: kdp, etsy, gumroad, generic.

## Specialist delegation

Use these agents only for bounded assignments with exact input hashes, output paths, and acceptance tests:
- `metadata-specialist`

## Procedure

1. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py project status $ARGUMENTS` and confirm listing-kit and package artifacts are current with matching hashes for the requested channel.
2. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py marketing guide --project-id <id> --channel <channel>` to retrieve the stored guide scaffold and any previously recorded channel-specific notes for this product.
3. Use WebSearch and WebFetch to verify current official platform upload and listing requirements against the documentation sources below. Record the URL and retrieval date for each source consulted. If a source returns a non-200 status or is behind an authenticated wall, note it as unverified and flag for human review.
   - KDP: https://kdp.amazon.com/help (paperback/hardcover content guidelines, cover specifications, metadata requirements, pricing policy)
   - Etsy: https://www.etsy.com/legal/sellers/ and https://help.etsy.com/hc/en-us/categories/200327107 (digital download listing, tag and title policies, prohibited items)
   - Gumroad: https://help.gumroad.com/ (product setup, file requirements, pricing, payout)
   - Generic: record the channel name and note that official documentation must be supplied by the human operator.
4. Delegate to `metadata-specialist` to cross-check the registered listing kit fields (title, description, tags, categories, pricing recommendation) against the verified platform rules retrieved in step 3. Flag any field that exceeds a platform limit or uses a term prohibited by current policy. Do not auto-correct; open a finding for each discrepancy and route to human review.
5. Produce the channel-specific manual launch guide. Each guide MUST:
   - Be written as step-by-step instructions for a human operator to execute manually.
   - Reference the specific files from the local channel package by name and hash.
   - State explicitly that all steps are performed by a human in their own platform account.
   - Distinguish one-time setup steps (account, payment, tax) from per-product upload steps.
   - Include a pre-launch checklist (file sizes within limits, preview generation, pricing entered as recommendation only, listing preview reviewed before publishing).
   - Include a post-launch verification checklist (listing live, digital delivery tested, pricing confirmed, search indexing wait time noted).
   - Note the expected platform review or processing time (e.g., KDP 24–72 hours, Etsy near-instant for digital).
6. Confirm `external_write_performed` is false. No listing is posted, no file is uploaded, and no funds are committed by this skill.
7. Write the guide to `marketing/launch-guide-<channel>.md` and record its hash in the project event log.

## Required outputs

- Per-channel manual launch guide document with step-by-step upload instructions, pre-launch checklist, and post-launch verification checklist.
- Source verification log listing each official documentation URL, retrieval date, and verification status.
- Metadata discrepancy findings (if any) with severity and required human action.
- Human action summary confirming all steps require manual operator execution.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
