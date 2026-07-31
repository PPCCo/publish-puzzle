# Cover Art Direction Brief — Large Print Sudoku for Seniors: Easy Puzzles with Solutions

## Artifact header

- **Project ID:** clr-2026-large-print-sudoku-for-seniors-easy-puzzles-with
- **Artifact type / intended schema:** cover-art-direction brief (markdown; direction and prototype description only — not a production asset)
- **Creator role:** art-director (AGT-019, Visual)
- **Created:** 2026-07-31
- **Status:** DRAFT — direction only. No cover approval granted or implied; the `cover` human gate is required before bulk cover production.
- **Lifecycle state at authoring:** VISUAL_DEVELOPMENT (per `state.json`)
- **Source artifacts (read-only inputs, cited by hash):**
  - `project.yaml` (project-spec) — `sha256:08f00aca62663310a92681a3bf31c5dde56cf9639207131f236f35651303db25`
  - `notes/intake.md` (intake-note) — `sha256:ddb37f896336cbc0492d0ddc33f4189cd86ec50dc9275a16eedebd8d14f11513`
  - `brief/product-brief.md` (product-brief) — `sha256:ac56faf8eed41711e071c40eb5a5d681f882fd3f9afc67c9a8dbfb82fbe57a25`
  - Interior page count confirmed via interior-pdf v2 — `sha256:b4028dad689372ecb1406295dfafe1922a4c3eeab535b5296e8f919f8dbcc26f` (provenance: 202 pages, paperback)
  - Rules: `.claude/rules/20-design-policy.md`, `.claude/rules/22-colour-policy.md`, `.claude/rules/07-originality-and-line-art.md`
- **This brief does NOT:** produce artwork or image files, mutate `state.json` / `project.yaml` / approvals, assert rights clearance on any font or asset, or infer any human approval.

---

## 1. Design-basis derivation (traceable, not taste-picked)

All decisions below trace to the resolved `production.design` block in `project.yaml` and the `senior-large-print` band profile. Nothing here re-derives or overrides a derived design-policy value.

| Derived design-policy value | Source | Effect on cover direction |
|---|---|---|
| Audience band `senior-large-print` (age 55+) | `project.yaml` `production.design.inputs.audience` | Oversized, dominant title type; maximum contrast; single, calm focal composition; no visual clutter. |
| Tone register `calm-clear` | `field_source.tone_register = audience:senior-large-print` | Restrained, quiet palette; generous white space; no urgency, no busyness. |
| Emotional-intensity ceiling `gentle` | `field_source.emotional_intensity_ceiling = audience:senior-large-print` | Soft, reassuring colour relationships; no harsh or aggressive contrasts beyond legibility needs. |
| Visual density `medium` | `field_source.visual_density = book_type:puzzle-book` | Cover carries one dominant element (title) plus one supporting motif (partial grid). Not sparse, not busy. |
| Trim `8.5x11` paperback | `production.design.trim_size` | Front-cover art area 8.5 x 11 in plus bleed; vertical/portrait composition. |
| `colour_interior = false` (B&W high-contrast interior) | `production.colour_policy` | Interior constraint does NOT bind the cover. Cover MAY be full colour — see §4 and rule 22 ("Covers MAY be full colour"). No design-policy deviation is being taken. |

**No deviation from any derived design-policy value is proposed in this brief.** Cover colour is permitted, not overridden: rule 22-colour-policy states coloring-book covers "MAY be full colour," and the `senior-large-print` greyscale rule governs the *print interior*, not the cover wrap.

---

## 2. Cover style

