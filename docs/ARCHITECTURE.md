# Architecture Notes (Detail)

This supplements the top-level `ARCHITECTURE.md` with subsystem detail.

## Deterministic spine

`ph_cli.py` dispatches to the `publishing_house` package:

- `project.py`, `state.py`, `events.py` — lifecycle, transitions, append-only history.
- `planner.py` — deterministic next-action recommendation used by the run loop.
- `generators/` — per-type deterministic content generators (puzzles, logic, activity, coloring, journal, printable) from a base generator.
- `generate.py` / `verify.py` — the generate/verify split; verification is independent of generation.
- `quality.py`, `rights.py`, `accessibility.py`, `metadata_audit.py` — gate evidence.
- `layout.py`, `packages.py`, `submission.py` — builds, channel packages, submission records.
- `approvals.py`, `gate_packet.py` — human-gate packets and hash-bound approvals.
- `artifacts.py`, `catalog.py`, `series.py` — registry, index, multi-volume linking.
- `validation.py`, `doctor.py` — framework and environment checks.
- `design_policy.py`, `util.py`, `paths.py`, `errors.py`, `markdown.py`, `niche.py` — policy resolution, repo-root resolution, helpers.

## Repo-root resolution

`util.repo_root()` walks up looking for a directory containing both `.claude/` and
`.claude/CLAUDE.md`. `CLAUDE.md` is therefore a functional prerequisite, not just docs.

## Config is authority

`.claude/config/` holds the state machine (`workflow_states.json` with `gate_edges` and
`gate_reports`), `quality_gates.json`, `age_bands.json`, `design_policy.json`,
`state_playbook.json`, and channel profiles. Policy changes happen in config, not code.

## Content integrity path

generate (seed) → register artifact (hash) → independent verify (hash) → review →
bounded revision → re-verify → interior gate freeze (hash) → downstream production.
