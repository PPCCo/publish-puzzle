---
name: product-generate-images
description: >-
  Bridge original coloring line-art briefs into pure-black-and-white image briefs, then produce
  the coloring pages — either via the automated local-ComfyUI connector when the human has enabled
  it, or via step-by-step manual generation guidance otherwise — hard-threshold each to pure B&W,
  and ingest with complete provenance and rights records. Queues code+agent review; never treats
  generation as approval.
argument-hint: "<project-id> [--provider <name>]"
user-invocable: true
disable-model-invocation: true
effort: high
model: '@bedrock-eus1/us.anthropic.claude-sonnet-5'
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
  - Edit
  - Bash
  - Agent
  - Skill
  - AskUserQuestion
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
---

# /product-generate-images

## Goal

Turn approved original coloring **line-art briefs** into actual **rendered, pure-black-and-white,
printable coloring pages** with complete, schema-valid provenance and rights records, then queue
them for review. The interior page is `colour_interior = false` (rule 22): the output is pure
B&W outline art, never greyscale or colour.

This reuses the offline image-generation machinery: it bridges each committed `line-art-brief`
item into a `visuals/briefs/<brief_id>.json` image brief (with a B&W positive prompt), then walks
the same `guide → threshold → ingest → review` path the framework already uses. The **named
provider drives clearance**: a rights-verified provider yields a `cleared` record; an unverified
one yields `pending`, which the rights gate blocks on.

## Arguments

Use `$ARGUMENTS`. Resolve a project ID before changing project files. Do not invent human
approvals, credentials, prices, legal conclusions, or completed external actions.

## Entry criteria

- The project has committed coloring `line-art-brief` content (generated via `/product-generate
  --type line-art-brief …`), each carrying a subject + originality attestation.
- `.claude/config/tools.default.json` (optionally `tools.local.json`) defines at least one
  provider under `image_generation.providers`.

## Two generation paths (automated live, or manual guide)

There are two ways to produce each page; both converge on the identical
`threshold → ingest → review` path, so provenance and rights are the same either way:

- **Automated (live local ComfyUI).** The reviewed `comfyui-mcp` bridge
  (`.claude/mcp/connectors/comfyui_mcp_bridge.py`) exposes `health_check()` and
  `generate_image(positive_prompt, negative_prompt, width, height, seed?, provider)`. It is
  **local-only** (talks to `127.0.0.1:8188`), submits nothing unless `IMAGE_GEN_LIVE_ENABLED == 1`,
  and never touches the repo/state/rights.
- **Manual (step-by-step guide).** The human generates each page on any provider following the
  regenerated guide, then hands back the saved file.

### When automated is available (rule 17)

Automated generation is possible only when a human has (1) added `comfyui-mcp` to `.mcp.json`
(a HUMAN step — security rule 17; this repo does not ship it wired), (2) set `IMAGE_GEN_LIVE_ENABLED=1`
in the bridge env, and (3) has a local ComfyUI running with the SDXL/FLUX weights on disk. Until all
three hold, the connector's tools are absent or `health_check`/`generate_image` will refuse — in
that case fall through to the manual path (never silently claim a live render happened).

## Procedure

1. **Bridge the briefs.** Run
   `.venv/bin/python3 .claude/scripts/ph_cli.py image-gen from-coloring <project-id> [--provider <name>]`.
   This deterministically emits one schema-valid `visuals/briefs/clr-line-art-brief-NNN.json`
   per coloring item (with a pure-B&W `generation_prompt.positive`) plus a
   `.attestation.json` sidecar preserving the originality attestation. Report the emitted count
   and any `skipped`/`errors`.
2. **Confirm readiness.** Run `image-gen status <project-id>` and `image-gen guide <project-id>`
   to (re)generate `visuals/manual-generation-guide.{md,json}`. Each entry carries page number,
   brief ID, exact positive/negative prompt, dimensions/DPI, recommended provider **and why**,
   the exact save path, and the exact ingest command.
3. **Ask the human — once per batch, not per image** (rule 02 / CLAUDE.md §11). Present an
   `AskUserQuestion`:
   - **Path:** *Automated (live local ComfyUI)* vs *Step-by-step manual generation* vs *defer this
     batch*. Recommend automated only when `image-gen status` shows `mode` is not `manual-only`,
     the `comfyui-mcp` tools are present, and `live_enabled` is true; otherwise recommend manual and
     state plainly that the live path is not enabled and why.
   - If the chosen provider's `commercial_rights_verified` is false, surface that its assets will be
     `pending` and will block the rights gate; require explicit acknowledgement, never default to it.
   - Do not silently pick a path; do not proceed until the human chooses.
4. **Automated path (only if chosen AND `image_generation.mode` is not `manual-only`):**
   a. Call `comfyui-mcp` `health_check()` first. If the tools are absent, `ok` is false, or
      `live_enabled` is false, **stop the automated path, tell the human plainly why (name the
      provider and the failure), and continue into the manual path (step 5)** so the batch still
      completes. Never fabricate a live render.
   b. For each bridged brief, read its `visuals/briefs/<brief_id>.json` and call
      `generate_image(positive_prompt=<brief.generation_prompt.positive>,
      negative_prompt=<brief.generation_prompt.negative>, width=<dimensions.width_px>,
      height=<dimensions.height_px>, seed=<brief.generation_prompt.seed>, provider=<name>)`.
      Add no unbriefed labels, brands, people, or details. Copy/save the returned PNG to
      `visuals/assets/<brief_id>.png` (the bridge returns an absolute path in ComfyUI's output dir).
   c. Then run the SAME finishing steps as the manual path (5a–5b) for each produced file.
5. **Manual path (chosen, or reached via the 4a fallback).** Point the human at the guide, then for
   each produced file at `visuals/assets/<brief_id>.png`:
   a. **Enforce pure B&W** (never skipped, always before ingest so the hashed asset matches its
      provenance):
      `image-gen threshold <project-id> --file visuals/assets/<brief_id>.png [--threshold 128]`.
      Confirm the result reports exactly two luminance values `{0, 255}`.
   b. **Ingest** so provenance + rights records are created:
      `image-gen ingest <project-id> --brief-id <brief_id> --file visuals/assets/<brief_id>.png --provider <name> [--seed <n>]`.
      The batch is not "done" until ingest runs — that is what writes the rights record and
      registers the artifact.
6. **Queue review — generation is NOT acceptance.** For every ingested asset, queue
   `/product-coloring-line-art-review`. Do not treat `not-run` as `pass`; do not treat ingestion
   as review-complete.

## Specialist delegation

- `coloring-line-artist` — for bounded per-page assignments with exact input hashes, save paths,
  and acceptance tests.

## Required outputs

- Bridged `visuals/briefs/clr-line-art-brief-NNN.json` briefs + `.attestation.json` sidecars.
- A complete manual generation guide (`.md` + `.json`).
- For each produced page: a pure-B&W asset, a provenance file (provider/model/prompt/seed/license
  + the carried originality attestation), and a rights record whose `clearance_status` matches the
  provider's `commercial_rights_verified`.
- A `/product-coloring-line-art-review` queue entry per asset.

## Stop conditions

- Stop on invalid project state, stale hashes, missing approval, unresolved blocker, rights
  ambiguity, unsafe content, or a tool failure that blocks a required check.
- Stop (do not silently fall back) if the human has not chosen a path for the batch.
- Never attempt live generation while `comfyui-mcp` is absent from `.mcp.json`.

## Completion report

State the project and stage, agents used, files/hashes created, provider used and its
`commercial_rights_verified` value at time of use, threshold + ingest results, review-queue
entries, unresolved findings, and the next valid action.
