---
name: product-listing-kit
description: >-
  Prepare a truthful, channel-compliant listing kit (title, subtitle, description, keywords/tags within channel limits, categories, and pricing recommendation) for KDP, Etsy, Gumroad, or generic; performs no external writes or live price commits.
argument-hint: "<project-id> [--channel <kdp|etsy|gumroad|generic>]"
user-invocable: true
effort: high
allowed-tools:
  - Read
  - Write
  - Bash
  - Agent
  - Skill
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-listing-kit

## Goal

Prepare a truthful, channel-compliant listing kit (title, subtitle, description, keywords/tags within channel limits, categories, and pricing recommendation) for KDP, Etsy, Gumroad, or generic; performs no external writes or live price commits.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Project ID resolves to a valid project in a state that permits listing preparation (e.g., interior and cover artifacts are registered).
- Product type, page count or file dimensions, niche, and target audience are recorded in project metadata.
- Any required rights-clearance or compliance gate has a current PASS result before claims are written into copy.
- Channel is supplied or the skill runs for all supported channels (kdp, etsy, gumroad, generic).

## Specialist delegation

Use these agents only for bounded assignments with exact input hashes, output paths, and acceptance tests:
- `listing-copywriter`
- `keyword-strategist`
- `pricing-strategist`

## Procedure

1. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py project status $ARGUMENTS` and confirm the project is in a list-eligible state with no unresolved blocking findings.
2. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py marketing listing --project-id <id> --channel <c>` for each requested channel; if no channel is specified, run `marketing kit --project-id <id>` to generate all channels in one pass.
3. Delegate to `listing-copywriter` to draft the title (max 200 chars KDP / 140 chars Etsy / 100 chars Gumroad), subtitle where supported, and channel-specific description using only features verifiable from registered artifacts. No superlatives, no competitor names, no trademarked third-party terms without rights evidence.
4. Delegate to `keyword-strategist` to produce keyword and tag sets within hard channel limits: KDP 7 keyword phrases, Etsy exactly 13 tags (each ≤ 20 chars), Gumroad exactly 10 tags. Flag any term that is a registered trademark or brand name for human review before inclusion.
5. Delegate to `pricing-strategist` to produce a pricing recommendation based on product type, page/file count, comparable market data, and royalty-rate projections. Label all prices explicitly as RECOMMENDATIONS — they are not committed or live.
6. Validate description length, keyword/tag counts, prohibited term list, and category path validity for each channel. FAIL the affected channel if any limit is violated; do not silently truncate.
7. Confirm `external_write_performed` is false. No listing is submitted, posted, or published by this skill.
8. Write the completed listing kit to `marketing/listing-kit-<channel>.yaml` (or `marketing/listing-kit-all.yaml` for the kit run) and record artifact hashes.

## Required outputs

- Per-channel listing kit YAML files with title, subtitle, description, keywords/tags, category paths, and pricing recommendation.
- Tag-count and character-limit validation report for each channel.
- Prohibited-term and trademark review log.
- Human action checklist for uploading each listing manually.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
