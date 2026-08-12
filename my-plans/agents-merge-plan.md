# Plan: Merge overlapping agents (Workstream D6 follow-up)

**Author intent:** This is the deferred **D6** item from `my-plans/token-optim-plan.md` — merging
overlapping agents so the framework carries fewer agent definitions and each product run makes fewer
handoff round-trips (less wall-clock, fewer tokens). D1–D5 already shipped; this plan is a standalone
follow-up that a fresh Claude session can execute end-to-end without prior context.

**Hard constraint (inherited from token-optim-plan.md):** do not sacrifice more than ~10–15% output quality,
and **do not weaken any safety/legal invariant**. In particular, the constitution rule
"a generator never signs off its own verification" (`.claude/CLAUDE.md` §4/§7) MUST hold, and the six
human gates plus content freeze ordering MUST be preserved.

All paths are relative to the repo root `/Users/qaiser.abbas/Dev/my-repos/pub/pub-clr`.
All `python3` invocations MUST be `.venv/bin/python3`. Changes stay **uncommitted on `main`** unless the
owner asks otherwise (matches the working style used for A–D). No `shell=True`; use subprocess arg
arrays. Do not touch deterministic invariants (seed determinism, SHA-256, jsonschema 2020-12,
network-free core).

---

## Decision: which of the four candidate groups to actually merge

Verified against the real agent files this was scoped from. Only **two** of the four D6 candidate
groups are safe to merge; the other two are **intentionally kept separate** and this plan does NOT
merge them (merging them would collapse a deliberate firewall or straddle a human gate).

| Group | Members | Decision | Reason |
|---|---|---|---|
| **1** | `content-verifier` + `solvability-checker` | **MERGE** → `content-verifier` | Frontmatter-twins (both sonnet/medium, identical tools/skills). Both are pure code verifiers; §4 forbids only a *generator* self-verifying — it does not forbid one verifier agent. |
| **4** | `metadata-specialist` + `keyword-strategist` + `listing-copywriter` | **MERGE** → `commercial-writer` (DRAFTING only) | No constitutional independence rule applies; all three are human-reviewed drafting roles feeding the listing gate. Needs model/effort/tool leveling (see G4). |
| **2** | `puzzle-designer` + `puzzle-generator` | **DO NOT MERGE** | Deliberate firewall: designer is prohibited from running the generator; generator is prohibited from asserting solvability. Also opus/high (reasoning) vs haiku/medium (deterministic shell-out) — merging forces one model to do both. |
| **3** | `layout-engineer` + `prepress-specialist` | **DO NOT MERGE** | Two human gates (interior + cover) and the interior content freeze sit *between* these two agents in the lifecycle. A merged agent would straddle both gates. |

> If the owner later wants max consolidation, Group 3 is the only *technically* feasible extra merge
> (same model/effort/tools) — but it is out of scope here because of the gate-straddle risk. Group 2
> should stay split regardless.

**Net effect of this plan:** 34 agents → **31** (remove `solvability-checker`; remove
`keyword-strategist` and `listing-copywriter`; `metadata-specialist` becomes `commercial-writer`).

---

## Registry & reference map (verified — update ALL of these)

Two registry/index files and the config routing table drive everything; miss one and a run will name a
dead agent.

- **`.claude/agents/CATALOG.md`** — the authoritative table keyed by `AGT-###` + kebab name. Rows to
  touch: AGT-014 (content-verifier), AGT-015 (solvability-checker), AGT-027 (metadata-specialist),
  AGT-028 (keyword-strategist), AGT-030 (listing-copywriter).
- **`.claude/agents/README.md`** — prose only; hardcodes the agent count **"34"** → update to **31**.
  Does NOT use kebab names, so no per-name edits there beyond the count.
- **`.claude/config/state_playbook.json`** — `recommended_agents` arrays. Lines with target names:
  57 (`content-verifier`,`solvability-checker`,`quality-lead`), 130
  (`metadata-specialist`,`pricing-strategist`,`listing-copywriter`), 23
  (`market-scout`,`competition-analyst`,`keyword-strategist`). (`config/quality_gates.json` has NO
  dimension-owner references to these names — nothing to change there.)
