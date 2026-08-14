---
name: product-approve
description: >-
  Grant or reject any craft/quality or compliance human gate (niche, interior, cover, compliance, listing) against exact SOURCE artifact hashes, honoring the auto_approve_gates policy and all safety overrides; on approval transition forward, on rejection route to the repair state. Release uses the separate /product-release-authorize skill.
argument-hint: "<gate> <project-id>   (gate: niche | interior | cover | compliance | listing)"
user-invocable: true
effort: medium
model: '@bedrock-eus1/us.anthropic.claude-sonnet-5'
allowed-tools:
  - Read
  - Bash
  - AskUserQuestion
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
---

# /product-approve

## Goal

Record a single human gate decision — for `niche`, `interior`, `cover`, `compliance`, or `listing` — against the exact SOURCE artifact hashes the code binds to that gate, honoring the `auto_approve_gates` policy and every safety override. On APPROVED, transition to the gate's forward state (interior additionally freezes its content source). On REJECTED, route to the repair state. This one skill replaces the five per-gate `product-approve-*` skills; **release authorization is intentionally separate** (`/product-release-authorize`) because of its nonce + two-approver + release-scope logic.

## Arguments

`$ARGUMENTS` is `<gate> <project-id>`. Parse the leading token as the gate (`niche`|`interior`|`cover`|`compliance`|`listing`); the remainder is the project ID. If the gate token is missing or is `release`, stop and tell the user: release uses `/product-release-authorize <project-id>`; the other four are handled here. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Per-gate table (the ONLY things that differ by gate)

| gate | required state | forward state (APPROVED) | repair state (REJECTED) | approval `--gate` |
|------|----------------|--------------------------|-------------------------|-------------------|
| niche | NICHE_APPROVAL | PLANNING | NICHE_ASSESSMENT | niche |
| interior | INTERIOR_APPROVAL | VISUAL_DEVELOPMENT | CONTENT_GENERATION | interior |
| cover | COVER_APPROVAL | LAYOUT_AND_FORMAT_BUILD | VISUAL_DEVELOPMENT | cover |
| compliance | COMPLIANCE_APPROVAL | METADATA_AND_COMMERCIAL_PACKAGE | RIGHTS_CLEARANCE | compliance |
| listing | LISTING_APPROVAL | FINAL_PROOF | METADATA_AND_COMMERCIAL_PACKAGE | listing |

Gate-specific notes:
- **interior** — APPROVAL FREEZES the content source. Bind and freeze SOURCE hashes only (content batch + verification + content-plan); the interior PDF does NOT exist yet — it is built afterward in LAYOUT_AND_FORMAT_BUILD from the frozen source. Never build or wait on the interior PDF here.
- **cover** — bind the cover SOURCE (art-direction) hash, NOT the cover PDF/proof (those are downstream build outputs and are intentionally excluded from the gate binding so a later re-render cannot invalidate the approval).
- **compliance** — HUMAN-DECIDED. A resolved mode of `"silent"` is downgraded to `"auto"` (never recorded without a human confirmation). Load `production.legal_defaults` from `project.yaml` and present them as the pre-filled posture the human confirms; ask only about deltas. `default_asset_rights_status: "unknown-blocks-release"` is NOT clearance. If accessibility is FAIL: stop before any prompt and route to the accessibility repair state. Escalate legal/safety findings; never resolve them autonomously.
- **listing** — include the truthful-claims outcome; state that NO pricing, text, or categories are submitted externally at this stage; note pricing is deferred to manual upload.

## Entry criteria

- A valid gate token and project ID matching `clr-YYYY-slug` are supplied.
- The project is in the gate's required state (see table); `project validate` passes.
- The gate's material evidence reports are recorded (the deterministic `gate_reports` for the edge already enforce this; e.g. niche assessment, content-verification + quality-gate for interior, cover proof for cover, rights + accessibility for compliance, metadata validation for listing).

## Procedure

