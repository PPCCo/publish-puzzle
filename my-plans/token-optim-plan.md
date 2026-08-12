# Plan: Reduce time & token cost of the publishing framework (keep quality ≥ ~85%)

**Author intent:** The `.claude/` framework produces high-quality puzzle/printable products but
is too slow and too expensive per product. On the run of
`clr-2026-large-print-sudoku-for-seniors-easy-puzzles-with` it got stuck, re-reviewed and
re-worked, got confused about versioning/approval invalidation, and fanned out too many
Opus/xhigh agents per activity. The owner wants near-100% autonomous create→review→improve
with the human only reviewing the final product + a small set of legal decisions pushed to
just-before-release. **Hard constraint: do not sacrifice more than ~10–15% of output quality.**

This plan is self-contained: a fresh Claude session can execute it end-to-end without prior
context. It has **four independent workstreams (A–D)**. Each can ship on its own; recommended
order is A → B → C → D. All paths are relative to the repo root
`/Users/qaiser.abbas/Dev/my-repos/pub/pub-clr`.

---

## Evidence this plan is based on (verified, not assumed)

Traced from `projects/clr-2026-large-print-sudoku-for-seniors-easy-puzzles-with/events.ndjson`
(110 events for ONE book) and `state.json`:

- Content was **generated → verified → interior-built → proofed, then re-generated →
  re-verified → re-built** — two full content cycles before the interior gate.
- **3 approvals were invalidated** (`APPROVALS_INVALIDATED` ×3) late in the run, then
  interior+cover were rebuilt and **re-approved at the very end** by the human.
  `state.json.invalidated_approvals` lists `apr-interior-*`, `apr-cover-*`, `apr-compliance-*`.
- **8 `APPROVAL_RECORDED` + 6 `PROOF_BUILT`** events for a single product.

Root causes (all verified in code/config):

1. **Approval-invalidation churn** — `scripts/publishing_house/artifacts.py:96-98` auto-invalidates
   any approval bound to an artifact hash whenever an active artifact of the **same `type`** is
   re-registered with a new hash. Combined with `gate_packet.py:167-181` binding approvals to
   **every** active artifact (not just gate-relevant ones), and the lifecycle approving
   cover(state 8)/compliance(12)/listing(14) **before** LAYOUT_AND_FORMAT_BUILD(9)/FINAL_PROOF(15)/
   PLATFORM_PACKAGING(16) rebuild the interior/cover PDFs → late rebuilds mechanically revoke
   earlier approvals → re-approval loop.
2. **Too many human gates** — 6 human gates, all mandatory. `auto_approve_gates` exists in
   `config/company.local.json` but is a single global string (`false|auto|silent`) with **no
   per-gate granularity**, so "auto everything except release" is currently impossible.
3. **Legal/rights decisions scattered** — no company-wide legal-defaults block; territory/spend/
   channel scope, AI-disclosure, license posture, child-safety policy are collected ad-hoc at gates.
4. **Opus/xhigh on mechanical work** — approve skills, verification/audit agents, and the
   orchestrator run on Opus high/xhigh while only narrating deterministic `ph_cli.py` output.
5. **Over-fanned workflows** — `final-red-team` (~15 agents, one-adversary-per-audit),
   `product-multi-review` (8 one-per-dimension), `accessibility-audit-batch` (4 lenses running the
   same CLI), `difficulty-audit` (redundant).

**Already fixed (do NOT redo):** review-file paths ARE surfaced — `gate_packet.py:264-281` emits
project-root-relative `review_files`, and all approve skills list them (`product-approve-*/SKILL.md`
step where it reads `human_action.review_files`).

---

## Guardrails for ALL workstreams (read before editing anything)

- **Do NOT weaken safety/legal.** Keep independent review for: `originality-auditor`,
  `child-safety-reviewer`, `accessibility-auditor` (judgment slice), `quality-lead` (synthesis),
  and the code verifiers. The constitution rule "a generator never signs off its own verification"
  (`.claude/CLAUDE.md` §4/§7) MUST hold — do not let a producer agent approve its own output.
- **Do NOT touch deterministic invariants** in `rules/18-python.md`: seed determinism, SHA-256 of
  every artifact, JSON-schema validation, network-free core modules, no `shell=True`.