- **`.claude/agent-memory/`** — per-agent memory folders. Only `content-verifier/` and
  `keyword-strategist/` exist (both empty). Keep `content-verifier/`; remove the empty
  `keyword-strategist/` (its role folds into `commercial-writer/` — create that folder if any memory is
  later written; do not pre-create empty).
- **`.claude/logs/hooks.ndjson`** — append-only history mentioning old names (SUBAGENT_START/STOP,
  changed-file lists). **Leave as-is** (immutable audit history).

---

## GROUP 1 — merge `solvability-checker` INTO `content-verifier`

The merged `content-verifier` (keep this name, `.claude/agents/content/content-verifier.md`, stays
sonnet/medium) must cover the union of both agents' checks and keep the independence firewall.

### G1.0 — Ground truth about the verification interface (read before editing)
Both current agent files reference verification interfaces that **do not exist in the code** — do not
copy them into the merged agent verbatim. Verified against `.claude/scripts/`:
- There is **no** `.claude/scripts/verify/verify_sudoku.py` (etc.) directory — `solvability-checker`'s
  per-type solver paths are aspirational.
- There is **no** `ph_cli.py verify solvability|uniqueness|answer-key` sub-verb — `content-verifier`'s
  sub-verb commands are aspirational.
- **The real interface is a single verb:** `.venv/bin/python3 .claude/scripts/ph_cli.py verify
  <project-id> [--type <content-type>]`. `publishing_house/verify.py:75 verify_content()` iterates
  registered batches and delegates per-item checks to the **content-type registry**
  (`registry.get(content_type).validate(item)`), returning a batch report with `decision` (PASS/FAIL),
  a `verifiable` flag per type, `item_count`, and `failed_items[].errors`; it stamps each batch's
  `validation_status` in the artifact manifest and appends a `CONTENT_VERIFIED` event with actor
  `"content-verifier"` (verify.py:123).

**Consequence for the merge:** the merged agent keeps ALL the conceptual checks below as its
responsibilities, but describes them as evaluated through `ph_cli.py verify` + the per-type
`validate()` in the content-type registry — NOT through fictional per-type solver scripts. Where a
puzzle type's `validate()` does not (yet) prove a given property, the agent MUST record it as a
coverage-gap / `UNVERIFIED` finding (never a silent PASS). If the owner later wants deeper per-type
solvers, that is a separate code task in `publishing_house/ctype*` — out of scope here.

### G1.1 — Fold solvability-checker's content into content-verifier.md

Read both files first. The merged `content-verifier.md` MUST preserve **every** activity from both
source agents. Coverage matrix — do not drop a row:

| Capability | content-verifier | solvability-checker | Must survive in merged agent |
|---|---|---|---|
| Solvability of every item | ✅ | ✅ | ✅ via `ph_cli.py verify`; script output is authoritative, never inspection |
| Uniqueness where the type requires it (sudoku/crossword/logic-grid/nonogram) | ✅ | ✅ | ✅ record exact solution count; any count ≠ 1 → NON-UNIQUE |
| Answer-key correctness per item | ✅ | ✅ | ✅ diff each key entry vs verified solution; mismatch = KEY-MISMATCH (major/blocker) |
| **Answer-key diff artifact** (separate output listing every divergent entry: id/expected/found) | — | ✅ | ✅ **ADD** — keep as a distinct output |
| **Difficulty-label accuracy** vs measured metric + `age_bands.json` thresholds | ✅ | — | ✅ keep |
| **Hash-integrity vs generation manifest** (SHA-256 recompute; integrity-fail = do not verify content) | ✅ | — | ✅ keep |
| **Enumeration count-mismatch vs project spec, checked BEFORE verifying** | — | ✅ | ✅ **ADD** — fail immediately if count ≠ spec |
| **Frozen/superseded guard** (do not verify a frozen/superseded or non-approved-spec artifact) | partial | ✅ | ✅ **ADD** the frozen/superseded check from solvability-checker step 1 |
| **Coverage-gap / UNVERIFIED finding** for any type with no automated check (no silent skip) | — | ✅ | ✅ **ADD** — critical given the real registry may not cover every type |
| **Solver method + elapsed-time** recorded per item | — | ✅ | ✅ **ADD** to the report row where available |
| **False-pass resistance**: script error / non-zero exit / timeout / empty output → FAIL or ERROR, never PASS | ✅ (errors) | ✅ (timeout/empty) | ✅ keep the UNION (both error AND timeout/empty rules) |
| Aggregate verdict + per-dimension PASS/FAIL/ERROR counts | ✅ | ✅ | ✅ keep |
| Structured findings (severity/id/location/evidence/recommendation/acceptance-test) | partial | ✅ | ✅ keep solvability-checker's fuller finding shape |
| Prohibition: never edit/repair/regenerate any artifact | ✅ | ✅ | ✅ keep |
| Prohibition: **never approve a gate or recommend release** | implicit | ✅ explicit | ✅ keep the explicit wording |
| Prohibition: never run generation / touch the seed namespace | ✅ | ✅ (deterministic-only) | ✅ keep |
| Independence firewall: verifier is separate from `puzzle-generator`; never trust the generator summary | ✅ | ✅ | ✅ keep — this is the §4/§7 invariant |

