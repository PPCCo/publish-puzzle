# Workflow state

- Read `state.json` before project work.
- Only `.claude/scripts/ph_cli.py project transition` may mutate workflow state.
- A project may move only through configured transitions defined in `.claude/config/workflow_states.json` (`gate_edges` + `gate_reports`).
- The lifecycle has 26 states; valid transitions and human-gate requirements are config-driven, not hard-coded.
- Human gates are: `niche`, `interior`, `cover`, `compliance`, `listing`, and `release` (release requires 2 approvers).
- A human-gated transition requires a valid, current approval record bound to the exact artifact hashes in scope.
- Conditional stages may be skipped only when `project.yaml` makes them inapplicable and the script records the skip.
- Pause rather than guess when project state and repository files disagree.