- **Model IDs** used in frontmatter (copy exactly):
  - Opus 4.8: `'@bedrock-eus2/us.anthropic.claude-opus-4-8'`
  - Sonnet 5: `'@bedrock-eus1/us.anthropic.claude-sonnet-5'`
  - Haiku 4.5: `'@bedrock-.../us.anthropic.claude-haiku-4-5-20251001-v1:0'` — copy the EXACT string
    from `.claude/agents/distribution/packaging-engineer.md` frontmatter (the only Haiku agent) so
    the region prefix matches this environment.
- **effort** values: `low | medium | high | xhigh | max`.
- After any Python change, run the unit tests (see "Verification" at the end). After any config/JSON
  change, run `python3 .claude/scripts/ph_cli.py project validate <id>` on a scratch project.
- **Back up before edits:** `git status` should be clean; commit or stash first so each workstream
  is a reviewable diff. Do NOT push unless the owner asks.

---

## WORKSTREAM A — Kill the approval-invalidation churn (biggest wall-clock + rework win)

**Goal:** Late PDF/package rebuilds MUST NOT invalidate an already-granted interior/cover/compliance/
listing approval. Achieve this by **scoping each gate's bound hashes to only that gate's material
artifacts** (source content/layout + that gate's proof), so a later rebuild of a *different*
artifact type never intersects an earlier gate's `artifact_hashes`.

### A1. Define per-gate binding sets (the core fix)

File: `.claude/scripts/publishing_house/gate_packet.py`

Currently `build_gate_packet` (lines ~164-181) binds `artifacts_under_review` to **all**
`active_artifacts`, and `human_action.artifact_hashes_to_bind` (line ~346) = all of them. Change it
so each gate binds only its own artifact **types**. Add a mapping near `_GATE_EVIDENCE` (line 30):

```python
# Which active-artifact TYPES each human gate approves (binds its approval to).
# Anything not listed here is intentionally excluded so a later rebuild of a
# different artifact type cannot invalidate this gate's approval.
_GATE_ARTIFACT_TYPES: dict[str, list[str]] = {
    "niche":      ["niche-assessment", "product-brief"],
    "interior":   ["content-sudoku", "content-verification", "content-plan"],  # SOURCE content, not the PDF
    "cover":      ["cover-art-direction"],                                     # cover DESIGN basis, not the print PDF
    "compliance": ["rights-ledger", "rights-gate", "accessibility-gate"],
    "listing":    ["metadata", "metadata-validation", "listing-kit"],
    "release":    [],   # release binds package-manifest hashes separately (unchanged logic)
}
```

> NOTE ON ARTIFACT TYPE NAMES: the exact `type` strings live in the project's
> `active_artifacts` map. Verify them first by reading a real project's `state.json`
> (`projects/clr-2026-large-print-sudoku-for-seniors-easy-puzzles-with/state.json` →
> `active_artifacts` keys). Observed keys there: `intake-note, product-brief, niche-assessment,
> content-plan, project-spec, content-sudoku, content-verification, interior-pdf, interior-proof,
> quality-review, quality-gate, cover-art-direction, cover-pdf, cover-proof, accessibility-gate,
> rights-ledger, rights-gate, metadata, metadata-validation, listing-kit, launch-guide,
> platform-package-kdp, platform-package-etsy`. Use the ACTUAL keys, and make the interior/cover
> gates bind to the SOURCE types (`content-sudoku`, `content-verification`, `cover-art-direction`)
> and **explicitly NOT** to `interior-pdf` / `cover-pdf` (those are what late stages rebuild).

Then in `build_gate_packet`, filter `artifacts_under_review` to the gate's types:

```python
allowed_types = _GATE_ARTIFACT_TYPES.get(gate)
for kind, digest in sorted(active.items()):
    entry = manifest.get(digest, {})
    if allowed_types is not None and kind not in allowed_types:
        continue   # not material to THIS gate; do not bind it
    artifacts_under_review.append({...})   # unchanged body
```

Keep `review_files` (lines ~264-281) computed from the **full** set OR from the gate's evidence +
bound artifacts — the human should still SEE the built PDF even though the approval isn't bound to
its hash. Recommended: keep listing the PDF in `review_files` (visibility) but exclude it from
`artifact_hashes_to_bind` (binding). Add a comment explaining the split.

### A2. Make the interior freeze bind to source content only

File: `.claude/scripts/publishing_house/approvals.py:89-93`

`grant_approval` freezes `record["artifact_hashes"]` on interior approval. After A1 those hashes are
the SOURCE content batches (`content-sudoku`, `content-verification`) — which is exactly what should
be frozen (the content-freeze point). Confirm the freeze still targets content, not the PDF. No code
change expected here beyond what A1 induces, but re-read to confirm the freeze set is correct.

### A3. (Defensive) Skip invalidation for downstream-only artifact types

File: `.claude/scripts/publishing_house/artifacts.py:96-98`

Even after A1, add a belt-and-braces guard: do not fire invalidation for artifact types that are
**pure downstream build outputs** and never a gate-binding type. Introduce a module-level set and
guard the call:

```python
# Artifact types that are downstream build outputs only; re-registering them must
# never invalidate an upstream gate approval (approvals bind to source hashes).
_DOWNSTREAM_BUILD_TYPES = {
    "interior-pdf", "interior-proof", "cover-pdf", "cover-proof",
    "platform-package-kdp", "platform-package-etsy", "platform-package-gumroad",
    "platform-package-generic", "launch-guide", "marketing-kit",
}
...
if previous_hash and previous_hash != digest and artifact_type not in _DOWNSTREAM_BUILD_TYPES:
    from .approvals import invalidate_approvals_for_hashes
    invalidate_approvals_for_hashes(root, project_id, [previous_hash], actor, f"Superseded by {digest}")
```

This makes the fix robust even if a future gate accidentally binds a PDF type. Keep A1 as the
primary fix; A3 is the safety net.

### A4. Rule/standard text alignment

The change is a **scoping clarification, not a relaxation** — approvals still invalidate on material
change to the *approved* material. Update wording so the constitution matches:

- `.claude/standards/artifact-contract.md:20` — clarify: "invalidates approvals whose scope includes
  the changed material" → add "Approvals bind to the *source* content/design/metadata artifacts they
  approve; re-rendering a downstream build output (interior/cover PDF, channel package) from an
  unchanged approved source does NOT invalidate the approval."
- `.claude/standards/approval-contract.md:5` — same clarification.
- `.claude/rules/03-artifact-provenance.md` — add one line: "Downstream build outputs (PDFs,
  packages) are distinct artifact types and are not bound by upstream gate approvals."

