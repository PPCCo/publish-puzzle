# Cover Art-Direction (Revision 2 — AI-art) — SOURCE Document

- **Project ID:** clr-2026-easy-sudoku-for-adults-relaxing-puzzles-with-ful
- **Working title:** Easy Sudoku for Adults: Relaxing Puzzles with Full Solutions
- **Product family / audience band:** puzzle-book / `adult-general`
- **Format / trim:** paperback, 8.5 × 11 in trim; full wrap **18.1553 × 11.25 in**
  (back | spine | front, all + 0.125 in bleed); spine **0.9053 in** derived from
  402 interior pages on white paper.
- **Creator role:** art-director (with cover-builder realisation)
- **Revision:** 2 (AI-art direction). Supersedes revision 1 procedural navy cover
  (`concepts/cover-art-direction.md`, `sha256:9d6093a756d3a3b7092f73dd9c6686f5887ef848061d2d4a3fb331ca1cf44461`),
  which remains on disk unchanged per new-revision discipline (constitution §5).
- **Status:** proposed — SOURCE artifact for the (re-opened) cover human gate.
  Authorises nothing, approves no gate, transitions no state.
- **Intended schema:** cover-art-direction
- **Describes built asset:** `outputs/cover/cover-wrap-art.pdf`
  (`sha256:a5fd8ff70c689879a313f047a9152c26c9fb7d4fda952676744e0810022d1317`)
- **Source of truth for what is drawn:** `.claude/scripts/publishing_house/layout.py`
  → `build_cover(style="art")` → `compositor.compose_cover_wrap`.

This document is the SOURCE artifact the cover human gate binds to. It DESCRIBES the
visual language of the built AI-art cover wrap so the two are consistent.

---

## 0. Why a revision (honest change record)

Revision 1 specified a **procedural** navy cover (`#1a3a5c` field, cream accent rules,
hand-drawn grid preview, white title) realised by the procedural `build_cover` path
and preserved as `outputs/cover/cover-wrap.pdf` (untouched).

Revision 2 changes the **visual basis** to an **AI-generated illustrative background**
(tasteful abstract geometric field, restful light) with **real typography composited
on top in rights-cleared embeddable fonts**. This is a material change to the cover's
visual language, not a re-render of the approved direction. Note: the revision-1 cover
approval bound ONLY the art-direction source hash, so the tooling did not auto-invalidate
it when the downstream PDF was replaced (rule 03). Regardless, adopting a new visual
basis is a human cover-gate decision; this cover must not ship under the revision-1
approval. The human explicitly elected to adopt this AI-art direction (recorded
in-session, then bound by the cover-gate approval command).

## 1. Visual language (as built)

### 1.1 Background art (AI-generated)
- An original, abstract, tasteful background evoking quiet puzzle-solving: soft
  geometric grid textures under gentle light; calm, relaxing, premium-bookstore mood.
  No readable numbers or letters in the art. Full-bleed on the front panel.
- Generated offline via the local ComfyUI bridge. Provenance in the rights ledger and
  `visuals/assets/clr-cover-art-front.provenance.json`:
  - provider `local-sdxl`, model `sdxl-1.0-base`, method `ai-generated`
  - seed `842635561`
  - licence `CreativeML Open RAIL-M`, `commercial_rights_verified: true`

### 1.2 Typography (composited by code, not in the art)
- Title, count callout, descriptor, spine title, and back-panel copy are drawn by
  `compose_cover_wrap` in **rights-cleared embeddable fonts** — a hard gate
  (`FontNotClearedError`) refuses any system-font fallback.
  - Display: **Archivo** (Archivo Black). Body: **Atkinson Hyperlegible**.
- The 4-line title "Easy Sudoku for Adults: Relaxing Puzzles with Full Solutions" is
  word-wrapped and point-size-fitted; a deterministic WCAG scrim guarantees AA contrast
  over the art. The cream "200 Puzzles" callout is positioned **dynamically below the
  measured title bottom** (fixes the earlier long-title/callout collision).

### 1.3 Palette
- Cover-only colour (interior stays greyscale; `colour_interior = false` unaffected —
  rule 22 permits colour covers). Composited navy solid `#1a3a5c` grounds the back panel
  and spine; cream `#fdf6e3` callout; white `#ffffff` ink.

## 2. Accessibility
- Title bold Archivo Black, white ink, auto-scrim for AA contrast over the art.
- Thumbnail legibility validated at cover-art review.
- Cover-art alt text / decorative designation recorded before the compliance gate
  (background art decorative; composited type carries the information).

## 3. Originality & rights
- Original AI-generated art: no trace/copy/close derivative; no living-artist imitation;
  no trademark, trade dress, or real-person likeness; in-image text prohibited.
- Provider `local-sdxl` `commercial_rights_verified: true`; ingested-asset rights record
  cleared with full provenance.
- Fonts Archivo and Atkinson Hyperlegible cleared for commercial embedding.
- **AI-assistance disclosure** handled at the compliance gate; flagged for continuity.

## 4. QA criteria (measurable — cover-art review must demonstrate)
1. Title legible at ~160 px thumbnail.
2. Title-to-background contrast passes WCAG AA (auto-scrim where needed).
3. No in-image text/lettering/watermark in the AI art.
4. Type set entirely in cleared embeddable fonts (no system fallback).
5. No people, clipart, trademarked/franchise imagery, or living-artist imitation.
6. Front art fills 8.5 × 11 + bleed; live text inside the safety margin only.
7. Rights records present: cover-art originality attestation + font licences.
8. Cover-art alt text / decorative designation recorded.
9. Long-title/callout non-collision (regression-tested).

## 5. Bound hashes (for the cover gate)
- SOURCE (this doc) — registered on write.
- Built cover-pdf — `sha256:a5fd8ff70c689879a313f047a9152c26c9fb7d4fda952676744e0810022d1317`
- Cover proof (art) — `sha256:26dbfe073b09b692e1e62b415b26d4d9f26f090c4399fd628eb2f0f48854c1ec`
- Interior-pdf (unchanged source) — `sha256:717acc5a7820ed4fdc969e8374bddea1f8e18cb4bc9a306f0273cdc821ee0594`
