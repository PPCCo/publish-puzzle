# Cover Art-Direction — SOURCE Document

- **Project:** clr-2026-easy-sudoku-for-adults-relaxing-puzzles-with-ful
- **Working title:** Easy Sudoku for Adults: Relaxing Puzzles with Full Solutions
- **Product family / audience band:** puzzle-book / `adult-general` (NOT senior-large-print)
- **Visual density (derived):** medium (`production.design.visual_density`, source `book_type:puzzle-book`)
- **Format / trim:** paperback, 8.5 × 11 in trim; full wrap 18.1553 × 11.25 in (back | spine | front, all + 0.125 in bleed); spine 0.9053 in derived from 402 interior pages on white paper
- **Creator role:** art-director
- **Timestamp:** 2026-08-14
- **Status:** proposed (source artifact for the cover human gate)
- **Intended schema:** cover-art-direction
- **Describes built asset:** `outputs/cover/cover-wrap.pdf`
- **Source of truth for what is drawn:** `.claude/scripts/publishing_house/layout.py` → `build_cover` (approx. lines 258–407)

This document is the SOURCE artifact the cover human gate binds to. It DESCRIBES the
visual language realised by the already-built cover wrap so the two are consistent. It
authorises nothing, approves no gate, and transitions no state.

---

## 1. Visual language

### 1.1 Palette (with hex)

| Role | Colour | Hex | Applied to |
| --- | --- | --- | --- |
| Background field | Navy | `#1a3a5c` | Front panel, back panel, and spine backgrounds (full-bleed rects) |
| Accent / rules / callout fill | Cream | `#fdf6e3` | Decorative horizontal rules, callout box fill, grid-preview lines, format badge text, back-panel divider rule |
| Primary type | White | `#ffffff` | Title, sudoku-preview digits, back-panel body text |

Rationale: a two-tone navy field with a warm cream accent reads as calm and orderly —
consistent with a "relaxing puzzles" positioning — while keeping a small, deliberate
palette. The single warm accent against a deep cool ground provides strong figure/ground
separation for the title and callout without visual noise. This is a cover-only colour
system; it does not affect the black-and-white print interior (see §4).

### 1.2 Line weight / rule treatment

- Header decorative rule below the title band: cream, **2.0 pt** stroke width, full inner-margin span.
- Secondary rule below the title block: cream, **1.0 pt**.
- Back-panel divider rule under "About This Book": cream, **1.0 pt**.
- Sudoku grid-preview (4×4 decorative sample): cream lines alternating **2.5 pt** (outer/every-other line) and **0.8 pt** (inner), giving the sample a subgrid-style rhythm that signals "sudoku" at a glance.

Rules are used sparingly as horizontal separators to establish hierarchy bands; they are
decorative, not content-bearing.

### 1.3 Typography relationship

The cover embeds a single sans-serif family — **Bitstream Vera Sans** (Roman + Bold),
embedded under the internal names PHSans / PHSans-Bold — chosen because its licence
permits commercial embedding and redistribution within a product (see §4). Sizes:

- **Title:** Bold, 28 pt (drops to 22 pt automatically if the wrapped title exceeds two lines), white, left-aligned at the front-panel inner margin, line height 1.3×.
- **Count callout ("200 Puzzles"):** Bold, 32 pt, navy on the cream callout box, centred — the largest and highest-contrast type element after the title.
- **Descriptor line:** Regular, 14 pt, navy on cream, centred, joined with " • " separators.
- **Format badge:** Regular, 12 pt, cream, right-aligned bottom of front panel (trim × binding, derived from project spec).
- **Back panel:** Bold 16 pt heading ("About This Book"); Regular 12 pt body (listing-kit description if present).

One typeface family (Bitstream Vera Sans Roman / Bold) is used throughout; hierarchy is carried
by weight, size, and colour rather than by mixing families. This keeps the cover coherent
and geometric, matching the grid-forward subject.

### 1.4 Composition / hierarchy (front panel)

Top-to-bottom reading order on the navy front field:

1. Title block (top, ~1.1 in from top edge) — white bold.
2. Header decorative rule (2.0 pt cream).
3. Secondary rule below the title (1.0 pt cream).
4. Cream rounded callout box (radius 6 pt, ~1.1 in tall) containing the "200 Puzzles" count and the descriptor line.
5. Decorative 4×4 sudoku grid-preview sample (~1.8 in) below the callout.
6. Format badge (bottom-right).

Inner content margin 0.625 in on front and back panels; all live content sits inside the
margin, clear of trim and the 0.125 in bleed.

### 1.5 Visual density rationale (adult-general, medium)

The derived density is **medium** for an adult-general puzzle-book. The composition
reflects that: it is neither the oversized single-element sparseness required for a
senior-large-print band nor a dense, busy teen/adult layout. It carries a moderate,
ordered element count — title, two rules, one callout, one grid motif, one badge — with
generous negative space on the navy field. This matches an adult reader's expectation of a
composed, uncluttered puzzle-book cover and directly traces to
`production.design.visual_density = medium`. No deviation from the derived density is taken.

---

## 2. Thumbnail legibility

Target: title and "200 Puzzles" callout must remain readable at a ~160 px channel
thumbnail (KDP/Etsy grid).

- **Contrast:** White title on navy `#1a3a5c` and navy "200 Puzzles" on cream `#fdf6e3` are both high-contrast pairings that survive downscaling.
- **Size hierarchy:** The 32 pt navy-on-cream count is the strongest single mark; the cream callout box isolates it as a high-contrast island against the navy field, so "200 Puzzles" stays legible at thumbnail scale. The 28 pt white title is the second-strongest element.
- **Secondary elements** (14 pt descriptor, 12 pt badge, grid-preview digits) are expected to become texture rather than readable text at 160 px — this is acceptable; they are not the thumbnail-critical elements.

