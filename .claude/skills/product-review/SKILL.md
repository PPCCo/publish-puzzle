---
name: product-review
description: >-
  Produce structured findings with severity, location, evidence, recommendation, acceptance test, and status for a target artifact from an independent review dimension.
argument-hint: "<project-id> --dimension <d> --artifact <path-or-hash>"
user-invocable: true
effort: high
model: '@bedrock-eus2/us.anthropic.claude-opus-4-8'
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
  - Agent
  - Skill
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-review

## Goal

Produce structured findings with severity, location, evidence, recommendation, acceptance test, and status for a target artifact from an independent review dimension.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- A complete artifact and its exact hash exist and are registered.
- The review dimension is selected from project risk profile and current stage.
- The reviewer has not produced the artifact under review (generator does not self-verify).

## Specialist delegation

Use these agents only for bounded assignments with exact input hashes, output paths, and acceptance tests:
- `quality-lead`
- `originality-auditor`
- `child-safety-reviewer`
- `accessibility-auditor`

## Procedure

1. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py project status $ARGUMENTS` and resolve the exact current artifact hash for the target artifact.
2. Confirm the reviewer agent is independent of the generator that produced the artifact; reject self-review assignments.
3. Assign the review dimension from `$ARGUMENTS`; valid dimensions include: solvability, solution_correctness, difficulty_accuracy, uniqueness, originality, audience_fit, child_safety, accessibility, rights_compliance, printable_spec, and line_art_originality.
4. Delegate the review to the appropriate specialist agent with: exact artifact hash, dimension schema, severity rubric, and stop criteria.
5. Require the reviewer to write a review JSON record containing: finding ID, severity (blocker / major / minor / info), artifact hash, item ID or page reference, evidence (quoted content or measured value), recommendation, acceptance test, and status (`open`).
6. Reject any finding that references a stale hash, lacks evidence, duplicates a closed finding with no new evidence, or fails schema validation.
7. For originality dimension: confirm coloring line art is designated original and not sourced from traceable third-party references; flag any uncertain provenance as a blocker.
8. For audience_fit and child_safety dimensions: verify theme, language register, and imagery are appropriate for the declared age range; any distressing or age-inappropriate content is a blocker.
9. Synthesize findings from multiple reviewer agents; preserve credible minority findings rather than discarding them; document conflicts in a conflict memorandum.
10. Write the consolidated review record to `reviews/<dimension>/<artifact-hash>.json` and queue repair via `/product-revise` for any blocker or major finding.

## Required outputs

- Structured review JSON file per dimension (findings with severity, evidence, acceptance tests, artifact hash).
- Conflict memorandum when reviewer agents disagree.
- Repair queue entries for blocker and major findings.
- Dimension score and recommendation (PASS / NEEDS_REVISION / FAIL).

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