### A5. Tests

Add/extend `unittest` coverage (find the existing test dir; likely `.claude/scripts/tests/` or
alongside modules — search `grep -rl "unittest" .claude/scripts`):

- Test: grant interior approval → rebuild `interior-pdf` with a new hash → assert the interior
  approval is **still current** (`approval_is_current` True, not in `invalidated_approvals`).
- Test: change the SOURCE `content-sudoku` hash → assert interior approval **is** invalidated
  (the guard must not over-suppress).
- Test: `build_gate_packet(..., "interior")` → assert `artifact_hashes_to_bind` contains the content
  hashes and does NOT contain the `interior-pdf` hash.

**A — acceptance:** Run a full pipeline on a scratch project; `events.ndjson` shows **zero**
`APPROVALS_INVALIDATED` caused by late PDF/package rebuilds, and no gate is re-approved.

---

## WORKSTREAM B — Per-gate auto-approve (fewer human decisions)

**Goal:** Default posture = Claude auto-approves the craft/quality gates when their deterministic
evidence PASSes and there are no open blockers/majors; human decides only **compliance** and
**release**. Owner can override per gate in local config.

### B1. Config: turn `auto_approve_gates` into a per-gate map

File: `.claude/config/company.default.json` — ADD (this is the checked-in template; safe defaults):

```json
"auto_approve_gates": {
  "niche": "silent",
  "interior": "silent",
  "cover": "silent",
  "listing": "silent",
  "compliance": "auto",
  "release": "false"
},
```

