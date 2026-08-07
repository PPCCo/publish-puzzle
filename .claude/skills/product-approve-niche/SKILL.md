---
name: product-approve-niche
description: >-
  Grant or reject the niche gate against exact niche-assessment and product-brief hashes; on approval transition to PLANNING, on rejection return to NICHE_ASSESSMENT.
argument-hint: "<project-id>"
user-invocable: true
effort: high
model: '@bedrock-eus2/us.anthropic.claude-opus-4-8'
allowed-tools:
  - Read
  - Bash
  - AskUserQuestion
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-approve-niche

## Goal

Grant or reject the niche gate against exact niche-assessment and product-brief hashes; on approval transition to PLANNING, on rejection return to NICHE_ASSESSMENT.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Project is in NICHE_APPROVAL.
- Niche assessment artifact is recorded and hash is current.
- Product brief artifact is recorded and hash is current.
- Demand signals, competition analysis, and format viability findings are present in the assessment.

## Procedure

1. Run `project status <project-id>` and confirm the state is NICHE_APPROVAL.
2. Run `approval packet <project-id> --gate niche` to retrieve artifacts, hashes, viability scores, risk flags, and open findings.
3. Read `.claude/config/company.local.json` (falling back to `company.default.json`) to load `default_approver` (identity/role/decision/scope) and `auto_approve_gates`. Also read `human_action.review_files` and `human_action.next_command` from the packet — these carry the exact files to review and the equivalent manual command.
4. Present the **gate card** to the approver:

   ```
   ── NICHE GATE ──────────────────────────────────────────────
   Product:    <working_title>
   Audience:   <audience>  |  Format: <book_type>
   Demand:     <opportunity_score>  |  Competition: <tier>
   Differentiation: <key rationale from assessment>

   Evidence
     Niche assessment  <sha256 short>  PASS
     Product brief     <sha256 short>

   Open findings: <blocker>B  <major>M  <minor>m  <note>n
   ────────────────────────────────────────────────────────────
   ```

5. Show **file links** for artifacts produced at this gate:

   ```
   Files at this gate
     niche/assessment-latest.json   — niche demand assessment
     brief/product-brief.md         — approved product brief
   ```

6. Determine the approval action based on `auto_approve_gates`:
   - **`"silent"`** — record approval immediately using `default_approver` values; skip the prompt; show "Approved as <identity> (<role>)."
   - **`"auto"` / `"false"` (default)** — display the gate card and the review-files list, then collect the decision interactively (step 7). Under `"false"`, `default_approver` is shown as the pre-filled default the approver may override.

7. **Interactive decision** (skip entirely in `silent` mode). List the `review_files` (relative paths) inline so the human knows what to open, then call **`AskUserQuestion`**:
   - Question: "Approve the niche gate for <working_title>?"
   - Options:
     - **Approve** — recommended *only* when the packet's `ready_for_human_review` is true and there is no open blocker or major finding; records APPROVED with `default_approver`. If not ready, list the top risk in the option description and do not mark it Recommended.
     - **Reject** — records REJECTED; then ask for a rejection reason.
     - **Customize** — ask explicitly for approver identity, role, scope, and decision; use those values.
   - The user may also answer with free text via "Other" (e.g. an added scope note); append it to the default scope.
   - A selection here is an explicit human decision. The typed command in `next_command` (`/product-approve-niche <project-id>`) remains valid as the equivalent manual path.

8. Record the gate decision:
   ```
   python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py approval grant <project-id> \
     --gate niche \
     --approver <identity> \
     --approver-role <role> \
     --artifact <assessment-hash> \
     --artifact <brief-hash> \
     --scope "<scope>" \
     --decision APPROVED|REJECTED \
     [--notes "<notes>"]
   ```
9. On APPROVED: run `project transition <project-id> --to PLANNING`. Show brief confirmation and the next step.
10. On REJECTED: run `project transition <project-id> --to NICHE_ASSESSMENT` and state the corrective action required.

## Publishing guide (show after every gate action)

After recording the decision, render inline:

```
── WHAT'S READY ────────────────────────────────────────────
  niche/assessment-latest.json   Niche demand assessment
  brief/product-brief.md         Product brief

── NEXT STEP ───────────────────────────────────────────────
  Run /product-run <project-id> to continue to content planning.
────────────────────────────────────────────────────────────
```

## Required outputs

- Niche gate approval record with decision, approver, role, scope, and exact artifact hashes.
- State transition to PLANNING (approved) or NICHE_ASSESSMENT (rejected).
- Publishing guide rendered inline.
- Event log entry.

## Stop conditions

- Stop on invalid project state, stale artifact hashes, unresolved blocker, rights ambiguity, or tool failure.
- Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, gate result, approver used, and next valid action.
