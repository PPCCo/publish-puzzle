---
name: product-incident
description: >-
  Human-only: record a published-product incident (content error, rights complaint, safety report, platform action, or distribution irregularity) and route corrective action through code re-verification and the appropriate gate; may recommend but never performs unpublish, takedown, or external account action.
argument-hint: "<project-id> <incident description>"
user-invocable: true
disable-model-invocation: true
effort: high
allowed-tools:
  - Read
  - Write
  - Bash
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-incident

## Goal

Human-only: record a published-product incident (content error, rights complaint, safety report, platform action, or distribution irregularity) and route corrective action through code re-verification and the appropriate gate; may recommend but never performs unpublish, takedown, or external account action.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Project is in PUBLISHED or MONITORING state.
- A real or suspected incident has been reported or detected (content error in printed or digital pages, rights or originality complaint against interior art or cover art, child-safety or harmful-content flag, platform enforcement notice, distribution data anomaly, or accessibility regression).

## Procedure

1. Run `project status <project-id>` and record the current state, active channels, territory list, and artifact hashes on record.
2. Preserve all available evidence without modification: error screenshots, platform notice text, complaint reference IDs, affected page ranges or puzzle/coloring plate identifiers, timestamps, and external IDs. Do not delete any evidence.
3. Stop any queued automated or external actions that could compound the incident (e.g., scheduled submissions or re-submissions for the affected channel).
4. Classify the incident by impact type and severity:
   - **Content error**: factual mistake, puzzle solution error, incorrect coloring guide, or broken journal prompt in a distributed product.
   - **Rights complaint**: third-party originality or ownership claim against interior art, cover art, font usage, or reference data.
   - **Safety/child-safety report**: harmful, age-inappropriate, or dangerous content flagged by a reader, platform, or internal review.
   - **Platform action**: channel takedown notice, ASIN/listing suppression, policy violation, or distribution hold.
   - **Accessibility regression**: distributed product found to violate accessibility requirements that were previously cleared.
   - **Distribution irregularity**: pricing error, wrong-territory distribution, incorrect product variant live on channel.
5. Record known facts, unknowns, timestamps, artifact hashes of affected distributed versions, external IDs, and all decisions taken. Do not speculate about cause or liability.
6. Recommend a corrective transition appropriate to the severity:
   - For content errors requiring re-verification: recommend transitioning to EDITION_MAINTENANCE and routing fixes through `product-verify` and the interior gate before re-release.
   - For rights complaints: recommend halting further distribution of the affected edition pending qualified legal review; do not resolve ownership questions autonomously.
   - For safety or child-safety reports: recommend immediate escalation to a qualified human safety reviewer; do not clear safety flags autonomously.
   - For platform actions: recommend human review of the platform notice and qualified legal consultation before any response.
   - For accessibility regressions: route back through accessibility audit and compliance gate.
   - For distribution irregularities: recommend human review and correction via the platform dashboard; do not attempt autonomous platform edits.
7. Write an incident record file at a path provided or derived from the project directory, containing: incident ID, project ID, timestamp, reporter, classification, severity, affected channels/territories/artifact hashes, evidence index, recommended corrective action, and escalation contacts.
8. Run `project transition <project-id> --to EDITION_MAINTENANCE` only when directed by the human after reviewing the incident record and corrective recommendation.

## Required outputs

- Incident record file with all required fields.
- Evidence index listing all preserved artifacts, references, and timestamps.
- Severity classification and impact scope.
- Corrective action recommendation routed through appropriate re-verification and gate path.
- Explicit statement that no unpublish, takedown, or external account action has been performed.
- Event log entry.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