Values per gate: `"silent"` = record with `default_approver`, no prompt; `"auto"` = show card +
one-tap confirm; `"false"` = full interactive collection. `default_approver` also belongs in
`company.default.json` (currently only in local) so the template is self-sufficient — copy the block
from `config/company.local.json`:

```json
"default_approver": {
  "identity": "PPC", "role": "publisher", "decision": "APPROVED",
  "scope": "reviewed and accepted the content"
},
```

File: `.claude/config/company.local.json` — REPLACE the string
`"auto_approve_gates": "false"` with the same per-gate map (owner's live override). Keep
`human_gates.release: 1` as-is unless the owner wants 2 approvers.

**Backward compatibility:** the skills must accept BOTH the old string form and the new map form.
See B2.

### B2. Update all 6 approval skills to read the per-gate value

Files (identical edit pattern in each):
- `.claude/skills/product-approve-niche/SKILL.md`
- `.claude/skills/product-approve-interior/SKILL.md`
- `.claude/skills/product-approve-cover/SKILL.md`
- `.claude/skills/product-approve-compliance/SKILL.md`
- `.claude/skills/product-approve-listing/SKILL.md`
- `.claude/skills/product-release-authorize/SKILL.md`

In each, find the step that reads `auto_approve_gates` (≈ step 3, "Read `company.local.json` … to
load `default_approver` and `auto_approve_gates`") and the step that branches on it (≈ step 6/7).
Replace the branch logic with:

> Resolve the effective mode for THIS gate `<gate>`:
> - If `auto_approve_gates` is an object/map, use `auto_approve_gates["<gate>"]` (default `"false"`
>   if the key is absent).
> - If `auto_approve_gates` is a string (legacy), use that string for every gate.
> Then act on the resolved mode: `"silent"` → record immediately with `default_approver`, skip the
> prompt, print the confirmation + review-file list; `"auto"` → show the gate card + review-files,
> then a single AskUserQuestion confirm (Approve recommended / Reject / Customize); `"false"` →
> full interactive collection.
> **Safety override (all gates):** if `ready_for_human_review` is false, or any open blocker/major
> finding exists, DO NOT auto-approve regardless of mode — fall through to interactive and name the
> top risk. For `compliance`, additionally never `silent` if rights-gate or accessibility-gate is
> not PASS/WARNING or any child-safety flag is open. For `release`, `silent` is only valid when the
> resolved required-approver count is 1 (already documented in
> `product-release-authorize/SKILL.md:100`).

Keep the existing `AskUserQuestion` block and the `approval grant` / `project transition` calls
unchanged. The CLI (`ph_cli.py approval grant`) still binds hashes and records the approver — this is
skill-layer behavior only, no Python change.

### B3. Amend the constitution so skills don't contradict it

The rules currently mandate a human decide EVERY gate. Amend to permit config-driven auto-approval
of craft gates while KEEPING compliance + release human. Edit:

- `.claude/CLAUDE.md` §11 ("A human must *decide* every gate") — change to: "A human MUST decide the
  **compliance** and **release** gates. Craft/quality gates (niche, interior, cover, listing) MAY be
  auto-approved by the configured `auto_approve_gates` policy when their deterministic gate evidence
  PASSes and no blocker/major finding is open; the human retains override and reviews the final
  product. Release still requires exact-hash human authorization."
- `.claude/rules/02-human-approval.md` — mirror the same split; keep the "never infer approval from
  silence" line but scope it to the gates that remain human.
- `.claude/rules/00-governance.md` — the "Stop autonomous work at human gates" bullet: qualify with
  "at the human-decided gates (compliance, release)".
- `.claude/rules/01-workflow-state.md` — the "Human gates are: niche, interior, cover, compliance,
  listing, release" line: add a note that niche/interior/cover/listing are auto-approvable by policy;
  compliance/release require a human decision.

> Keep the change **auditable**: an auto-approval still writes a real `APPROVAL_RECORDED` event with
> the `default_approver` identity. Add one line to §11: "Auto-approvals are recorded with the
> configured default approver identity and remain fully auditable in `events.ndjson`."

### B4. product-run gate handling

File: `.claude/skills/product-run/SKILL.md` — its STOP_AT_GATE logic already delegates recording to
the approve skill and says it "does not enter silent/auto behavior — that is decided inside the
approval skill." Confirm that when the approve skill auto-approves, `product-run` **continues** past
the gate instead of halting. Add: "If the gate's approve skill records an approval (silent/auto per
policy), continue the autonomous loop to the next stage; only halt at a gate whose resolved mode is
`false` or whose safety override triggered."

**B — acceptance:** With the default map, a clean project runs niche→interior→cover→…→listing with
**no human prompts**, halts at **compliance** (human) and **release** (human). Setting a gate to
`"false"` restores the prompt. Legacy string value still works.

---

## WORKSTREAM C — Company-wide legal/rights defaults (push legal to the end)

**Goal:** One editable company-level legal-defaults block, copied into each project at creation, read
by the compliance/release skills so the human only confirms *deltas* just before release.

### C1. Add `legal_defaults` to the company template

File: `.claude/config/company.default.json` — ADD:

```json
"legal_defaults": {
  "ai_disclosure": "This book's puzzles and layout were generated and verified by software; cover and interior art are original works. No AI-generated text is presented as human authorship.",
  "rights_posture": {
    "line_art": "original-only",
    "fonts": "licensed-for-commercial-embedding",
    "puzzle_word_lists": "original-or-public-domain",
    "default_asset_rights_status": "unknown-blocks-release"
  },
  "originality_attestation_template": "Original work created via deterministic code generation and original illustration; no protected reference was traced or closely derived; no living artist imitated by name or style.",
  "release_scope_defaults": {
    "territories": ["US"],
    "channels": ["kdp", "etsy"],
    "permitted_operations": ["prepare-package", "dry-run"],
    "maximum_external_spend": 0.0,
    "currency": "USD"
  },
  "child_safety_policy": {
    "kids-4-8": "friendly/familiar imagery only; no scary/dark/ambiguous-threat; large cells+type; forgiving difficulty",
    "kids-6-10": "positive imagery; modest progression; no violence/sexualisation/disturbing themes",
    "tween-8-12": "no horror/graphic-violence/age-inappropriate social themes; school/family safe"
  }
},
```

> These are DEFAULTS, not clearances. `default_asset_rights_status: "unknown-blocks-release"`
> preserves the rule "never infer clearance from missing evidence" (`rules/12-rights.md`,
> `standards/rights-contract.md`). Edit `company.local.json` to override per company.

### C2. Seed the defaults into each project at creation

File: `.claude/skills/product-new/SKILL.md` (and confirm the underlying
`scripts/publishing_house/` init path — search `grep -rn "legal_defaults\|company" scripts/publishing_house/project.py`).
Add a step: "Read `legal_defaults` from the resolved company config and write it into the new
project's `project.yaml` under `production.legal_defaults` (a copy the owner can edit directly per
project)." If a Python init function assembles `project.yaml`, add the copy there instead of in the
skill, and add a schema-safe optional field. Keep it OPTIONAL in the schema so existing projects
validate.

