# Plan: ComfyUI image generation for commercial-grade covers & coloring-book art

**Status:** Not started
**Owner branch:** create a feature branch off `main` (e.g. `comfyui-image-gen`)
**Model pin (constitution):** `@bedrock-eus2/us.anthropic.claude-opus-4-8`
**Author date:** 2026-08-16

---

## 0. Problem & findings (read this first in a fresh session)

The framework-generated cover is not commercial-grade. Example:
`projects/clr-2026-large-print-sudoku-for-seniors-easy-puzzles-with/outputs/cover/cover-wrap.pdf`.

**Root cause (verified by reading the code):** the cover is 100% procedural
reportlab drawing in `.claude/scripts/publishing_house/layout.py::build_cover`
(lines ~313-512): a flat navy rectangle, wrapped title text, a cream callout box,
a *hand-drawn fake 4×4 sudoku grid*, and a spine. There is **no art, no image,
no illustration** anywhere in the pipeline. It cannot look like a retail book
because nothing generates a visual.

**Current state of image capability in pub-clr (all verified absent):**
- No `image_generation` block in any config; no `tools.default.json` / `tools.local.json`.
- No `image-gen` subcommand in `ph_cli.py` / `cli.py`.
- No MCP bridge; `.mcp.json` has only `publishing-house` (no `comfyui-mcp`).
- `generators/coloring.py` emits a **line-art *brief*** (text spec + originality
  attestation) only — it explicitly notes "Code cannot draw publishable art."
  So coloring books today have briefs but no rendered pages.
- Agents `visual/cover-designer.md`, `visual/coloring-line-artist.md`,
  `visual/art-director.md` exist but delegate to procedural/manual steps only.

**Reference implementation to port from — `../publish-bk`:**
- `.claude/scripts/publishing_house/image_gen.py` — offline core: provider
  registry (merges `tools.default.json` + `tools.local.json`), `image_gen_status`,
  `build_guide` (manual guide from briefs), `ingest` (hash + register artifact +
  write rights record driven by provider `commercial_rights_verified`),
  `ai_content_disclosure`. **Network-free** — generation egress is out-of-core.
- `.claude/config/tools.default.json` — `image_generation.providers` list
  (`local-sdxl`, `local-flux-schnell` both `commercial_rights_verified: true`;
  hosted/`-dev` ones `false`), `mode: manual-only`, `default_provider`.
- `.claude/skills/book-generate-images/SKILL.md` — the human-elicited (auto vs
  manual), provider-selecting, per-brief generate→ingest→queue-review skill.
- `.claude/mcp/connectors/comfyui_mcp_bridge.py` — the ~180-line stdio MCP bridge
  (`health_check`, `generate_image(provider=...)`), `IMAGE_GEN_LIVE_ENABLED` gate.