Merge mechanics: keep `content-verifier`'s name, department (Content), frontmatter (sonnet/medium,
tools `Read, Grep, Glob, Bash, Write, Skill`, skills `product-verify, product-quality-gate`) — they are
identical in both files, so no frontmatter change. Merge the **quality rubric** as the union of both
(add solvability-checker's *Solver Coverage*, *Uniqueness Rigour*, *Enumeration Completeness*). Merge
the **Escalate/stop** and **Prohibited** lists as the union. Update the merged `Invoke this agent when`
to include solvability-checker's triggers (post-repair re-verification; quality-lead re-verification
request; open solvability finding).

> The `quality/` → `content/` department move is fine (solvability-checker was Quality; its verifier
> role lives naturally in Content). The `quality-lead` remains the independent judgment agent that
> *consumes* this verifier's report — do not fold the verifier into quality-lead.

### G1.2 — Delete `.claude/agents/quality/solvability-checker.md`.

### G1.3 — Update references to `solvability-checker`
- `CATALOG.md` — delete row AGT-015; leave AGT-014 (content-verifier). Optionally note in AGT-014's
  description that it subsumes solvability/uniqueness/answer-key proof.
- `config/state_playbook.json:57` — change `["content-verifier","solvability-checker","quality-lead"]`
  → `["content-verifier","quality-lead"]`.
- `.claude/agents/quality/quality-lead.md:69-70` — the two lines that say
  "requires solvability-checker PASS ..." → "requires **content-verifier** PASS with zero
  UNSOLVABLE/NON-UNIQUE items" and "... zero KEY-MISMATCH items". (Quality-lead stays opus/xhigh,
  untouched otherwise — it is an independent judgment agent, do not downgrade.)
- `.claude/workflows/content-verification-batch.js:28` — the agent prompt string
  "Act as the independent content-verifier and solvability-checker for the ... batch" → drop
  "and solvability-checker" (now redundant). Leave the workflow structure otherwise unchanged.
- No code change needed: `scripts/publishing_house/verify.py:121,123` already uses the string
  `"content-verifier"` — that name survives, so the event actor/`updated_by` stays valid.

---

## GROUP 4 — merge `metadata-specialist` + `keyword-strategist` + `listing-copywriter` INTO `commercial-writer`

Create one Commercial DRAFTING agent. **`pricing-strategist` stays separate** (it is opus/high with
web tools and a distinct commercial-judgment role — do not fold it in). Metadata-channel audit stays
independent (it is a workflow, not one of these agents).

### G4.1 — Create `.claude/agents/commercial/commercial-writer.md`
Rename/replace `metadata-specialist.md` as the base and expand it, OR create fresh and delete the three
originals. Frontmatter (level UP so nothing is lost — the copywriting role is the most demanding):
- `name: commercial-writer`
- `model: '@bedrock-eus1/us.anthropic.claude-sonnet-5'` — **recommended**: keep sonnet/high. Rationale:
  D1/D2 already moved most drafting to sonnet; listing copy is honest-claims drafting, not open-ended
  creative writing. If the owner wants to preserve the old listing-copywriter quality exactly, use
  `@bedrock-eus2/us.anthropic.claude-opus-4-8` instead — call this out and let the owner pick (see
  "Open decision" below).
- `effort: high` (was the max of the three; keeps copy quality).
- tools: `Read, Write, WebSearch, WebFetch, Skill` — the UNION (web tools come from keyword-strategist;
  needed for keyword/tag relevance and rights screening).
