---
name: product-coloring-line-art-review
description: >-
  Independently review ingested coloring line-art pages: run the deterministic code checks
  (pure-B&W, printability at trim/DPI, even background, line-weight proxy), then layer agent
  judgment (originality per rule 07, age-appropriateness per rule 06, alt-text quality), and
  synthesize structured findings. Queues the interior gate; never approves.
argument-hint: "<project-id> [--brief-id <id>]"
user-invocable: true
disable-model-invocation: true
effort: high
model: '@bedrock-eus2/us.anthropic.claude-opus-4-8'
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
  - Edit
  - Bash
  - Agent
  - Skill
  - "Bash(${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py *)"
---

# /product-coloring-line-art-review

## Goal

Independently review each ingested coloring page and produce structured, evidence-backed findings
for the interior gate. Verification is separate from generation (CLAUDE.md §4): a generator never
signs off its own output. This skill combines deterministic **code** checks with **agent
judgment**, and it **queues** the interior gate — it never records an approval.

## Arguments

Use `$ARGUMENTS`. Resolve a project ID before reading project files. `--brief-id` restricts the
review to one coloring brief; default is all ingested coloring assets.

## Entry criteria

- One or more coloring line-art assets have been ingested via `/product-generate-images`
  (active `illustration` artifacts mapped to a coloring brief, each with a rights record).

## Procedure

1. **Run the deterministic code checks.**
   `.venv/bin/python3 .claude/scripts/ph_cli.py audit coloring-review <project-id> [--brief-id <id>]`.
   This writes `reviews/coloring-review-latest.json` with per-asset measurements and findings:
   - `pure_bw` — luminance ⊆ `{0, 255}`, exactly two values (else **blocker**: the threshold step
     was skipped or the source had anti-aliasing).
   - `printability_at_trim_dpi` — asset pixels vs the brief's `dimensions` (else **major**).
   - `even_background` — dominant white coverage plausibility (else **major**).
   - `min_line_weight` — minimum stroke *width* (perpendicular thickness, measured with a
     distance-transform medial axis, orientation-independent and speck-robust) vs
     `min_line_weight_pt × dpi / 72` (**major** if under — a human confirms legibility).
   Report the decision and open blocker/major counts. A code PASS is evidence, not approval.
2. **Layer agent judgment** (the code cannot decide these):
   - **Originality (rule 07).** Read each `visuals/briefs/<brief_id>.attestation.json` sidecar and
     the ingested provenance. Confirm the originality attestation is present and consistent (no
     tracing, no third-party/IP source, no living-artist imitation). Delegate to
     `originality-auditor` for material similarity risk when warranted.
   - **Age-appropriateness (rule 06).** For a child/tween band, confirm subject, density, and
     imagery fit the approved age band (friendly/familiar for kids-4-8; nothing violent,
     sexualised, disturbing, or age-inappropriate). Delegate to `child-safety-reviewer` for any
     child-band concern. Escalate immediately on any child-protection concern.
   - **Alt-text quality.** Confirm each asset's brief alt text (or documented decorative
     designation) is meaningful and accurate to the rendered page (rule 09).
3. **Synthesize findings** in the standard shape (severity, dimension, location, evidence,
   recommendation, acceptance test, status), merging the code findings with agent-judgment
   findings. Write them to the project reviews.
4. **Queue the interior gate — do NOT approve.** Route the synthesized findings to the interior
   gate. The interior gate is a human/auto-approve decision made elsewhere (rule 02); this skill
   only assembles the evidence and queues it. Never treat `not-run` as `pass`, and never record an
   approval here.

## Specialist delegation

- `originality-auditor` — material similarity / resemblance risk.
- `child-safety-reviewer` — age-fit and child-safety for child/tween bands.
- `accessibility-auditor` — alt-text and legibility when a deeper accessibility read is needed.

## Stop conditions

- Escalate and stop immediately on any child-safety, originality, or rights concern.
- Stop on a `pure_bw` blocker: the asset must be re-thresholded and re-ingested before review can
  pass. Report the exact recovery action.
- Stop on invalid state, stale hashes, or a tool failure that blocks a required check.

## Completion report

State the project and stage, agents used, the code-review decision and per-dimension findings,
agent-judgment findings, unresolved blockers/majors, and the next valid action (interior gate
queued, or the specific repair required first).