- **Composition:** Clean, single-focus, portrait layout. **Title dominant** in the upper-to-middle field; a **partial sudoku grid motif** as a background/accent element occupying the lower or corner region as a supporting (not competing) visual. Ample calm negative space between elements.
- **Density:** Low-to-medium. One primary message (the title), one secondary motif (the grid), one clear benefit line ("Easy Puzzles with Solutions"). No third competing focal point.
- **Hierarchy of attention:** (1) main title, (2) "for Seniors" / audience signal, (3) benefit subtitle, (4) grid motif as texture/context, (5) author/imprint line (smallest).
- **Thumbnail-first design:** The cover MUST read at KDP/Etsy thumbnail size. The words "Large Print Sudoku" must be legible and the large-print promise visually self-evident at approximately 160 x 160 px equivalent. Design at full size but validate every decision against the shrunk thumbnail.
- **Calm, uncluttered feel:** consistent with `calm-clear` tone and `gentle` intensity ceiling — reassuring, orderly, easy on the eye. This is a functional requirement for the audience, not a stylistic preference.

## 3. Typography

- **Font class:** Clear, high-legibility **sans-serif** (preferred for maximum thumbnail and low-vision legibility) OR a **clean, sturdy slab/humanist serif**. Large counters, open apertures, generous x-height.
- **Prohibited type:** No cursive, script, handwritten, condensed, thin/hairline, decorative, distressed, or ornamental display faces. Nothing that reduces legibility at small size or for reduced-acuity readers.
- **Title size hierarchy (relative, front cover):**
  1. **"LARGE PRINT SUDOKU"** — largest element; dominant; high weight (bold/semibold); the single most legible phrase at thumbnail size.
  2. **"for Seniors"** — second tier; clearly subordinate to the main title but still large and unambiguous.
  3. **"Easy Puzzles with Solutions"** — benefit subtitle; third tier; readable at thumbnail but visually lighter than the title block.
  4. **Author / imprint line** — smallest; bottom of cover; must not compete with the title.
- **Case & spacing:** Title may be all-caps or title-case; keep tracking open, avoid tight/condensed setting. Left-align or centre — one consistent axis, no mixed alignment.
- **Weight & contrast:** Title weight bold enough to hold up at thumbnail; body/subtitle medium. Avoid ultra-thin weights entirely (fails contrast and thumbnail legibility for this band).

## 4. Colour palette intent

- **Constraint check:** Cover colour is permitted under rule 22-colour-policy (covers MAY be full colour). Interior remains B&W high-contrast per `colour_interior = false`; this brief does not touch interior colour. No `colour_interior` contradiction and no design-policy deviation.
- **Palette rule:** **2–3 colours maximum**, high contrast, calm and reassuring for the senior audience (aligned with `calm-clear` tone and `gentle` intensity).
- **Recommended palette (primary):** **Deep navy + white + warm gold accent.**
  - Deep navy background or title band — calm, trustworthy, high contrast against white.
  - White (or near-white) for the dominant title text — maximum legibility, strong figure/ground separation.
  - Warm gold as a single restrained accent (e.g. a rule line, the grid motif stroke, or a highlighted key word) — adds warmth and a premium, gift-appropriate feel without noise.
- **Alternate palette (equally acceptable):** **Teal + white + soft warm grey** — calm, contemporary, still high-contrast; grey used only for the supporting grid motif so it recedes behind the white title.
- **Contrast requirement:** Title-to-background contrast must be strong (dark-on-light or light-on-dark). Do not set the title in the gold accent over white, or in any low-contrast pairing. The accent colour is for small/secondary elements only.
- **Background-to-foreground relationship:** One dominant field colour, one high-contrast text colour, one accent used sparingly. No gradients that reduce text contrast; if a gradient is used it must not drop title contrast below the high-contrast target.

## 5. Imagery / motif

- **Central/supporting motif:** A **partial sudoku grid** — an original, abstract 9x9 (or a cropped portion of one) rendered as clean geometric line-work. It may sit behind or beside the title as background texture or as a defined accent block. It signals the product category instantly at thumbnail size.
- **Motif treatment:** Bold, clean rule lines consistent with the large-print, high-contrast ethos. A few cells may show large, clear digits (1–9) to reinforce "sudoku" and "large print" at a glance; digits must be in the same legible type family and large enough to read at thumbnail.
- **Strictly prohibited imagery:**
  - No people, faces, hands, or figures (no photos or illustrations of seniors).
  - No clipart, stock-photo elements, or decorative embellishment libraries of unknown provenance.
  - No trademarked, branded, or franchise imagery; no puzzle-brand logos or recognisable proprietary grid styling.
  - No imitation of any living artist's style or any identifiable commercial studio look.