- skills: `product-metadata-build, product-listing-kit` (union).
- department: Commercial; color yellow; maxTurns 45 (all three already agree on these).

Body must cover the union of all three roles. These are DRAFTING/generation activities (not code
verification), but the same "nothing dropped" rule applies. Coverage matrix — every output and every
guardrail below must survive in `commercial-writer`:

| Activity / output | metadata-specialist | keyword-strategist | listing-copywriter | Must survive |
|---|---|---|---|---|
| Canonical metadata JSON (title, subtitle, long+short description, categories 1°/2°, audience band + reading level, page/puzzle/difficulty fields, trim, interior-color, formats, territories, contributor-roles, isbn-placeholder, language) | ✅ | — | — | ✅ full canonical field set |
| Per-channel metadata variants (kdp-paperback, kdp-hardcover, etsy-digital, gumroad-digital, generic) with channel field-name mapping + length limits | ✅ | — | — | ✅ |
| **AI-disclosure embedded in EVERY variant** | ✅ | — | ✅ (present in copy) | ✅ mandatory in all metadata + copy |
| Use ONLY verified artifact counts (never spec targets when a verification report exists) | ✅ | ✅ | ✅ | ✅ |
| Keyword strategy doc: search-intent analysis + per-term rationale | — | ✅ | — | ✅ |
| KDP 7 keyword fields (≤50 chars each, no title-word repeats, no punctuation separators) | — | ✅ | — | ✅ hard limit |
| Etsy ≤13 tags (multi-word, no sentences) | — | ✅ | — | ✅ hard limit |
| Gumroad ≤10 tags | — | ✅ | — | ✅ hard limit |
| Generic ranked flat keyword list | — | ✅ | — | ✅ |
| **Rights-risk screening of every term** against the rights-gate report (discard protected brand / licensed character / living artist / trademarked series / uncleared IP) | — | ✅ | — | ✅ keep — this is a rights guardrail |
| Channel-policy screening (medical claims, misleading difficulty, category-bait) | — | ✅ | — | ✅ |
| Long-form listing description per channel (KDP HTML-subset / Etsy plain / Gumroad markdown) | partial | — | ✅ | ✅ keep copywriter's per-channel formatting |
| Bullet-feature list (5–7), each traceable to a verified attribute; no vague superlatives | — | — | ✅ | ✅ |
| Gallery image captions (add info not visible in image; don't describe absent elements) | — | — | ✅ | ✅ |
| KDP A+ content text blocks (module structure, each independently accurate) | — | — | ✅ | ✅ |
| **Digital-download material terms** (digital file, page size US Letter/A4, DPI, no physical item, personal-use license) prominently stated | — | — | ✅ | ✅ keep — legal/consumer-honesty guardrail |
| Accuracy/traceability checklist mapping each factual claim → artifact hash + evidence source | ✅ | — | ✅ | ✅ merge into one checklist |
| Rejected-values / rejected-terms / rejected-copy log with reason codes | ✅ | ✅ | ✅ | ✅ merge into one rejected log |
| Marked as DRAFT requiring human review before any live listing | — | — | ✅ | ✅ keep |
| Prohibition: no keyword stuffing | ✅ | ✅ | — | ✅ |
| Prohibition: no false scarcity / awards / bestseller / endorsement not on record | partial | — | ✅ | ✅ |
| Prohibition: no unverifiable health/cognitive/therapeutic benefit claims | — | — | ✅ | ✅ |
| Prohibition: never write to a live channel, publish, spend, buy identifiers, or accept channel terms | ✅ | ✅ | ✅ | ✅ union |
| Escalate: verified counts conflict with spec; channel limit can't be met without dropping disclosure; product type has no clear category; AI-disclosure/territory law undeterminable; child-targeted copy needs age review; rights-gate unavailable/hash-mismatched | ✅ | ✅ | ✅ | ✅ union of all three escalation lists |

Merge the three **quality rubrics** as a deduplicated union (Factual Accuracy, AI-Disclosure,
Channel Compliance, Audience Fit, Field Completeness, Traceability, Relevance/Search-Intent, Rights
Safety, Limit Adherence, Benefit Clarity, Digital-Download Terms). Preserve the explicit input
dependencies (verification report, rights-gate report, cover brief, channel profiles, AI-disclosure
record) — they were shared across all three.

> Note the internal `metadata → keywords/copy` handoff seam collapses into ordered steps inside one
> agent (build canonical metadata first, then derive keywords and copy from it). Keep that ordering in
> the procedure so copy/keywords still anchor to the finalized canonical metadata, not to raw spec.

### G4.2 — Delete `keyword-strategist.md` and `listing-copywriter.md`; remove the old
`metadata-specialist.md` if you created `commercial-writer.md` fresh (otherwise rename it).
Remove the empty `.claude/agent-memory/keyword-strategist/` folder.

### G4.3 — Update references (all three old names → `commercial-writer`)
- **CATALOG.md** — collapse rows AGT-027/028/030 into a single `commercial-writer` row (keep one
  AGT-### id; note it subsumes metadata + keywords + listing copy). Renumbering other IDs is NOT
  required — leave gaps or keep AGT-027 as the surviving id.
- **`config/state_playbook.json`**:
  - line 130 `["metadata-specialist","pricing-strategist","listing-copywriter"]` →
    `["commercial-writer","pricing-strategist"]`.
  - line 23 `["market-scout","competition-analyst","keyword-strategist"]` →
    `["market-scout","competition-analyst","commercial-writer"]`.
- **Skills — "Specialist delegation" blocks + delegate steps** (replace each old name; if a block now
  lists `commercial-writer` twice, dedupe to one):
  - `skills/product-metadata-build/SKILL.md:38-39,48` (metadata-specialist + keyword-strategist).
  - `skills/product-listing-kit/SKILL.md:38-39,46-47` (listing-copywriter + keyword-strategist).
  - `skills/product-marketing-guide/SKILL.md:40,51` (metadata-specialist).
  - **Variant** `skills/product-run/SKILL.md:44` — text `product-metadata-specialist` → reconcile to
    `commercial-writer` (verify it is meant as the agent name, not a skill slug, when you get there).
- **Workflows — `agent()` prompt strings** (these say "Act as the X and Y ..."; collapse to
  `commercial-writer`):
  - `workflows/marketing-asset-fanout.js:23` ("listing-copywriter and keyword-strategist") and `:47`
    ("metadata-specialist and listing-copywriter lead") → "Act as the commercial-writer ...".
  - `workflows/metadata-channel-audit.js:16` ("packaging-engineer and metadata-specialist") and `:36`
    ("metadata-specialist and keyword-strategist") → replace the metadata/keyword names with
    `commercial-writer`; keep `packaging-engineer` at :16. **Keep this audit workflow's independence
    intent** — the audit still cross-checks the drafts; it just names one drafter now.
- **Agent cross-references** (prose inside other agent files):
  - `agents/commercial/metadata-specialist.md:48` "placeholder for keyword-strategist" — disappears when
    the file is merged; ensure the merged body no longer references a separate keyword agent.
  - `agents/commercial/pricing-strategist.md` — no name match found; leave unless it gains a stale
    reference during editing.

---

## What is explicitly NOT changed by this plan

- **`puzzle-designer` and `puzzle-generator` stay separate** (Group 2) — the spec/never-run and
  generate/never-assert-solvability firewalls and the opus↔haiku split are intentional.
- **`layout-engineer` and `prepress-specialist` stay separate** (Group 3) — two human gates and the
  interior content freeze sit between them. The variant string
  `rules/22-colour-policy.md:33` (`product-designer-layout-engineer`) is a colour-policy responsibility
  label, not an agent-merge target — leave it.
- `difficulty-curator` stays a separate agent (it was only referenced in passing; not a merge target).
  Its `content-verification-batch.js` / `content-generation-fanout.js` synthesis prompts ("Act as the
  difficulty-curator and quality-lead") are unaffected by Groups 1 and 4 — leave them.
- Independent safety/legal judgment agents (`originality-auditor`, `child-safety-reviewer`,
  `quality-lead`, `accessibility-auditor`), the code verifiers' independence, release exact-hash
  authorization, and human-decided compliance/release — all untouched.
- Deterministic generators/verifiers and the Python invariants in `rules/18-python.md`.

## Open decision for the owner (resolve before/at execution)
- **`commercial-writer` model**: sonnet/high (recommended — consistent with the D1/D2 downgrades, lower
  cost) vs opus/high (preserves the exact prior `listing-copywriter` copy quality). Default to
  **sonnet/high** unless the owner prefers opus for listing copy.

## Verification

```bash
cd /Users/qaiser.abbas/Dev/my-repos/pub/pub-clr

# The merged-away names must have ZERO live references outside append-only logs.
for n in solvability-checker keyword-strategist listing-copywriter metadata-specialist; do
  echo "== $n =="
  grep -rn "$n" .claude/agents .claude/skills .claude/workflows .claude/config \
    .claude/CLAUDE.md .claude/rules .claude/standards 2>/dev/null
done
# Expect: no matches for solvability-checker / keyword-strategist / listing-copywriter.
# metadata-specialist: no matches (folded into commercial-writer). Logs under .claude/logs/ are OK.

# New/kept agent files exist and old ones are gone.
ls .claude/agents/content/content-verifier.md              # exists (merged verifier)
ls .claude/agents/quality/solvability-checker.md 2>&1       # No such file
ls .claude/agents/commercial/commercial-writer.md           # exists
ls .claude/agents/commercial/keyword-strategist.md 2>&1     # No such file
ls .claude/agents/commercial/listing-copywriter.md 2>&1     # No such file

# CATALOG count / README count consistent with the surviving set (31 agents).
grep -c "AGT-" .claude/agents/CATALOG.md
grep -n "34\|31" .claude/agents/README.md

# state_playbook.json still parses and names only live agents.
.venv/bin/python3 -c "import json;json.load(open('.claude/config/state_playbook.json'));print('playbook OK')"

# Regression: the A-workstream tests still pass (no code path renamed).
.venv/bin/python3 -m unittest discover -s .claude/scripts/tests -p "test_*.py"

# verify.py actor string still valid (content-verifier kept).
grep -n "content-verifier" .claude/scripts/publishing_house/verify.py

# Scratch project still validates/plans end-to-end with the new routing.
.venv/bin/python3 .claude/scripts/ph_cli.py project validate <scratch-id>
.venv/bin/python3 .claude/scripts/ph_cli.py project plan <scratch-id>
```

### Capability-coverage check (the point of this revision — do this by reading, not grep)

Before deleting any source file, and again after writing the merged file, walk the two coverage
matrices above (G1.1 and G4.1) row by row against the final merged agent body and confirm **every
row's "Must survive" capability, output, prohibition, and escalation trigger is present**. A merge is
NOT done until:

- **Merged `content-verifier`** covers all 17 G1.1 rows — in particular the four that were
  solvability-checker-only and easy to lose: (1) enumeration count-mismatch check *before* verifying,
  (2) frozen/superseded guard, (3) explicit UNVERIFIED / coverage-gap finding for any type the registry
  does not check (never a silent PASS), (4) the separate answer-key diff output — plus the explicit
  "never approve a gate or recommend release" prohibition and the generator-independence firewall.
- **Merged `commercial-writer`** covers all G4.1 rows — in particular the ones unique to a single source
  agent: keyword rights-risk screening against the rights-gate report, the three hard tag/keyword limits
  (KDP 7×50, Etsy 13, Gumroad 10), digital-download material terms, KDP A+ content blocks, and
  AI-disclosure in *every* metadata variant and copy block.
- The merged bodies point ONLY at the real interface — `ph_cli.py verify <id> [--type ...]` and the
  content-type registry `validate()` — and do NOT reintroduce the fictional `.claude/scripts/verify/`
  solver paths or `verify solvability|uniqueness|answer-key` sub-verbs (see G1.0). Any check the current
  registry cannot perform is written as a coverage-gap finding, not asserted as passing.

If any row cannot be honored through the real interface, record it in the plan's completion notes as a
known coverage gap and (if it matters to the owner) file it as a follow-up code task under
`publishing_house/ctype*` — do not silently drop the capability or fake a passing result.

**Acceptance:** agent count drops 34 → 31; the three merged-away names have zero live references
(logs excepted); `content-verifier` covers solvability/uniqueness/answer-key/difficulty/enumeration and
still cannot self-verify generator output; `commercial-writer` covers metadata + keywords + listing copy
with all prior guardrails; `state_playbook.json` parses and routes to live agents only; the A test suite
still passes; a scratch project validates and plans. Groups 2 and 3 remain split. Changes uncommitted on
`main` for review.