### C3. Read defaults at compliance + release (confirm deltas, don't re-collect)

- `.claude/skills/product-approve-compliance/SKILL.md` — add: "Load
  `production.legal_defaults` (project) falling back to company `legal_defaults`. Present the
  AI-disclosure text, rights posture, and child-safety policy as the pre-filled decision; the human
  confirms or edits deltas only. Do not re-ask for values that match the defaults."
- `.claude/skills/product-release-authorize/SKILL.md` — add: "Default `channels`, `territories`,
  `permitted_operations`, `maximum_external_spend`, `currency` from
  `legal_defaults.release_scope_defaults`; present them pre-filled and let the human confirm/override
  in one AskUserQuestion. This is the single place legal scope is confirmed before release."
- The `rights-manager` agent (`.claude/agents/rights/rights-manager.md`) — add: "Seed ledger
  rights_status/attestation from `legal_defaults` where applicable; still gate on real evidence,
  never infer clearance from absence."

**C — acceptance:** A new project's `project.yaml` contains `production.legal_defaults`. At
compliance the human sees pre-filled disclosure/rights/safety text and confirms in one step; at
release the scope is pre-filled from defaults. Editing `company.local.json.legal_defaults` changes
the defaults for the next new project.

---

## WORKSTREAM D — Model/effort downgrades + fan-out cuts (raw token cost)

