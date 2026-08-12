---
name: product-analytics
description: >-
  Convert available post-publication performance data (sales, traffic, reviews, search ranking, conversion) into honest, confidence-labelled, actionable learning without fabricating attribution or overfitting small samples.
argument-hint: "<project-id>"
user-invocable: true
effort: high
model: '@bedrock-eus1/us.anthropic.claude-sonnet-5'
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Agent
  - Skill
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
---

# /product-analytics

## Goal

Convert available post-publication performance data (sales, traffic, reviews, search ranking, conversion) into honest, confidence-labelled, actionable learning without fabricating attribution or overfitting small samples.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Project ID resolves to a published or post-release product with at least one recorded performance data file.
- Data is available locally or through an approved read-only source; no live platform credentials are required by this skill.
- Customer privacy constraints and any platform data-use restrictions are confirmed before analysis begins.

## Specialist delegation

Use these agents only for bounded assignments with exact input hashes, output paths, and acceptance tests:
- `performance-analyst`
- `review-responder`

## Procedure

1. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py project status $ARGUMENTS` to confirm the product is in a post-release state and identify all registered performance data files and their hashes.
2. Delegate to `performance-analyst` to validate the data before any computation: check period boundaries, timezone consistency, currency normalization, granularity (daily/weekly/monthly), duplicate rows, missingness, and channel-specific metric definitions (e.g., KDP KENP pages read vs. unit sales, Etsy views vs. visits, Gumroad conversions). Flag any data-quality issue as a finding before proceeding.
3. Annotate the dataset with known external events: product launch date, price change dates, promotional campaigns, platform algorithm updates, and seasonal patterns relevant to the product niche (puzzles, coloring, journaling, printables). These annotations inform interpretation; they do not establish causation.
4. Delegate to `performance-analyst` to compute transparent descriptive metrics: units sold per period, revenue per period, conversion rate (views to purchases), return/refund rate, average review score and review velocity. Apply uncertainty appropriate to sample size — label each metric's confidence as HIGH (>90 data points), MEDIUM (20–90 data points), or LOW (<20 data points). Do not extrapolate trends from LOW-confidence windows.
5. Separate three evidence tiers explicitly in the report: (a) observed correlation, (b) plausible explanation consistent with data, (c) causal evidence (requires controlled test). Never present (a) or (b) as (c).
6. Aggregate or suppress review text and cohort data for groups of fewer than 5 customers to protect buyer privacy.
7. Delegate to `review-responder` to categorize qualitative review and Q&A feedback by theme (content accuracy, print quality, difficulty level, value-for-price, product description accuracy). Route any content-correctness finding (e.g., puzzle solution error, mislabelled page) back through the standard interior verification gate — do not silently note it; open a tracked finding.
8. Produce bounded recommendations labelled as FOR HUMAN ACTION: listing copy adjustments, tag/keyword experiments, pricing tests, or product-line candidates. Do not change live prices, listings, tags, or campaigns.

## Required outputs

- Data-quality report with per-file validation results and any flagged issues.
- Analysis report with reproducible metric calculations, confidence labels (HIGH/MEDIUM/LOW), and annotated event timeline.
- Evidence-tier summary separating correlation, plausible explanation, and causal evidence.
- Bounded recommendation list labelled FOR HUMAN ACTION.
- Any content-correctness findings opened as tracked blockers for interior re-verification.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
