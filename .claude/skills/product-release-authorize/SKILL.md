---
name: product-release-authorize
description: >-
  Record a time-limited release authorization bound to exact release-candidate artifact hashes, channels, products, territories, and operation scope; enables prepared submission dry-runs only and never performs live publication or commits external spend.
argument-hint: "<project-id>"
user-invocable: true
effort: high
model: '@bedrock-eus1/us.anthropic.claude-sonnet-5'
allowed-tools:
  - Read
  - Bash
  - AskUserQuestion
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
---

# /product-release-authorize

## Goal

Record a time-limited release authorization bound to exact release-candidate artifact hashes, channels, products, territories, and operation scope. Enables prepared submission dry-runs only. Never performs live publication or commits external spend.

## Arguments

Use the invocation arguments exactly as `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- Project is in RELEASE_AUTHORIZATION.
- Final proof is current and recorded.
- All five upstream gates (niche, interior, cover, compliance, listing) have APPROVED decisions.
- Channel packages exist for every configured sales channel with current SHA-256 hashes.

## Procedure

1. Run `project status <project-id>` and confirm the state is RELEASE_AUTHORIZATION.
2. Run `approval packet <project-id> --gate release` to retrieve the full release packet: all artifact hashes, channel packages, upstream gate statuses, and open findings.
3. Read `.claude/config/company.local.json` (falling back to `company.default.json`) to load `default_approver` and `auto_approve_gates`. Resolve the **effective mode for THIS gate (`release`)**: if `auto_approve_gates` is an object/map, use `auto_approve_gates["release"]` (default `"false"` if the key is absent); if it is a plain string (legacy), use that string for every gate. **Release is the highest-stakes human gate:** the recommended posture is `"false"`, and `"silent"` is valid only when the resolved required-approver count is 1 (see step 7). Also read `human_action.review_files` and `human_action.next_command` from the packet.
   Then load the project's `production.legal_defaults.release_scope_defaults` from `project.yaml` (copied from company `legal_defaults` at init; fall back to company `legal_defaults.release_scope_defaults`). Use it to **pre-fill** the release scope — `channels`, `territories`, `permitted_operations`, `maximum_external_spend` (default `0.0`), `currency` — presented for one-step human confirmation. **This is the single place legal/commercial release scope is confirmed before release.** The defaults never grant permission to accept legal terms or exceed the stated spend/territory/channel scope; `maximum_external_spend` stays `0.0` unless the human explicitly raises it, and any live publication/spend remains disabled regardless.
4. Resolve the number of required approvers from `human_gates.release` in company config (default 1 after `company.local.json` override).
5. Present the **release gate card**:

   ```
   ── RELEASE GATE ────────────────────────────────────────────
   Product:    <working_title>
   Edition:    <edition>  |  Channels: <channels>  |  Territory: WORLD

   All upstream gates
     Niche       APPROVED
     Interior    APPROVED  (content frozen)
     Cover       APPROVED
     Compliance  APPROVED  (accessibility PASS, rights PASS)
     Listing     APPROVED

   Release packages
     KDP     outputs/packages/kdp/package-manifest.json    WARNING (offline)
     Etsy    outputs/packages/etsy/package-manifest.json   WARNING (offline)

   Final proof
     Interior  202pp, min_type 18pt                        PASS
     Cover     spine 0.455in, wrap 17.705×11.25in          PASS

   Open findings: 0B  0M  1m  5n
   Minor: fnd-progression-generator-001 (uniform givens, accepted)

   ⚠ This authorizes submission preparation only. No live publication,
     external spend, or account action is performed.
   ────────────────────────────────────────────────────────────
   ```

6. Show the **"Your Book Files"** map:

   ```
   ── YOUR BOOK FILES ─────────────────────────────────────────

   FOR KDP UPLOAD
     Interior PDF       outputs/packages/kdp/print/interior.pdf
     Cover PDF          outputs/packages/kdp/print/cover.pdf
     Listing metadata   outputs/packages/kdp/listing.json
     Keywords           outputs/packages/kdp/keywords.txt
     Categories         outputs/packages/kdp/categories.json
     Upload steps       outputs/packages/kdp/upload-checklist.md

   FOR ETSY LISTING
     Printable PDF      outputs/packages/etsy/files/printable.pdf
     Listing data       outputs/packages/etsy/etsy-listing.json
     Listing steps      outputs/packages/etsy/listing-checklist.md

   ADDITIONAL RESOURCES
     Step-by-step guide marketing/launch-guide.json
     Full metadata      metadata/book.json

   ── RELEASE SCOPE (pre-filled from legal_defaults — confirm/override) ──
     Channels           <channels from release_scope_defaults>
     Territories        <territories>
     Operations         <permitted_operations>  (prepare/dry-run only)
     Max external spend <maximum_external_spend> <currency>   (0.0 = no spend)

   ── OPEN DECISIONS ─────────────────────────────────────────
     Pricing            Not set — enter at upload time on each platform
     ISBN               Not purchased — KDP assigns ASIN automatically
     Etsy fulfilment    This is a paperback; consider if Etsy digital listing
                        makes sense or if you want to use it as a POD referral
   ────────────────────────────────────────────────────────────
   ```

7. Act on the **resolved effective mode** (from step 3):
   - **`"silent"`** — record authorization immediately with `default_approver`; skip prompt. (Only valid when the resolved required-approver count is 1; if more than one approver is required, you cannot proceed silently — fall through to the interactive path and collect the additional distinct approver.)
   - **`"auto"`** — show the gate card, the "Your Book Files" map, and the `review_files` list, then a single `AskUserQuestion` confirm (Authorize recommended / Reject / Customize). Only valid when the required-approver count is 1; otherwise fall through to interactive to collect the additional distinct approver.
   - **`"false"`** — show the gate card, the "Your Book Files" map, and the `review_files` list, then collect the decision interactively (step 8).
   - **Safety override (applies to every mode):** if the packet's `ready_for_human_review` is false, or any open blocker or major finding exists, do NOT auto-authorize regardless of mode — fall through to interactive (step 8) and name the top risk. Never treat `not-run` as `pass`.

8. **Interactive decision** (skip in `silent` mode). List the `review_files` (relative paths) inline, then call **`AskUserQuestion`**:
   - Question: "Authorize release for <working_title>? (This authorizes submission preparation only — no live publication, spend, or account action.)"
   - Options: **Authorize** (recommended only when `ready_for_human_review` is true and no open blocker/major; records the authorization with `default_approver`), **Reject** (ask reason; do not authorize), **Customize** (ask explicitly for all approver identities and roles).
   - If the required-approver count is greater than 1, do not offer a one-click Authorize: you MUST collect that many **distinct** human identities (with the interior/compliance and commercial/operations role split from the two-person-release pattern). One person cannot fill both slots.
   - A selection is an explicit human decision; the `next_command` (`/product-release-authorize <project-id>`) is the equivalent manual path. Authorization never grants permission to accept legal terms or exceed the stated spend/territory/channel scope.

9. Record the release authorization. Collect all package manifest hashes and include them as `--artifact` flags:
   ```
   ${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py approval release-authorize <project-id> \
     --approver <identity> \
     [--approver <identity2> if required_approvers > 1] \
     --channel kdp --channel etsy \
     --product puzzle-book \
     --territory WORLD \
     --artifact <kdp-package-manifest-hash> \
     --artifact <etsy-package-manifest-hash> \
     --operation submit \
     --maximum-external-spend 0.0 \
     --currency USD
   ```
10. Run `approval release-verify <project-id> --channel kdp --operation submit --hash <kdp-package-manifest-hash>` to confirm the authorization is valid.
11. On valid: run `project transition <project-id> --to READY_FOR_SUBMISSION`. Show the publishing guide below.
12. On failure: report the exact mismatch and required corrective action. Do not transition.

## Publishing guide (show after authorization)

```
── READY FOR SUBMISSION ────────────────────────────────────

Your book is packaged and authorized. No files have been submitted
externally. You now upload manually using the files below.

FOR KDP (Amazon)
  1. Go to kdp.amazon.com → Add new title → Paperback
  2. Enter metadata from:   outputs/packages/kdp/listing.json
  3. Upload interior:       outputs/packages/kdp/print/interior.pdf
  4. Upload cover:          outputs/packages/kdp/print/cover.pdf
  5. Set pricing (not set — your decision)
  6. Order a physical proof before publishing
  7. Full checklist:        outputs/packages/kdp/upload-checklist.md

FOR ETSY
  1. Go to etsy.com/selling → Add a listing → Digital download
  2. Upload file:           outputs/packages/etsy/files/printable.pdf
  3. Use listing data from: outputs/packages/etsy/etsy-listing.json
  4. Set price (not set — your decision)
  5. Full checklist:        outputs/packages/etsy/listing-checklist.md

After submitting, record evidence with:
  /product-submit <project-id> --channel kdp|etsy
────────────────────────────────────────────────────────────
```

## Required outputs

- Release authorization record with approver(s), channels, products, territories, artifact hashes, operation scope, expiry, and maximum-external-spend of 0.0.
- Release-verify confirmation output.
- State transition to READY_FOR_SUBMISSION.
- "Your Book Files" map rendered inline.
- Full publishing guide rendered inline.
- Event log entry.

## Stop conditions

- Stop on invalid state, stale artifact hashes, missing upstream approvals, or tool failure.
- Never silently skip a gate or treat `not-run` as `pass`.

## Completion report

State the project, authorization result, approver(s) used, and publishing guide.
