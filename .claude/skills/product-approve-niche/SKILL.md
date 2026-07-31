---
name: product-approve-niche
description: >-
  Grant or reject the niche gate against exact niche-assessment and product-brief hashes; on approval transition to PLANNING, on rejection return to NICHE_ASSESSMENT.
argument-hint: "<project-id>"
user-invocable: true
effort: high
allowed-tools:
  - Read
  - Bash
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
3. Read `.claude/config/company.local.json` (falling back to `company.default.json`) to load `default_approver` (identity/role/decision/scope) and `auto_approve_gates`.
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
   - **`"auto"`** — display the gate card, then show the interactive prompt (step 7) and wait for a single response.
   - **`"false"` (default)** — display the gate card, then show the interactive prompt (step 7) and wait for a full response. If `default_approver` is set, pre-fill the values as shown defaults that the approver may override.

7. **Interactive approval prompt** (skip entirely in `silent` mode):

   ```
   ── APPROVE NICHE GATE? ────────────────────────────────────
   Default approver: <identity> (<role>)
   Default scope:    <scope>

   Press ENTER   → Approve with defaults
   Type REJECT   → Reject (you will be asked for a reason)
   Type CUSTOM   → Set a different approver, role, or scope
   ───────────────────────────────────────────────────────────
   ```

   Wait for the approver's response. Handle:
   - Empty / ENTER → proceed as APPROVED with default values
   - `REJECT` (any case) → ask for rejection reason; proceed as REJECTED
   - `CUSTOM` (any case) → ask explicitly for approver identity, role, scope, decision; use those values
   - Any other text → treat as a scope note appended to the default scope

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
