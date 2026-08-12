---
name: product-doctor
description: >-
  Check the local framework, model pin, dependencies, and optional production tools without making changes.
argument-hint: ""
user-invocable: true
effort: medium
model: '@bedrock-eus1/us.anthropic.claude-haiku-4-5-20251001-v1:0'
allowed-tools:
  - Read
  - Bash
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
  - WebSearch
  - WebFetch
---

# /product-doctor

## Goal

Check the local framework, model pin, dependencies, and optional production tools without making changes.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Run from the repository root.
- No project ID is required; this skill checks the framework environment, not a specific project.

## Procedure

1. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py doctor $ARGUMENTS`.
2. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py framework validate`.
3. Report required failures (Python version, schema files, CLI availability, model pin) separately from optional-tool warnings (PDF renderers, image processors, barcode generators, KDP/Etsy/Gumroad CLI tools).
4. Do not mark a missing optional production tool (e.g., a PDF compositor or line-art renderer) as a passed validation; report it as an optional-tool warning with its release impact.
5. Do not make any changes to configuration, dependencies, or framework files during this check.

### Research connectivity probe (per-tier)

This records, per research source, the cheapest retrieval tier that works, into
the gitignored manifest `.claude/config/research-connectivity.json`. `/research`
reads it to avoid wasting turns. All network happens through the reviewed
`ph_cli.py fetch` path (the quarantined `net/fetch.py`) or the `web_search` tool —
never loose `curl`.

6. Run `${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py doctor --probe-plan` to get the ordered per-source tier plan.
7. **Tier 1 (web_search tool):** make ONE cheap `WebSearch` (e.g. "large print sudoku 2026"). If it returns results, set `web_search_available: "true"`; if it fails/blocks, set `"false"`.
8. **Tier 2 (HTTP fetcher):** run `ph_cli.py fetch --allow-net search "large print sudoku"` and `ph_cli.py fetch --allow-net get https://www.kdpeasy.com/`. If either returns `status: 200` (not `disabled`), set `http_fetch_available: "true"`.
9. **Tier 3 (headless browser):** run `ph_cli.py fetch --allow-net probe amazon`. Read `best_tier`/`browser_available` to set `browser_available` for the manifest.
10. **Per source:** for each source in the probe plan, record `best_tier` = the cheapest tier that returned usable content (`cache` < `web_search` < `http` < `browser`); use `assisted` for login-gated data (bookbolt) and `manual` when every automated tier is blocked (typically amazon, etsy, gtrends).
11. Persist the manifest: pass the assembled JSON to `ph_cli.py connectivity write --json -` (stdin). It validates against schema and refuses malformed input.
12. Report a connectivity summary (per-tier availability + per-source best tier) SEPARATELY from the framework checks. A blocked source is informational, not a required failure. Never fabricate a probe result — if a probe was not run, record the source `status: "unknown"`.

## Required outputs

- Environment diagnostics: Python version, framework schema status, CLI availability, and model pin.
- Required failures listed with corrective commands.
- Optional-tool warnings listed with release-impact statement for each missing tool.
- Framework validate result (pass or list of violations).
- Research connectivity summary: per-tier availability (`web_search`, `http`, `browser`) and per-source best tier, written to `.claude/config/research-connectivity.json` (gitignored).

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