**Goal:** Stop spending Opus/xhigh on mechanical narration of deterministic `ph_cli.py` output, and
stop over-fanning agents. Nothing generative or safety-critical is downgraded.

### D1. Skill frontmatter downgrades

Edit the `model:` / `effort:` frontmatter in these `SKILL.md` files:

| File | From | To |
|---|---|---|
| `.claude/skills/product-approve-niche/SKILL.md` | opus / high | **haiku / medium** |
| `.claude/skills/product-approve-cover/SKILL.md` | opus / high | **haiku / medium** |
| `.claude/skills/product-approve-interior/SKILL.md` | opus / high | **haiku / medium** |
| `.claude/skills/product-approve-listing/SKILL.md` | opus / high | **haiku / medium** |
| `.claude/skills/product-approve-compliance/SKILL.md` | opus / high | **sonnet / medium** (keeps escalation judgment) |
| `.claude/skills/product-release-authorize/SKILL.md` | opus / high | **sonnet / high** (highest stakes; conservative) |
| `.claude/skills/product-run/SKILL.md` | opus / high | **sonnet / high** (orchestrator; delegates real work) |
| `.claude/skills/product-analytics/SKILL.md` | opus / high | **sonnet / high** |
| `.claude/skills/product-final-red-team/SKILL.md` | opus / xhigh | **opus / high** (keep Opus; drop xhigh) |

Rationale: approve skills only read a packet, print a fixed card, prompt once, and call the CLI —
the human (or the deterministic evidence) decides. Keep `research` at opus/high (genuine multi-source
synthesis) — do NOT downgrade.

### D2. Agent frontmatter downgrades

Edit `model:`/`effort:` in these agent files (paths under `.claude/agents/`):

| Agent file | From | To |
|---|---|---|
| `content/content-verifier.md` | sonnet / xhigh | **sonnet / medium** |
| `quality/solvability-checker.md` | sonnet / xhigh | **sonnet / medium** |
| `production/accessibility-auditor.md` | sonnet / xhigh | **sonnet / medium** (keep judgment for alt-text quality) |
| `content/difficulty-curator.md` | sonnet / high | **sonnet / medium** |
| `content/puzzle-generator.md` | sonnet / high | **haiku / medium** |
| `rights/rights-manager.md` | opus / xhigh | **sonnet / high** |
| `compliance/compliance-officer.md` | opus / xhigh | **sonnet / high** |
| `distribution/release-coordinator.md` | opus / xhigh | **sonnet / high** |
| `content/acquisitions-editor.md` | sonnet / high | **sonnet / medium** |
| `commercial/metadata-specialist.md` | sonnet / high | **sonnet / medium** |
| `commercial/keyword-strategist.md` | sonnet / high | **sonnet / medium** |
| `production/layout-engineer.md` | sonnet / high | **sonnet / medium** |
| `production/prepress-specialist.md` | sonnet / high | **sonnet / medium** |

**DO NOT downgrade** (genuine judgment/generation — quality risk > budget):
`executive/publisher-in-chief`, `quality/quality-lead`, `rights/originality-auditor`,
`compliance/child-safety-reviewer`, `discovery/market-scout`, `discovery/competition-analyst`,
`discovery/audience-strategist`, `visual/art-director`, `visual/coloring-line-artist`,
`visual/cover-designer`, `content/journal-prompt-writer`, `content/content-architect`,
`commercial/listing-copywriter`, `commercial/pricing-strategist`.

> Verify current values first: `grep -rn "^model:\|^effort:" .claude/agents/**/*.md`. The exact
> subfolder for each agent may differ — locate by name, don't assume the path.

### D3. Workflow fan-out reductions

Files under `.claude/workflows/*.js` (each starts with `export const meta = {...}`):