- **Font-clearance subsystem (newly discovered — directly enables the cover
  approach in Decision #2):**
  - `.claude/config/dependencies.default.json` — offline registry of 8+
    license-checked font families, each with `license_reference`,
    `embedding_allowed`, `commercial_use_verified`, and a bundled
    `font_file_path`. A font is `cleared` only when embedding + commercial are
    both true — mirrors the image-provider pattern. Font family names referenced
    by `design_policy.json` must exist here (analog of trim keys in `TRIM_SIZES`).
  - `.claude/config/fonts/` (~50 MB) — the actual `.ttf` files: Atkinson
    Hyperlegible (low-vision), Andika (early-reader), Charis/Gentium/Literata
    (serif reading), Lexend, Baloo2, Archivo — all OFL-1.1, commercial-clear.
  - `.claude/config/licenses/` — `OFL-1.1.md`, `Apache-2.0.md` license texts.
  - `.claude/scripts/publishing_house/dependencies.py` — `font_registry`,
    `select_font` (writes a rights record; `cleared` iff both flags true), and a
    `dependency select` CLI verb: shift-left font clearance at design time.
  - `.claude/scripts/publishing_house/compositor.py` — **deterministic Pillow
    compositor** that draws REAL caption text in a cleared, embeddable repo font
    onto generated art, refusing to fall back to a system font (which would
    re-open the license hole). This is exactly the "art + code typography"
    machinery the cover needs; the font gate is a hard dependency.
- `docs/comfyui-image-generation-guide.md` — the operator guide (ground truth,
  weights, Apple-silicon fp16 lesson, safety gates, troubleshooting).

**Shared infra & the neutral home (DECISION #1 = neutral `image-tools/` home):**
BOTH repos currently point their `comfyui-mcp` at the SAME installed bridge copy
`~/Dev/my-repos/pub/image-tools/ComfyUI/comfyui_mcp_bridge.py` and the SAME ComfyUI
at `127.0.0.1:8188`. The bridge is generic (prompt in, PNG out) with no book-repo
dependency. **Plan: promote the bridge to a neutral home under `image-tools/`
(e.g. `image-tools/mcp/comfyui_mcp_bridge.py`) as the single reviewed source of
truth**, install/copy it next to ComfyUI, and have BOTH repos register that same
neutral source. pub-clr keeps only a thin pointer/README, not a divergent copy. A
sha256 drift check in `product-doctor` guards the neutral source vs the installed
copy. (Coordinate the move for publish-bk too, or leave its copy and just repoint
its `.mcp.json` at the neutral home; record which was done.)

**`inspiration/` is genuinely new** — grep shows publish-bk has no such concept.
Net-new design (Phase 3), built to *derive style descriptors, never copy* —
consistent with rules 07 (originality) and 12 (rights). Folder convention:
`projects/<id>/visuals/inspirations/` (DECISION #3), plus a `--inspiration-dir`
arg for the standalone skill (DECISION #4).

---

## 1. Design decisions (LOCKED by user 2026-08-16)

1. **Bridge sharing model — DECIDED: neutral `image-tools/` home.** The single
   reviewed source of truth for `comfyui_mcp_bridge.py` lives under `image-tools/`
   (e.g. `image-tools/mcp/comfyui_mcp_bridge.py`), NOT inside either book repo.
   Both repos register the same neutral bridge in their `.mcp.json`; pub-clr keeps
   only a thin pointer/README under `.claude/mcp/connectors/`. `product-doctor`
   does a sha256 drift check (neutral source vs installed copy). Coordinate/record
   the equivalent repoint for publish-bk.

2. **Cover rendering — DECIDED: AI art with reserved white space + Claude adds
   the fonts.** Generation models are poor at typography, so:
   - The ComfyUI **positive prompt for cover art MUST instruct the model to leave
     appropriate/relevant white space** (e.g. a clean upper band for the title, a
     lower area for author/series, uncluttered margins) so real type can be placed
     into that negative space. No in-image text is requested.
   - **Claude then composites real typography** (title/subtitle/author/series +
     count callout) into the reserved white space using the **compositor +
     rights-cleared embeddable fonts** ported from publish-bk (see below),
     preserving the existing spine-width math in `build_cover`. Determinism,
     rights-clean fonts, and thumbnail legibility are preserved.
   - **Fonts:** copy publish-bk's `.claude/config/fonts/`, `licenses/`,
     `dependencies.default.json`, `dependencies.py`, and `compositor.py` into
     pub-clr. The compositor's hard font gate (refuse system-font fallback) is
     kept. This is now part of Phase 1 (config/deps) + Phase 3 (cover compositor).
   - Keep the existing pure-procedural drawing as a `--style procedural` fallback
     when ComfyUI is unavailable.

3. **Coloring pages — flux-schnell default for line art**, SDXL fallback, with a
   strong **black-and-white line-art positive prompt** ("clean black outline
   coloring page, white background, no shading, no grayscale, bold even line
   weight") because negatives are inert on flux (CFG≈1). Post-process to enforce
   pure high-contrast B&W (rule 22: coloring interior `colour_interior=false`).

4. **Asset & inspiration paths — DECIDED.** Generated assets go to
   `projects/<id>/visuals/assets/` (matches publish-bk). Inspiration examples go to
   `projects/<id>/visuals/inspirations/` (covers and coloring both under this
   folder; subfolders `cover/` and `images/` MAY be used to disambiguate). The
   standalone inspiration skill also accepts an explicit **`--inspiration-dir <path>`**
   for an ad-hoc folder outside the project (DECISION #4: support both).

5. **Human gate posture — unchanged.** Generation is spend-adjacent/external-
   adjacent, so `image_generation.mode` ships `manual-only`; auto requires the
   gitignored `tools.local.json` + `IMAGE_GEN_LIVE_ENABLED=1` + reachable bridge.
   Generation completing is NEVER acceptance — always route to an independent
   visual review before the interior/cover gate. (Constitution §9, §11; rule 03.)

6. **Rights.** Both local providers are `commercial_rights_verified: true` →
   `cleared` records. Fonts clear at selection time via the dependency registry
   (`cleared` iff embeddable + commercial). Inspiration-derived assets are still
   original AI output; each inspiration source is recorded as *reference only, not
   traced/derived* with its own ledger note (rule 07/12). Never mark an asset
   cleared because a human eyeballed it — clearance is provider/registry-driven.

---

## 2. Phases (tracked; each has a checkbox + acceptance test)

> Update the checkboxes and the "Status" line as you go so a fresh session can
> resume. Do not mark a phase done until its acceptance test passes.

### Phase 1 — Offline core + config + MCP wiring (foundation)  ☐ NOT STARTED

Goal: pub-clr can *describe, guide, ingest, and rights-record* AI images exactly
like publish-bk, and the ComfyUI MCP bridge is registered and reachable — **no
new visual output yet**, just the plumbing and its safety gates.

Steps:
1. **Port the offline core.** Copy `publish-bk/.claude/scripts/publishing_house/image_gen.py`
   into `pub-clr/.claude/scripts/publishing_house/image_gen.py`; adapt to pub-clr
   conventions:
   - Asset dir is **`visuals/assets/`** (DECISION #3, matches publish-bk). Confirm
     the brief location (`visuals/briefs/`) against pub-clr `paths.py`; add a
     `visuals/` convention to `paths.py` if not present.
   - Reuse pub-clr's `rights.add_rights_record`, `artifacts.register_artifact`,
     `util.*`; confirm signatures match (they differ slightly between repos).
   - Keep it **network-free** (rule 18) — no imports of state/gate/generator/builder
     beyond what publish-bk imports.
2. **Port the font-clearance subsystem** (needed by the cover in Phase 3; belongs
   in the foundation because both are config/deps + a rights-gated registry):
   - Copy `.claude/config/fonts/` (~50 MB `.ttf`), `.claude/config/licenses/`
     (`OFL-1.1.md`, `Apache-2.0.md`), and `.claude/config/dependencies.default.json`.
   - Copy `publishing_house/dependencies.py` (`font_registry`, `select_font`) and
     add the `dependency select`/`dependency status` CLI verbs.
   - Copy `publishing_house/compositor.py` (deterministic Pillow caption
     compositor with the hard font gate). Add `Pillow` to the venv requirements if
     absent; keep it out of the network-free core's import surface appropriately.
   - Ensure any font families named in pub-clr's `design_policy.json` exist in the
     registry (analog of trim keys in `TRIM_SIZES`); add if missing.
3. **Add the `image-gen` CLI subcommand** to `cli.py` (`status`, `guide`, `ingest`,
   `providers`) mirroring publish-bk's argparse wiring.
4. **Add `tools.default.json`** under `.claude/config/` with the `image_generation`
   block (providers: `local-sdxl`, `local-flux-schnell` verified true; hosted/`-dev`
   false; `mode: manual-only`; `default_provider: local-flux-schnell`). Add
   `tools.local.json` + `dependencies.local.json` to `.gitignore`; document the
   `mode: auto` override.
5. **Promote the bridge to the neutral home (DECISION #1):** create
   `image-tools/mcp/comfyui_mcp_bridge.py` as the single source of truth (move the
   existing reviewed copy there; do not edit behavior). Leave pub-clr a thin
   pointer/README under `.claude/mcp/connectors/` describing the neutral location.
6. **Register `comfyui-mcp` in `.mcp.json`** pointing at the neutral bridge (the
   human does this by hand if a security hook blocks editing `.mcp.json` — include
   `FLUX_WEIGHT_DTYPE: "default"` for Apple silicon). Repoint publish-bk's
   `.mcp.json` at the same neutral bridge and record it.
7. **Extend `product-doctor`** to report: image_generation mode, providers +
   verified flags, font-registry clearance summary, `IMAGE_GEN_LIVE_ENABLED`,
   bridge reachability (best-effort), and a sha256 drift check between the neutral
   bridge source and the installed copy.
8. Unit tests (rule 18): provider registry ordering/merge, `ingest` rights record
   fields (cleared vs pending by provider), `select_font` clearance logic (cleared
   iff both flags), compositor font-gate refusal on an uncleared font, guide
   determinism, path containment (asset must resolve inside project).

Acceptance test:
- `.venv/bin/python3 .claude/scripts/ph_cli.py image-gen status <existing-project>`
  prints providers, mode, live flag, and brief readiness — with no network call.
- `... dependency status <project>` lists fonts with clearance flags.
- New unittests pass; `product-doctor` shows the ComfyUI + font sections.
- `.mcp.json` (both repos) point at the neutral bridge; `health_check` reachable
  in a restarted session (manual verification note recorded in this plan).

### Phase 2 — Coloring-book line-art generation + audit  ☐ NOT STARTED

Goal: turn the existing line-art *briefs* into actual rendered, B&W, printable,
originality-checked coloring pages.

Steps:
1. **Bridge briefs → generation.** Extend `generators/coloring.py`'s `line-art-brief`
   so each brief carries a `generation_prompt.positive` (+ inert negative) tuned for
   B&W coloring line art and dimensions/DPI for the trim (rule 09/11/22). Keep the
   originality attestation.
2. **New skill `product-generate-images`** (port/adapt `book-generate-images`):
   human elicits auto-vs-manual + provider; per brief calls the bridge
   (`provider="local-flux-schnell"`, thread the provider through — see guide §3
   caveat), saves PNG, runs `image-gen ingest`, then post-processes to enforce
   pure high-contrast B&W (no grayscale) suitable for a coloring interior.
3. **New audit skill `product-coloring-line-art-review`** (adapt publish-bk's
   `coloring-line-art-review` pattern which pub-clr already lists as an agent-skill):
   per-asset checks — originality/no-IP, printability, line-weight/contrast at trim,
   age-appropriateness (rule 06 for kids bands), alt-text/decorative designation.
   Produces a deduplicated structured finding register (review-contract).
4. **Wire into interior build.** `product-build-interior` places approved coloring
   PNGs one-per-page at target trim/DPI, back-only nothing (no answer keys), even
   page count. Generation completing ≠ acceptance — review gate first.
5. Update agents `visual/coloring-line-artist.md` + `content` docs to delegate to
   the new skill; update rule 07/08/22 references if needed.

Acceptance test:
- For a coloring project, `product-generate-images` produces N `*.png` B&W pages,
  each ingested with a `cleared` rights record and provenance (seed, prompt, model).
- `product-coloring-line-art-review` emits findings; a clean asset passes contrast/
  line-weight/originality checks.
- `product-build-interior` assembles a coloring interior PDF using the rendered art
  at correct trim/DPI; a manual eyeball confirms it reads as real coloring pages.

### Phase 3 — Commercial-grade cover (AI art + typographic overlay) + inspiration  ☐ NOT STARTED

Goal: replace the flat navy cover with an art-backed, retail-quality wrap; add the
inspiration capability for covers AND coloring images.

Steps:
1. **Cover-art brief with reserved white space (DECISION #2).** `art-director`/
   `cover-designer` produce a cover *art background* brief with a
   `generation_prompt.positive` that **explicitly instructs the model to leave
   appropriate/relevant white space** for typography — e.g. "clean uncluttered
   upper third for a title, calm lower band for author/series, generous margins,
   no text, no lettering, no watermark." Palette from `colour_policy`, mood from
   audience/age band, dimensions = front-panel px at 300 DPI + bleed. Record
   provenance/rights via `image-gen ingest`.
2. **Two-layer cover build (art + code typography).** Refactor
   `layout.py::build_cover` to a new `--style art` path that uses the ported
   **compositor + rights-cleared fonts**: (a) place the generated front-cover art
   (full-bleed on the front panel); (b) draw REAL title/subtitle/author/series +
   count callout into the reserved white space using an embeddable **cleared** repo
   font (hard font gate — refuse system fallback), with legible contrast (auto
   scrim/drop-shadow only if contrast check fails); (c) build spine + back panel
   (art or solid) with description/features. Keep spine-width math and
   `cover-spec.json` output. Keep the pure-procedural drawing as `--style
   procedural` fallback when no art/ComfyUI. Preserve register_artifact/hash.
3. **Cover art review.** Extend cover review to check: thumbnail legibility at
   channel min size, title contrast over art, that type sits within the reserved
   white space (not over busy art), trim/bleed/DPI, no IP/likeness, AI-disclosure
   text present. Feed the cover gate (`product-approve-cover`), which still binds
   the SOURCE (art-direction) hash, not the downstream PDF (rule 03).
4. **Inspiration capability (NEW). Design + implement:**
   - Folder convention (DECISION #3/#4): `projects/<id>/visuals/inspirations/`
     (optional `cover/` and `images/` subfolders to disambiguate cover vs coloring).
     The standalone skill also accepts an ad-hoc **`--inspiration-dir <path>`**.
   - New skill `product-inspire-from-examples` (and an `--inspiration-dir` mode on
     `product-generate-images`): reads example images and — **without copying** —
     extracts *style descriptors only* (palette, composition, line-weight, mood,
     motif category, typographic feel) into a structured `inspiration-analysis.json`
     under `visuals/`. It MUST NOT pass the examples as image-conditioning/img2img,
     MUST NOT reproduce identifiable characters/logos/trade dress, and MUST record
     each source as "reference-only, not traced/derived" in the rights ledger
     (rule 07/12).
   - The derived descriptors are merged into the `generation_prompt.positive` for
     the cover-art or coloring brief. An **originality-auditor** pass compares
     output against the inspiration sources and flags material similarity
     (existing `originality-auditor` agent + an embedding-free heuristic;
     escalate close matches as blockers).
   - Guardrails doc: what "inspiration, not copy" means operationally; refuse a
     folder that appears to be a single competitor's book to be cloned.
5. Rules/standards: add `.claude/rules/23-image-generation.md` (providers, gates,
   provider→rights mapping, threading provider through, B&W coloring rule, cover
   art+reserved-white-space+code-typography rule, font-gate) and
   `.claude/rules/24-inspiration.md` (reference-only, no trace/img2img, similarity
   audit, rights recording). Add/extend a standards contract for image provenance
   and font selection if needed.

Acceptance test:
- A rebuilt cover for the seniors sudoku project (`--style art`) visibly reads as a
  commercial book: art background, legible title at thumbnail size, correct
  trim/bleed/spine; `cover-spec.json` unchanged in schema.
- Given a folder of example covers, `product-inspire-from-examples` yields a
  descriptors JSON + rights "reference-only" records, and generated art passes the
  originality-auditor similarity check (no material copy).

### Phase 4 — Docs, operator guide, shared-infra hardening, end-to-end  ☐ NOT STARTED

Goal: make it reproducible, safe, and shared cleanly between the two repos.

Steps:
1. **Port & adapt the operator guide** to `docs/comfyui-image-generation-guide.md`
   in pub-clr (ground truth paths, weights, Apple-silicon fp16 lesson, the three
   safety gates, provider→rights table, coloring + cover specifics, inspiration
   usage, troubleshooting). Cross-link from `publishing-help`.
2. **Setup script** `setup-comfyui-bridge.sh` (idempotent): install `mcp<2` +
   `Pillow` into the ComfyUI/tooling venv, copy the **neutral** bridge
   (`image-tools/mcp/comfyui_mcp_bridge.py`) to the ComfyUI install path, verify
   import + py_compile + sha256 match. Document in the guide (mirror publish-bk 2C).
3. **Shared-infra doc** `docs/shared-comfyui-infra.md`: the neutral single-source-
   of-truth bridge under `image-tools/`, how both repos register the same
   `comfyui-mcp` pointed at it, the drift check, and how to update the bridge in one
   place. (Records Decision #1.)
4. **End-to-end dry run** on one coloring project and one puzzle-cover project with
   the live bridge (manual verification, results recorded in this plan). Confirm
   fallback-to-manual works when ComfyUI is down.
5. **framework-learn** pass: promote durable learnings (fp16 on MPS, provider
   threading, B&W enforcement, inspiration guardrails) into memory/framework.

Acceptance test:
- A brand-new session, following only `docs/comfyui-image-generation-guide.md`,
  can generate + ingest + review + build a cover and a coloring interior.
- `product-doctor` reports the ComfyUI section green; bridge sha256 matches across
  repo copy + installed copy.

---

## 3. Constraints & guardrails to honor throughout (constitution + rules)

- **Determinism / offline core (rule 18):** `image_gen.py` and all generators/
  builders stay network-free; generation egress lives only in the MCP bridge.
- **Gates (constitution §9/§11, rules 00/02):** generation is never approval;
  human decides compliance/release; craft gates may auto-approve on PASS evidence.
  `mode: manual-only` ships default; auto is opt-in + `IMAGE_GEN_LIVE_ENABLED=1`.
- **Rights (rules 07/12):** provider `commercial_rights_verified` drives clearance;
  inspiration sources recorded reference-only; no tracing, no living-artist imitation,
  no IP/trade-dress/likeness reproduction. Any unresolved rights issue blocks release.
- **Colour policy (rule 22):** coloring interior is B&W (`colour_interior=false`);
  whole-page colour rule for covers/colour pages.
- **Child content (rule 06):** kids-band coloring imagery friendly, no scary/violent
  themes; child-safety review before interior gate for child bands.
- **Provenance (rule 03):** register every asset with seed/prompt/model; downstream
  PDFs are distinct artifacts, not bound by upstream gate approvals.
- **Security (rule 17):** never read secrets; bridge is local-only; no external
  writes; `.mcp.json` edits done by the human if the security hook blocks them.
- **Never overwrite approved/frozen artifacts (constitution §5):** new revisions only.

## 4. Resolved decisions (locked by user 2026-08-16)

1. **Bridge sharing:** neutral home under `image-tools/` (single source of truth);
   both repos register that same bridge; pub-clr keeps only a pointer.
2. **Cover approach:** AI art with the prompt instructing the model to reserve
   appropriate white space; Claude composites real typography in cleared,
   embeddable repo fonts (copied from publish-bk). Not model-rendered title text.
3. **Asset dir:** `projects/<id>/visuals/assets/`. **Inspirations dir:**
   `projects/<id>/visuals/inspirations/`.
4. **Inspiration:** both — the `visuals/inspirations/` folder convention AND a
   standalone skill with an explicit `--inspiration-dir <path>` argument.

## 5. Resume checklist (for a fresh session)

1. Read this file top-to-bottom; check the Status line and phase checkboxes.
2. `git status` / `git log` to see what's landed; re-read any changed
   `image_gen.py`, `layout.py`, new skills, and `tools.default.json`.
3. Verify ComfyUI is running (`curl -s http://127.0.0.1:8188/system_stats`) and
   `comfyui-mcp` is connected (`/mcp`) before any live generation.
4. Continue at the first unchecked phase; run that phase's acceptance test before
   checking it off.
