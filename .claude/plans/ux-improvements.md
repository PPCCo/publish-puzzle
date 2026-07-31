# Plan: Publishing House UX Improvements

## Context

The user's core feedback: the approval loop is too manual, the gate UX is uninviting,
the project folder is confusing, and there's no publisher-friendly "what's ready and
where do I go next" guide at each gate. Five specific asks:

1. Release gate should require only **1** approver (not 2)
2. **Default approver settings** in config (PPC / publisher / APPROVED / "reviewed and accepted the content")
3. **AUTO_APPROVE_GATES** with 3 values: `false` | `auto` | `silent`
4. **Interactive gate UX** — Claude asks "press ENTER to approve" with options, rather than asking the user to re-type a skill command
5. **Publishing guide** at the bottom of each gate — inline in chat, showing finalized file links, what's ready, KDP/Etsy next steps

---

## What changes and where

### A. Create `.claude/config/company.local.json`

**Template:** `.claude/config/company.default.json` (never edit)  
**New file:** `.claude/config/company.local.json`

Override values + new UX keys:
```json
{
  "publisher_brand": "Clarity Press",
  "human_gates": {
    "release": 1
  },
  "default_approver": {
    "identity": "PPC",
    "role": "publisher",
    "decision": "APPROVED",
    "scope": "reviewed and accepted the content"
  },
  "auto_approve_gates": "false"
}
```

- `human_gates.release: 1` — the existing deep-merge in `util.py:load_company_config` picks this up; `approvals.py:162` reads it. No Python change needed.
- `default_approver` — consumed by approval skills only.
- `auto_approve_gates` — `"false"` | `"auto"` | `"silent"`, consumed by approval skills.

### B. All 6 approval SKILL.md files — interactive UX rewrite

**Files:**
- `.claude/skills/product-approve-niche/SKILL.md`
- `.claude/skills/product-approve-interior/SKILL.md`
- `.claude/skills/product-approve-cover/SKILL.md`
- `.claude/skills/product-approve-compliance/SKILL.md`
- `.claude/skills/product-approve-listing/SKILL.md`
- `.claude/skills/product-release-authorize/SKILL.md`

**Changes applied to each:**

1. **Remove `disable-model-invocation: true`** from frontmatter. This flag is what forces the user to manually type commands; removing it lets Claude run the interactive approval loop.

2. **Replace the "Do not infer or default these values" hard requirement** with a new **Procedure** that:
   - Reads `company.local.json` (via `ph_cli.py` or direct JSON read) to get `default_approver` and `auto_approve_gates`
   - Presents a **compact gate card**: title, gate name, key evidence lines (decisions + artifact hashes), open findings count
   - Shows **file links table**: what was produced at this gate, paths relative to project root
   - Then acts based on `auto_approve_gates`:
     - `"silent"` — record approval with defaults immediately, no prompt; show confirmation
     - `"auto"` — show gate card + "Press ENTER to approve as PPC (publisher) or type REJECT / CUSTOMIZE"; wait for response
     - `"false"` — show gate card + explicitly ask for approver identity/role/scope (current behaviour, friendlier formatting)
   - Falls back gracefully: if `default_approver` is absent, always asks explicitly

3. **Add publishing guide** at the bottom of every gate response (see §C).

### C. `product-run/SKILL.md` — add publishing guide to STOP_AT_GATE output

**File:** `.claude/skills/product-run/SKILL.md`

Extend step 3b (`STOP_AT_GATE`) to also render a **"What's ready — next steps"** section after the gate packet. Format:

```
── WHAT'S READY ────────────────────────────────
[table of finalized artifacts at this gate with paths]

── NEXT STEPS ──────────────────────────────────
For KDP:  [3-4 files + upload-checklist.md path]
For Etsy: [files + etsy listing checklist path]
Open decisions: [pricing / Etsy fulfilment / ISBN]

── ACTION ──────────────────────────────────────
[gate name] approval needed.
Press ENTER to approve, or type REJECT / CUSTOMIZE.
```

At the **RELEASE_AUTHORIZATION** gate specifically, also render a **"Your Book Files"** map:

```
── YOUR BOOK FILES ─────────────────────────────
Interior PDF (KDP upload)   outputs/packages/kdp/print/interior.pdf
Cover PDF (KDP upload)      outputs/packages/kdp/print/cover.pdf
KDP listing metadata        outputs/packages/kdp/listing.json
KDP upload steps            outputs/packages/kdp/upload-checklist.md

Etsy printable PDF          outputs/packages/etsy/files/printable.pdf
Etsy listing data           outputs/packages/etsy/etsy-listing.json
Etsy listing steps          outputs/packages/etsy/listing-checklist.md

Launch guide                marketing/launch-guide.json
```

---

## Implementation order

1. Create `.claude/config/company.local.json`
2. Edit all 6 approval SKILL.md files
3. Edit `product-run/SKILL.md`
4. Immediately run the updated `/product-release-authorize` for the current project

## Files modified

| File | Change |
|---|---|
| `.claude/config/company.local.json` | CREATE |
| `.claude/skills/product-approve-{niche,interior,cover,compliance,listing}/SKILL.md` | Remove disable-model-invocation; add interactive UX + publishing guide |
| `.claude/skills/product-release-authorize/SKILL.md` | Same + 1-approver aware |
| `.claude/skills/product-run/SKILL.md` | Add publishing guide to STOP_AT_GATE step |

## What is NOT changed

- `approvals.py`, `gate_packet.py`, `state.py` — no Python changes needed
- `company.default.json` — never edited (checked-in template)
- Any schema files — new config keys are skill-only, not in validated records

## Verification

1. Check `company.local.json` loaded: `ph_cli.py project status <id>` should reflect Clarity Press brand
2. Invoke `/product-release-authorize` for the current project — should show compact card + ENTER prompt, require only 1 approver
3. After approval: `project status` → `READY_FOR_SUBMISSION`; `release-authorization-*.json` has 1 approver
4. For future projects: all gates should show the interactive prompt + file guide