1. **`final-red-team.js`** — biggest win. Currently ~7 audit lenses + a **per-audit "Challenge"
   fan-out** (one adversary per audit) + synthesis, all Opus/xhigh (~15 agents).
   - Replace the per-audit challenge fan-out with **ONE batched challenger** agent that reviews all
     audit outputs together.
   - Group the 7 lenses into **4**: (a) solvability+solution-correctness (code re-run),
     (b) originality+rights, (c) accessibility+audience-fit, (d) packaging/hash integrity.
   - Drop lens effort xhigh→high. Keep the independent code re-run (do not reuse cached reports) —
     that's the point of a final red team — but cap any spot-check at a **fixed item count** (e.g.
     min(20, batch_size)) instead of a 10%-of-book percentage that scales with page count.
   - Target: ~5 agents.
2. **`product-multi-review.js`** — 8 one-per-dimension reviewers + integrity(sonnet/xhigh) +
   synthesis(opus/xhigh). Collapse the 8 dimensions into **4 grouped reviewers**:
   (a) solvability+difficulty (already code-backed), (b) audience+child-safety+originality,
   (c) rights+accessibility, (d) structure+layout+answer-key+page-budget. Integrity phase xhigh→high.
   Keep child-safety and originality as their own judgment inside group (b) — the grouped reviewer
   must still emit per-dimension findings.
3. **`accessibility-audit-batch.js`** — 4 lenses all run the SAME `ph_cli.py audit accessibility`
   and read the same policy. Collapse to **1 audit agent** covering all lenses (the code runs once).
   Synthesis phase → high or fold in.
4. **`difficulty-audit.js`** — fully redundant with `content-verification-batch.js` (difficulty match
   is a field in the same `verify.py` result). **Remove this workflow** (and any skill/agent
   reference to it — grep first: `grep -rn "difficulty-audit" .claude`).
5. **`content-verification-batch.js`** / **`content-generation-fanout.js`** — set the per-batch
   verify phase effort xhigh→**medium** (code decides pass/fail; keep 1 verify per batch as the
   independence boundary). Generation already on Haiku — leave.
6. **`marketing-asset-fanout.js`** — per-channel drafting on Opus → **sonnet/high**. Keep 4 channels.
7. **`niche-opportunity-scan.js`** — group 6 lenses → **4** (demand+seasonal, saturation+pricing,
   audience+accessibility, rights+safety).

> When grouping reviewers, the grouped agent's prompt MUST still require it to emit a finding per
> original dimension (severity/location/evidence/recommendation/acceptance-test/status per
> `standards/review-contract.md`) so the quality gate's per-dimension thresholds
> (`config/quality_gates.json`) still evaluate. Grouping changes WHO reviews, not WHAT is scored.

### D4. Strip decorative sub-agent fan-out from deterministic skills

These skills list `Agent` in `allowed-tools` and a "Specialist delegation" block around what is one
`ph_cli.py` call. Remove the sub-agent spawn (keep the direct script call + fixed checklist); reserve
delegation for genuine independent-judgment dimensions only:

- `.claude/skills/product-verify/SKILL.md` — drop the extra `solvability-checker` + `difficulty-curator`
  spawns; `ph_cli.py verify` is authoritative. Only delegate if the script returns `not-run`/ambiguous.
- `.claude/skills/product-gate-packet/SKILL.md` — drop `quality-lead` + `human-collaboration-facilitator`
  spawns; `ph_cli.py approval packet` already emits the structured packet. Format inline.
- `.claude/skills/product-build-interior/SKILL.md` — drop the post-build `coloring-line-artist` +
  `layout-engineer` inspection spawns (inspection belongs in proof/review, not a second pass here).
- Optionally: `product-build-cover`, `product-build-proof`, `product-build-digital`,
  `product-generate`, `product-metadata-build`, `product-rights-check`, `product-accessibility-audit`
  — same treatment where the body is a single deterministic CLI call.

### D5. product-run per-iteration re-validation

File: `.claude/skills/product-run/SKILL.md` steps 4 & 6. Currently runs `project validate` **and**
`project next` (quality gate) after EVERY stage and re-reads full state + all hashes every iteration.
Change to: "Run `project validate` once **after each transition** (not after every intra-stage
action). Do not re-run the full quality gate here if the stage's own skill already ran it — trust the
recorded `reviews/quality-gate-latest.json` decision. Re-read `state.json` after a transition only."
Keep the "never treat not-run as pass" safety rule.

### D6. (Optional, larger effort) Merge overlapping agents