- **Everything on the cover must be original** — either generated/constructed original geometry (the grid, rules, digits) or abstract/geometric shapes composed for this cover. The grid is generic mathematical subject matter (a 9x9 lattice with digits 1–9) and carries no third-party expression.

## 6. Originality statement

- The cover direction imitates **no living artist** by name or recognisable style, and references **no contemporary studio identity or commercial franchise**.
- All specified elements are **original or abstract/geometric**: the sudoku-grid motif is generic mathematical subject matter (a lattice of squares with digits 1–9); the typographic layout, colour system, and composition are original to this product.
- **No protected image is traced, reproduced, or closely adapted.** No public-domain reference image is required for this cover; if the cover builder introduces any reference, it must be recorded in the rights ledger with source and status before the interior/cover gate.
- Per rule 07-originality-and-line-art: any cover art asset produced from this direction MUST carry an **originality attestation** in the rights ledger (creator, creation method, tool/model version, statement that no protected reference was traced or closely derived) before the cover gate.

## 7. Accessibility note

- The cover is **exempt from the interior high-contrast rule** in the sense that it MAY use colour; however, this audience (`senior-large-print`, 55+) makes **legibility a hard functional requirement, not a stylistic option**.
- **Title text must be large, bold, and high-contrast** against its background at full trim and at thumbnail. The large-print promise must be visually credible: the cover itself should look large-print.
- **Thumbnail legibility target:** "Large Print Sudoku" and the "for Seniors" signal must remain readable at approximately 160 x 160 px (KDP/Etsy grid thumbnail). Validate by shrinking the mock to thumbnail and confirming the title still reads.
- **Alt text / decorative designation:** Provide meaningful alt text for the cover (e.g. describing the title treatment and the sudoku-grid motif) or a documented decorative designation, per house rule 9 and rule 07. This is required before the compliance/accessibility gate.
- Avoid low-contrast grey-on-grey, thin rules, and small secondary text — the same acuity constraints that govern the interior inform good cover practice here even though colour is allowed.

## 8. Rights note

- **Fonts:** Any typeface used on the cover MUST be rights-cleared for **commercial use** (including print-on-demand and marketplace distribution) and recorded in the rights ledger before the cover gate. **This brief does NOT assert clearance for any specific font** — font rights must be verified by the cover builder / rights check. The rights ledger for this project is currently empty (`rights/ledger.json` has no records), so **no font, art, or asset clearance exists yet**.
- **No asset with unknown rights** may appear on the cover. Any element whose commercial-use rights are `unknown`, `restricted`, or `expired` blocks the cover/compliance gate.
- **Cover art originality attestation** and **font licence records** must both be present in the rights ledger before the cover human gate can pass.
- No stock imagery, icon set, or ornament with unverified licensing may be introduced.

## 9. Prototype description (concept only — not a production asset)

**Cover concept "Calm Navy Grid" (primary):**
- Portrait 8.5x11 field. Upper ~55%: deep-navy band. "LARGE PRINT SUDOKU" set large, bold, white sans-serif, centred, open tracking. Directly beneath, smaller white "for Seniors."
- Lower ~45%: white/near-white field carrying a partial 9x9 sudoku grid in clean navy rule-lines, a handful of cells filled with large legible digits (1–9), a couple of cells shown in warm gold as the single accent.
- A thin warm-gold rule separates the two fields. Benefit subtitle "Easy Puzzles with Solutions" sits in navy on the white field, clearly subordinate to the title. Author/imprint line smallest, bottom edge.
- Thumbnail check: at 160 px the navy/white split, the bold white title, and the grid motif all remain distinguishable; "Large Print Sudoku" stays legible.

