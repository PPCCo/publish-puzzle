# Cover Art-Direction (Revision 2 — AI-art) — SOURCE Document

- **Project ID:** clr-2026-large-print-sudoku-for-seniors-easy-puzzles-with
- **Working title:** Large Print Sudoku for Seniors: Easy Puzzles with Solutions
- **Product family / audience band:** puzzle-book / `senior-large-print`
- **Format / trim:** paperback, 8.5 × 11 in trim; full wrap **17.7049 × 11.25 in**
  (back | spine | front, all + 0.125 in bleed); spine **0.4549 in** derived from
  202 interior pages on white paper.
- **Creator role:** art-director (with cover-builder realisation)
- **Revision:** 2 (AI-art direction). Supersedes revision 1 "Calm Navy Grid"
  (`concepts/cover-art-direction.md`, `sha256:412608ca1b24d68647cb6eec3a5da3bea53aa3140e37d544b5ecd2805e444f0f`),
  which remains on disk unchanged per new-revision discipline (constitution §5).
- **Status:** proposed — SOURCE artifact for the (re-opened) cover human gate.
  Authorises nothing, approves no gate, transitions no state.
- **Intended schema:** cover-art-direction
- **Describes built asset:** `outputs/cover/cover-wrap-art.pdf`
  (`sha256:3a6f2d7df1624a0bf0c0dab4243bdebe0b4c2d4edd30f6f2e02d7a8c5c55ec98`)
- **Source of truth for what is drawn:** `.claude/scripts/publishing_house/layout.py`
  → `build_cover(style="art")` → `compositor.compose_cover_wrap`.

This document is the SOURCE artifact the cover human gate binds to. It DESCRIBES the
visual language of the built AI-art cover wrap so the two are consistent.

---

## 0. Why a revision (honest change record)

Revision 1 specified a **procedural "Calm Navy Grid"** cover: a flat navy field, a
hand-drawn partial 9×9 sudoku grid motif, cream accent rules, white title. That
direction was realised by the procedural `build_cover` path and produced
`outputs/cover/cover-wrap.pdf` (preserved, untouched).

Revision 2 changes the **visual basis** to an **AI-generated illustrative background**
(soft geometric grid-textured field, calm light) with **real typography composited on
top in rights-cleared embeddable fonts**. This is a material change to the cover's
visual language — it is NOT a re-render of the approved direction. It therefore
requires a fresh human cover-gate decision; it must not ship under the revision-1
approval. The human explicitly elected to adopt this AI-art direction (recorded
in-session, then bound by the cover-gate approval command).

## 1. Visual language (as built)

### 1.1 Background art (AI-generated)
- An original, abstract, calm background evoking quiet puzzle-solving: soft geometric
  grid textures under gentle, even light. No readable numbers or letters in the art
  itself. Full-bleed on the front panel.
- Generated offline via the local ComfyUI bridge. Provenance in the rights ledger and
  `visuals/assets/clr-cover-art-front.provenance.json`:
  - provider `local-sdxl`, model `sdxl-1.0-base`, method `ai-generated`
  - seed `1940807268`
  - licence `CreativeML Open RAIL-M`, `commercial_rights_verified: true`
  - flux-schnell was attempted first and rejected for poor prompt adherence
    (washed-out near-empty field); SDXL honoured the constraints.

### 1.2 Typography (composited by code, not in the art)
- Title + audience signal + benefit line, count callout, spine title, and back-panel
  copy are drawn by `compose_cover_wrap` in **rights-cleared embeddable fonts** — a hard
  gate (`FontNotClearedError`) refuses to fall back to a system face.
  - Display: **Archivo** (Archivo Black) — cleared via `dependency select`.
  - Body: **Atkinson Hyperlegible** — cleared via `dependency select`.
- A deterministic WCAG contrast check adds a semi-opaque scrim panel behind the title
  ONLY when the art beneath it is too low-contrast, so the title always meets AA.
- The cream count callout ("100 Puzzles") is positioned **dynamically below the
  measured title bottom**, so a long multi-line title never collides with it.

### 1.3 Palette
- Cover-only colour (interior stays B&W high-contrast; `colour_interior = false`
  unaffected — rule 22 permits colour covers). The AI field is calm/cool with soft
  light; the composited navy solid (`#1a3a5c`) grounds the back panel and spine; the
  cream callout (`#fdf6e3`) and white ink (`#ffffff`) carry the type.

## 2. Accessibility (senior-large-print — hard requirement)
- Title is large, bold Archivo Black, white ink, with auto-scrim guaranteeing AA
  contrast over the art. "Large Print" is stated in the descriptor line.
- Thumbnail legibility: validated at cover-art review; the title band + cream callout
  read at ~160 px.
- Alt text / decorative designation for the cover art must be recorded in the rights
  ledger before the compliance/accessibility gate (the background art is decorative;
  the informational content is the composited type).

## 3. Originality & rights
- Cover art is **original AI-generated** work: not a trace, copy, or close derivative of
  any existing cover, photograph, artwork, character, or logo; no living-artist-style
  imitation; no trademark, trade dress, or real-person likeness. In-image text is
  prohibited (the brief states this positively because flux negatives are inert).
- Provider `local-sdxl` is `commercial_rights_verified: true`; the rights record for the
  ingested asset is cleared with full provenance (seed, prompt, model, licence).
- Fonts Archivo and Atkinson Hyperlegible are cleared for commercial embedding.
- **AI-assistance disclosure** must be handled at the compliance gate (this cover is
  AI-generated); flagged for continuity, out of scope for this visual brief.

## 4. QA criteria (measurable — cover-art review must demonstrate)
1. Title legible at ~160 px thumbnail; "Large Print" promise visually credible.
2. Title-to-background contrast passes WCAG AA (auto-scrim where needed).
3. No in-image text/lettering/watermark in the AI art.
4. Type set entirely in cleared embeddable fonts (no system fallback).
5. No people, clipart, trademarked/franchise imagery, or living-artist imitation.
6. Front art fills 8.5 × 11 + bleed; live text inside the safety margin only.
7. Rights records present: cover-art originality attestation + font licences.
8. Cover-art alt text / decorative designation recorded.

## 5. Bound hashes (for the cover gate)
- SOURCE (this doc) — registered on write.
- Built cover-pdf — `sha256:3a6f2d7df1624a0bf0c0dab4243bdebe0b4c2d4edd30f6f2e02d7a8c5c55ec98`
- Cover proof (art) — `sha256:a63f92629754d5b23c270813425929962a6556cfc8401b34ba8c6826b66690b8`
- Interior-pdf (unchanged source) — `sha256:b5e76422633756f5505c5186f3a96e257699319ba40160d1314902b77d99b0ae`
