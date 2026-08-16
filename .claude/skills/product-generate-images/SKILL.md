---
name: product-generate-images
description: >-
  Bridge original coloring line-art briefs into pure-black-and-white image briefs, then produce
  the coloring pages — via step-by-step manual generation guidance (live ComfyUI generation is
  deferred until a human enables it) — hard-threshold each to pure B&W, and ingest with complete
  provenance and rights records. Queues code+agent review; never treats generation as approval.
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

## Deferred live generation (rule 17)

Live ComfyUI generation is **deferred**: `comfyui-mcp` is not wired into `.mcp.json` in this
repository, and adding it is a HUMAN step (security rule 17). This skill therefore drives the
**manual generation guide** path end-to-end and never attempts a live provider call. When a human
has enabled a live provider, the same ingest path applies unchanged.

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
   - **Path:** *Step-by-step manual generation* (Recommended — live ComfyUI generation is deferred
     until a human adds `comfyui-mcp` to `.mcp.json`) vs *defer this batch*. State plainly that
     the live path is not enabled and why.
   - Do not silently pick a path; do not proceed until the human chooses.
4. **Manual path (produce each page).** Point the human at the guide, then for each produced file
   at `visuals/assets/<brief_id>.png`:
   a. **Enforce pure B&W** (never skipped, always before ingest so the hashed asset matches its
      provenance):
      `image-gen threshold <project-id> --file visuals/assets/<brief_id>.png [--threshold 128]`.
      Confirm the result reports exactly two luminance values `{0, 255}`.
   b. **Ingest** so provenance + rights records are created:
      `image-gen ingest <project-id> --brief-id <brief_id> --file visuals/assets/<brief_id>.png --provider <name>`.
      The batch is not "done" until ingest runs — that is what writes the rights record and
      registers the artifact.
5. **Queue review — generation is NOT acceptance.** For every ingested asset, queue
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