Confirmed: the two thumbnail-critical elements (title, count callout) are high-contrast and
legible at the 160 px target.

---

## 3. Originality attestation

This cover is an **original work**. The layout is produced deterministically by project
code (`build_cover`) and the composition (navy field, cream rule system, cream count
callout, decorative 4×4 grid motif, single sans-serif hierarchy) is an original arrangement. No
protected third-party image was traced or closely derived; no living artist is imitated by
name or by recognisable style; no franchise, character, logo, or trademarked design is
reproduced. The 4×4 grid motif is a generic decorative representation of a sudoku subgrid
using arbitrary sample digits and is not derived from any published puzzle or protected
artwork.

Matches `production.legal_defaults.originality_attestation_template`.

---

## 4. Rights posture

- **Fonts:** Bitstream Vera Sans (Roman + Bold) is embedded for all cover type (internal names PHSans / PHSans-Bold). **RESOLVED:** the Bitstream Vera licence expressly permits use, copying, embedding, and redistribution within a larger product for commercial sale (it only bars selling the font by itself), satisfying `fonts: licensed-for-commercial-embedding`. Recorded in the rights ledger as `rgt-font-vera-roman` and `rgt-font-vera-bold`, clearance status **cleared**, commercial-use true, WORLD. The font programme is embedded in the cover PDF (TrueType `FontFile2`), meeting the print-channel requirement that all fonts be embedded. This replaces the earlier proprietary-Helvetica concern.
- **Imagery:** No third-party imagery, stock art, clip elements, or photographs are used. All marks on the cover are code-drawn vector shapes, rules, and type.
- **Interior colour policy consistency:** The interior is black-and-white (`production.colour_interior = false`, per `.claude/rules/22-colour-policy.md`). A full-colour cover is permitted and does NOT constitute a `colour_interior` contradiction or a design-policy deviation — rule 22 scopes the greyscale rule to the print interior only and permits colour covers. No deviation rationale is required.

---

## 5. Alt text / decorative designation (per cover visual element)

| Element | Designation | Alt text / note |
| --- | --- | --- |
| Front title block | Meaningful (text) | "Easy Sudoku for Adults: Relaxing Puzzles with Full Solutions" — rendered as cover title text. |
| Count callout box | Meaningful (text) | "200 Puzzles — Easy • Complete Solutions" — the product's key claims, rendered as text on a cream panel. |
| 4×4 sudoku grid-preview sample | **Decorative** | Decorative sudoku-subgrid motif indicating the puzzle type; carries no information beyond genre signalling. No functional alt text required; documented as decorative. |
| Header / secondary / back divider rules | **Decorative** | Horizontal separator rules; decorative, no alt text required. |
| Format badge | Meaningful (text) | "8.5 × 11 in | Paperback" — format information rendered as text. |
| Navy background field | **Decorative** | Solid colour ground; decorative, no alt text required. |
| Back-panel "About This Book" heading + description | Meaningful (text) | Heading plus description body drawn from the listing kit. |

---

## 6. Accuracy attestation (truthful-claims)

- The front cover callout reads **"200 Puzzles"**, matching `content_plan.target_content_count = 200`. **Confirmed accurate.**
- The descriptor line reads **"Easy • Complete Solutions"** and the cover does **NOT** claim **"Large Print."** The product's audience band is `adult-general`, not `senior-large-print`; in `build_cover`, `is_large_print` is False for this band, so the "Large Print" descriptor token is not emitted. **Confirmed: no unsupported large-print claim is made.**
- "Easy" matches `content_plan.difficulty_progression = flat-single-tier-easy`. "Complete Solutions" matches `content_plan.solutions_placement = back-only` (full solutions present). "8.5 × 11 in | Paperback" matches the derived trim and one declared format.

All cover claims are supported by verified project facts. No claim exceeds the product's
real count, band, difficulty, or format.

---

## 7. QA criteria (measurable, for cover-designer / layout-engineer)

1. Front title and "200 Puzzles" callout legible at 160 px thumbnail (visual check at downscale).
2. All live content inside the 0.625 in inner margin; nothing in the 0.125 in bleed or across trim.
3. Palette matches exactly: navy `#1a3a5c`, cream `#fdf6e3`, white `#ffffff`.
4. Descriptor line is exactly "Easy  •  Complete Solutions" with NO "Large Print" token.
5. Count label reads "200 Puzzles".
6. Fonts embedded (Bitstream Vera Sans) are confirmed licensed for commercial embedding — RESOLVED, cleared in rights ledger (`rgt-font-vera-roman`, `rgt-font-vera-bold`); PDF embeds TrueType `FontFile2`.
7. Spine width matches derived 0.9053 in for 402 pages on white paper; full wrap 18.1553 × 11.25 in.
8. Grid-preview motif documented as decorative; no protected reference used.

---

## 8. Provenance

- **Source artifacts referenced:** `project.yaml`; `.claude/scripts/publishing_house/layout.py` (`build_cover`); `outputs/interior/page-map.json` (page_count = 402); `outputs/cover/cover-wrap.pdf` (built asset described).
- **Derived design policy source:** `production.design` block (engine `publishing_house.design_policy.derive_design`, config `.claude/config/design_policy.json`).
- **Deviations from derived design-policy values:** none. Colour, visual density, and trim as realised match the derived values; the full-colour cover on a greyscale-interior product is explicitly permitted by `.claude/rules/22-colour-policy.md` and is not a deviation.
