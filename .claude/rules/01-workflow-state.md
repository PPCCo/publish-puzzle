# Workflow state

- Read `state.json` before project work.
- Only `.claude/scripts/ph_cli.py project transition` may mutate workflow state.
- A project may move only through configured transitions defined in `.claude/config/workflow_states.json` (`gate_edges` + `gate_reports`).
- The lifecycle has 26 states; valid transitions and human-gate requirements are config-driven, not hard-coded.
- Human gates are: `niche`, `interior`, `cover`, `compliance`, `listing`, and `release` (release requires 2 approvers).
- A human-gated transition requires a valid, current approval record bound to the exact artifact hashes in scope. That record MAY be produced from an in-session interactive human decision (assistant presents the options and records the choice) or from an explicit approval command; either way it is bound to the exact hashes.
- Conditional stages may be skipped only when `project.yaml` makes them inapplicable and the script records the skip.
- Pause rather than guess when project state and repository files disagree.
