---
name: product-gate-packet
description: >-
  Assemble a deterministic human-gate packet containing current active-artifact hashes, gate report decisions, open findings, invalidated approvals, scope summary, and required-approver count for a named gate; prepares only and grants nothing.
argument-hint: "<project-id> --gate <niche|interior|cover|compliance|listing|release>"
user-invocable: true
effort: medium
model: '@bedrock-eus1/us.anthropic.claude-haiku-4-5-20251001-v1:0'
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Agent
  - Skill
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-gate-packet

## Goal

Assemble a deterministic human-gate packet containing current active-artifact hashes, gate report decisions, open findings, invalidated approvals, scope summary, and required-approver count for a named gate; prepares only and grants nothing.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Project ID resolves to a valid project.
- The requested gate name is one of: niche, interior, cover, compliance, listing, release.
- All artifacts that feed into the gate are registered in the project event log (stale or missing artifacts are a blocking finding, not a silent skip).
- No prior gate packet for the same gate and artifact set is already awaiting human decision (duplicate packet prevention).

## Specialist delegation

Use these agents only for bounded assignments with exact input hashes, output paths, and acceptance tests:
- `human-collaboration-facilitator`
- `quality-lead`

## Procedure

1. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py project status $ARGUMENTS` to confirm current project state and identify any hash mismatches or stale approvals before packet assembly.
2. Run `python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py approval packet <id> --gate <gate>` to generate the structured gate packet from the current event log.
3. Delegate to `quality-lead` to verify that every artifact listed in the packet carries a current hash and that all preceding gate results referenced are themselves non-stale.
4. Delegate to `human-collaboration-facilitator` to format the packet for human review: present the gate scope (what is being decided), the set of active-artifact hashes under review, all prior gate report decisions relevant to this gate, every open finding with severity and owner, any approvals that have been invalidated by subsequent artifact changes, the required-approver count and role, and the explicit decision options available to the approver (APPROVE / REJECT / REQUEST CHANGES).
5. Record prominently that this skill grants no approval, makes no gate decision, and takes no action on behalf of any human approver. The packet is read-only input to a human decision process.
6. Write the assembled packet to `approvals/gate-packet-<gate>-<timestamp>.yaml` and record its hash in the project event log.
7. Emit the event `gate_packet_prepared` with gate name, packet hash, and required-approver count. Do not emit `gate_approved` or any approval event.

## Required outputs

- Gate packet YAML file with artifact hashes, gate report decisions, open findings, invalidated approvals, scope summary, and required-approver count.
- Human-readable gate briefing document stating scope, risks, and decision options.
- Event log entry confirming packet preparation with hash.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, missing required approval, unresolved blocker, rights ambiguity, unsafe content, or tool failure that prevents a required check.
- Report partial work and the exact recovery action. Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, current stage, agents used, files and hashes created, validation/gate results, unresolved findings, and next valid action.