Lower priority; do only if pursuing max savings. Each merge removes a handoff round-trip:
- `content-verifier` + `solvability-checker` → one `content-verifier` (both wrap the same
  `verify.py`). Update all workflow/skill references (`grep -rn "solvability-checker" .claude`).
- `puzzle-designer` + `puzzle-generator` → one (spec + deterministic generate; verification stays
  separate and independent).
- `layout-engineer` + `prepress-specialist` → one `production-engineer` (adjacent Bash build steps).
- `metadata-specialist` + `keyword-strategist` + `listing-copywriter` → one `commercial-writer` for
  the DRAFTING phase (keep `pricing-strategist` separate). Metadata-channel audit stays independent.

> Merging requires updating: the agent files, `CATALOG.md`, `README.md`, every `SKILL.md` /
> `workflows/*.js` that names the merged agents, and the `agent-memory/` folders. Grep for each name
> before deleting. Because it touches many references, treat D6 as its own follow-up PR after D1–D5.

**D — acceptance:** `grep -rn "^effort: xhigh" .claude/skills .claude/agents` returns only the
intended keepers (none, after D1/D2, unless you kept red-team core — but D1 moves it to high). A full
run spawns materially fewer agents (compare `events.ndjson` `CLAUDE_TOOL_USED`/agent counts before vs
after). Quality gate still evaluates all 17 dimensions in `config/quality_gates.json`.

---

## Cross-cutting: verify quality didn't regress (the ≤15% guardrail)

After A–D, run one full product end-to-end on a **scratch** project and compare against the
`clr-2026-large-print-sudoku-for-seniors-easy-puzzles-with` baseline:

1. `reviews/quality-gate-latest.json` — `weighted_overall` must stay ≥ 4.3 (the
   `minimum_weighted_overall` in `config/quality_gates.json`) and all 6 critical dimensions
   (`solvability, solution_correctness, originality, rights, accessibility, audience_fit`) ≥ 4.5.
2. `verification/content-verification-latest.json` — decision PASS (unchanged; code-driven).
3. `accessibility/gate-latest.json` and `rights/gate-latest.json` — PASS/WARNING.
4. `events.ndjson` — **zero** `APPROVALS_INVALIDATED` from late rebuilds; **fewer** total events and
   agent spawns; human prompts only at compliance + release.
5. If any critical dimension drops below its threshold, the last change to that dimension's reviewer
   (a D2/D3 downgrade or grouping) is the suspect — revert that single change and re-run.

## Test & validation commands

```bash
# Python unit tests (locate the test runner/dir first)
grep -rl "unittest" .claude/scripts | head
python3 -m unittest discover -s .claude/scripts -p "test_*.py"   # adjust -s to the real tests dir

# Config/state validation on a scratch project
python3 .claude/scripts/ph_cli.py project validate <scratch-id>
python3 .claude/scripts/ph_cli.py project status <scratch-id>
python3 .claude/scripts/ph_cli.py project plan <scratch-id>

# Framework self-check
python3 .claude/scripts/ph_cli.py  # then the product-doctor skill

# Confirm no stray xhigh remains where not intended
grep -rn "^effort:" .claude/skills .claude/agents .claude/workflows
```

## Suggested commit sequence (one PR per workstream, on a branch — do not push unless asked)

1. `fix: scope gate approvals to source hashes; stop late-rebuild invalidation` (Workstream A + tests)
2. `feat: per-gate auto_approve_gates; auto-approve craft gates, human keeps compliance+release` (B)
3. `feat: company legal_defaults block seeded per project; confirm deltas at compliance/release` (C)
4. `perf: downgrade mechanical skills/agents off opus/xhigh; slim red-team & multi-review fan-out` (D1–D5)
5. `refactor: merge overlapping agents` (D6, optional follow-up)

## What is explicitly NOT changed

- Deterministic generators/verifiers (`verify.py`, `accessibility.py`, `quality.py`, `ctype.*`) —
  the code that actually proves solvability/uniqueness/difficulty/accessibility.
- Independent safety/legal judgment agents (originality, child-safety, quality-lead synthesis).
- Release exact-hash human authorization.
- Schema files' required fields (new fields are optional/additive).
- The network carve-out and Python invariants in `rules/18-python.md`.