1. Parse the gate and project ID from `$ARGUMENTS`. Run `project status <project-id>` and confirm the state equals the gate's required state (table). If not, stop and report the actual state and the correct next skill.
2. Run `approval packet <project-id> --gate <gate>` to retrieve the bound artifact hashes, the material evidence decisions, open findings, `ready_for_human_review`, `human_action.review_files` (the SINGLE source of the relative file paths to show), and `human_action.next_command`.
3. Read `.claude/config/company.local.json` (falling back to `company.default.json`) for `default_approver` and `auto_approve_gates`. Resolve the **effective mode for THIS gate**: if `auto_approve_gates` is a map, use `auto_approve_gates[<gate>]` (default `"false"` if absent); if it is a legacy plain string, use that string. **For compliance, downgrade `"silent"` → `"auto"`.** For compliance, also load `production.legal_defaults` (fall back to company `legal_defaults`).
4. Present the **gate card** — a compact header (product, audience/format or channels as relevant), the material evidence lines from the packet with their decisions and short hashes, and the open-findings tally (`<b>B <maj>M <min>m <note>n`). For compliance, add the accessibility/rights/AI-disclosure/child-safety check lines and a "Legal posture (pre-filled — confirm deltas)" block. For listing, add the metadata/limits/truthful-claims/pricing lines and the "No external submission at this stage" note. Use only values present in the packet/project; never invent a score, hash, or decision.
5. **Show the files to review** — print the packet's `human_action.review_files` verbatim as relative paths under a `── TO REVIEW ──` heading. This is the only file list; do not hand-maintain a separate example list.
6. **Compliance FAIL short-circuit:** if the gate is compliance and accessibility is FAIL, stop here — do not present any approval prompt. State the accessibility FAIL and run `project transition <project-id> --to ACCESSIBILITY_VALIDATION` (the repair route). End.
7. Act on the **resolved effective mode**:
   - **`"silent"`** (never compliance) — record APPROVED immediately with `default_approver`; skip the prompt; print the confirmation and the review-files list.
   - **`"auto"`** — show the gate card + review-files, then a single `AskUserQuestion` confirm.
   - **`"false"`** — show the gate card + review-files, then the interactive decision (step 8).
   - **Safety override (every mode, every gate):** if `ready_for_human_review` is false, or any open blocker or major finding exists — and for compliance also: rights-gate or accessibility not PASS/WARNING, any open child-safety flag, or AI-disclosure MISSING — do NOT auto-approve. Fall through to the interactive path and name the top risk. Never treat `not-run` as `pass`.
8. **Interactive decision** (skipped only in true `silent`). With the `review_files` already listed, call **`AskUserQuestion`**:
   - Question: "Approve the <gate> gate for <working_title>?" (interior adds "— approval freezes the content batch"; listing adds "— no pricing/text is submitted externally").
   - Options: **Approve** (mark Recommended ONLY when `ready_for_human_review` is true and no open blocker/major — and for compliance no safety condition is tripped; otherwise not Recommended and name the top risk in its description; records APPROVED with `default_approver`), **Reject** (then collect a reason; records REJECTED), **Customize** (collect approver identity, role, scope, decision).
   - Free-text "Other" is appended to the default scope. The selection is the explicit human decision; `next_command` is the equivalent manual path for headless runs. For compliance, escalate legal/safety findings — never resolve them autonomously.
9. **Record** the decision, binding the gate's SOURCE artifact hashes from the packet (the `approval` command scopes to the gate's bound types; pass every hash the packet lists as bound to this gate):
   ```
   ${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py approval grant <project-id> \
     --gate <gate> \
     --approver <identity> --approver-role <role> \
     --artifact <bound-source-hash> [--artifact <bound-source-hash> ...] \
     --scope "<scope>" \
     --decision APPROVED|REJECTED \
     [--notes "<notes>"]
   ```
   Use exactly the hashes the packet reports as bound to this gate — do NOT add a downstream build hash (interior/cover PDF, proof, package); those are intentionally not gate-bound.
10. **On APPROVED:** run `project transition <project-id> --to <forward state>` (table). For interior, confirm the content source hashes are now FROZEN. **On REJECTED:** state the specific defect and run `project transition <project-id> --to <repair state>` (or a more specific directed repair state the finding indicates).

## Publishing guide (render inline after every gate action)

```
── WHAT'S READY ────────────────────────────────────────────
  [finalized artifacts up to & including this gate, relative paths + one line; mark ✓ FROZEN where frozen]
── TO REVIEW ───────────────────────────────────────────────
  [the packet's human_action.review_files, relative paths]
── NEXT STEP ───────────────────────────────────────────────
  Run /product-run <project-id> to continue.
  Equivalent manual command: [packet human_action.next_command.command]
────────────────────────────────────────────────────────────
```
For interior, note the interior PDF is built next (LAYOUT_AND_FORMAT_BUILD) from the frozen source. For listing, add the pricing reminder (prices not set; entered manually at upload). For compliance, list the confirmed accessibility/rights/disclosure evidence.

## Required outputs

- Gate approval record with decision, approver, role, scope, and the exact SOURCE artifact hashes bound to the gate.
- State transition to the forward state (APPROVED) or the repair state (REJECTED); interior freeze confirmed on approval.
- Relative review-file paths shown (from the packet) at the decision.
- Publishing guide rendered inline; event log entry.

## Stop conditions

- Stop on invalid/mismatched state, stale artifact hashes, open blockers, rights ambiguity, accessibility FAIL (compliance), unsafe content, or tool failure that prevents a required check.
- Never silently skip a gate or treat `not-run` as `pass`. Never record compliance or any human-decided gate without an explicit human selection.
- Report partial work and the exact recovery action.

## Completion report

State the project, gate, result, approver used, frozen hashes (interior, on APPROVED), and next valid action.
