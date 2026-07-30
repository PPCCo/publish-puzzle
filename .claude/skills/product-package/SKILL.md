---
name: product-package
description: >-
  Prepare a deterministic, checksum-verified local channel package for KDP, Etsy, Gumroad, or generic from canonical release artifacts; performs no network write or live upload.
argument-hint: "<project-id> --channel <kdp|etsy|gumroad|generic>"
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

# /product-package

## Goal

Prepare a deterministic, checksum-verified local channel package for KDP, Etsy, Gumroad, or generic from canonical release artifacts; performs no network write or live upload.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Release authorization gate has a current PASS result for the project.
- All required canonical artifacts (interior PDF, cover PDF or image, metadata YAML) are registered with current hashes.
- The requested channel (kdp, etsy, gumroad, or generic) is supported for this product type (e.g., KDP requires paperback or hardcover trim dimensions; Etsy and Gumroad require digital-PDF instant-download assets).
- No unresolved blocking findings exist in the project event log.

## Specialist delegation

Use these agents only for bounded assignments with exact input hashes, output paths, and acceptance tests:
- `packaging-engineer`

## Procedure

1. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py project status $ARGUMENTS` and confirm release-authorization is current with no hash mismatches.
2. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py package --project-id <id> --channel <channel>` to assemble the local channel package from registered canonical artifacts.
3. Delegate to `packaging-engineer` to validate the assembled package: check that all required files for the channel are present (e.g., KDP interior PDF bleed/trim compliance, cover flat-file dimensions, Etsy/Gumroad zip bundle contents), that every file hash in the manifest matches the registered canonical source hash, and that metadata mapping is complete and correctly formatted for the channel.
4. Confirm `external_write_performed` is false. The package is a local artifact only; no file is transmitted, listed, or uploaded by this skill.
5. Generate the package manifest (file list with SHA-256 hashes), a preflight report (dimension checks, color-space checks, file-size limits, metadata completeness), and a manual submission checklist stating the exact steps a human must perform to upload the package to the channel.
6. Register the package manifest hash in the project event log and advance the project state only when all checks pass.

## Required outputs

- Self-contained local channel package directory or archive.
- Package manifest with SHA-256 checksums for every included file.
- Preflight report with per-check PASS/FAIL/WARNING results.
- Manual submission checklist for the human operator.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
