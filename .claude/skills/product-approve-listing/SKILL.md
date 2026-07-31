---
name: product-approve-listing
description: >-
  Grant or reject the listing gate against exact metadata and listing-kit artifact hashes, truthful-claims review, and pricing recommendation; on approval transition to FINAL_PROOF.
argument-hint: "<project-id>"
user-invocable: true
effort: high
allowed-tools:
  - Read
  - Bash
  - "Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"
---

# /product-approve-listing

## Goal

Grant or reject the listing gate against exact metadata and listing-kit artifact hashes, truthful-claims review, and pricing recommendation; on approval transition to FINAL_PROOF.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Project is in LISTING_APPROVAL.
- Metadata artifact (title, description, keywords, categories, BISAC codes) is recorded with a current SHA-256 hash.
- Listing-kit artifact is recorded with a current SHA-256 hash.
- Channel character-limit and keyword-policy compliance check is recorded.

## Procedure

1. Run `project status <project-id>` and confirm the state is LISTING_APPROVAL.
2. Run `approval packet <project-id> --gate listing` to retrieve the metadata hash, listing-kit hash, channel-limit compliance, pricing recommendation, truthful-claims outcome, and open findings.
3. Read `.claude/config/company.local.json` (falling back to `company.default.json`) to load `default_approver` and `auto_approve_gates`.
4. Present the **gate card**:

   ```
   ── LISTING GATE ────────────────────────────────────────────
   Product:    <title>
   Channels:   <channels>  |  Format: <book_type>

   Metadata
     Title (chars):    <N>/<limit>
     Description:      <N> chars
     Keywords:         <N> — all within channel limits
     Categories:       <category 1> / <category 2>
     Truthful claims:  PASS  (no unsupported superlatives)
     Pricing:          Not set — to be entered manually at upload

   Evidence
     Metadata          <sha256 short>  PASS
     Listing kit       <sha256 short>

   Open findings: <blocker>B  <major>M  <minor>m  <note>n

   No pricing, text, or categories will be submitted externally at this stage.
   ────────────────────────────────────────────────────────────
   ```

5. Show **file links**:

   ```
   Files at this gate
     metadata/book.json              — canonical book metadata
     marketing/listing-kit.json      — channel listing copy
     marketing/launch-guide.json     — per-channel upload steps
   ```

6. Determine action based on `auto_approve_gates` (silent / auto / false — same logic as other gates).

7. **Interactive approval prompt** (skip in `silent` mode):

   ```
   ── APPROVE LISTING GATE? ──────────────────────────────────
   Default approver: <identity> (<role>)
   Default scope:    <scope>

   Press ENTER   → Approve with defaults
   Type REJECT   → Reject (you will be asked for a reason)
   Type CUSTOM   → Set a different approver, role, or scope
   ───────────────────────────────────────────────────────────
   ```

   Handle ENTER → APPROVED with defaults; REJECT → ask reason; CUSTOM → ask fields.

8. Record the gate decision:
   ```
   python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py approval grant <project-id> \
     --gate listing \
     --approver <identity> \
     --approver-role <role> \
     --artifact <metadata-hash> \
     --artifact <listing-kit-hash> \
     --scope "<scope>" \
     --decision APPROVED|REJECTED \
     [--notes "<notes>"]
   ```
9. On APPROVED: run `project transition <project-id> --to FINAL_PROOF`.
10. On REJECTED: identify the specific issue and run `project transition <project-id>` to the appropriate repair state.

## Publishing guide (show after every gate action)

```
── WHAT'S READY ────────────────────────────────────────────
  metadata/book.json          ✓ Canonical book metadata
  marketing/listing-kit.json  ✓ Listing copy for KDP / Etsy
  marketing/launch-guide.json   Per-channel upload steps (step-by-step)

── PRICING REMINDER ────────────────────────────────────────
  Prices are NOT set. You will enter them manually at upload time.
  KDP paperback: recommended $8.99–$12.99 for this page count.
  Etsy:          set at time of listing creation.

── NEXT STEP ───────────────────────────────────────────────
  Run /product-run <project-id> to continue to final proof and packaging.
────────────────────────────────────────────────────────────
```

## Required outputs

- Listing gate approval record with decision, approver, role, scope, and exact artifact hashes.
- Truthful-claims review outcome documented.
- Pricing noted as deferred to manual upload.
- State transition to FINAL_PROOF (approved) or repair state (rejected).
- Publishing guide rendered inline.
- Event log entry.

## Stop conditions

- Stop on invalid state, stale hashes, false claims, open blockers, or tool failure.
- Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, gate result, approver used, and next valid action.