This is a representative concept to validate the design basis; it is not the final cover and produces no image file.

## 10. QA criteria (measurable — the cover builder / cover-designer must demonstrate)

1. **Title thumbnail legibility:** "Large Print Sudoku" is legible when the cover is scaled to ~160 x 160 px. (Acceptance: reviewer can read the phrase from the thumbnail without enlarging.)
2. **Contrast:** Title-to-background pairing is high-contrast (dark-on-light or light-on-dark); accent colour is not used for the main title. (Acceptance: title contrast passes a high-contrast check; accent confined to secondary elements.)
3. **Palette discipline:** No more than 3 colours in the final cover; matches one of the two recommended palettes or a documented equivalent with recorded rationale. (Acceptance: colour count ≤ 3.)
4. **Type class:** No cursive, script, thin/hairline, condensed, or decorative face; title is sans-serif or clean sturdy serif at a dominant size. (Acceptance: type audit confirms class and hierarchy.)
5. **Motif originality & prohibitions:** Grid motif is original abstract geometry; no people, no clipart, no trademarked/franchise imagery, no living-artist-style imitation. (Acceptance: originality attestation recorded; prohibited-element checklist all clear.)
6. **Hierarchy:** Four-tier hierarchy (title > audience signal > benefit subtitle > author/imprint) is visually unambiguous. (Acceptance: reviewer identifies the intended reading order without prompting.)
7. **Trim/bleed readiness:** Front-cover art fills 8.5x11 plus required bleed; no live text inside the safety margin (verified at cover build, not here).
8. **Rights records present:** Font licence(s) cleared for commercial use and cover-art originality attestation both recorded in the rights ledger. (Acceptance: no `unknown`/`restricted`/`expired` asset; ledger entries exist.)
9. **Accessibility:** Alt text or documented decorative designation provided for the cover.

---

## 11. Quality self-assessment (rubric)

- **Design-Policy Alignment — 5/5.** Every decision (dominant type, high contrast, calm palette, low-medium density, portrait 8.5x11) traces to `production.design` values (`calm-clear`, `gentle`, `visual_density medium`, `senior-large-print`, `trim 8.5x11`). Cover colour is permitted by rule 22, not an override; no deviation taken.
- **Audience Fit — 5/5.** Oversized dominant title, maximum figure/ground contrast, reassuring calm palette, thumbnail-legibility requirement, no clutter — all serve the 55+ reduced-acuity band. The cover visibly delivers the "large print" promise.
- **Originality — 5/5.** No living artist, studio, or franchise referenced; all elements original or generic abstract geometry (grid = generic maths). Originality attestation required before gate.
- **Production Feasibility — 5/5.** All elements achievable at 8.5x11 print trim within a 2–3 colour cover; grid motif and type are trivially renderable at 300 DPI; no exotic technique required.
- **Comprehension Support — 5/5.** Explicit hierarchy, high-contrast title, sudoku-grid motif for instant category recognition, thumbnail-first legibility target.
- **Completeness — 4/5.** Cover style, typography, palette, motif, originality, accessibility, rights, prototype, and measurable QA criteria are all specified. Held at 4 because two external dependencies remain open (specific font choice + its clearance; final palette selection between the two offered) — these are correctly deferred to the cover builder + rights check, not decided here.

## 12. Open questions / risks (for the cover gate)

- **Font rights unresolved (blocker for cover gate):** no font is cleared yet; rights ledger is empty. The specific typeface and its commercial-use licence must be selected and recorded before the cover human gate.
- **Palette selection:** two high-contrast calm palettes offered; final pick is a routine cover-builder decision within this direction, to be recorded.
- **AI-assistance disclosure requirement** is `unknown` in `project.yaml`; if the cover art is AI-generated, disclosure language handling must be resolved before the compliance gate (out of scope for this visual brief, flagged for continuity).
- **Etsy fulfilment for a paperback-only product** remains an open channel question from the brief; does not affect cover direction but noted for continuity.
