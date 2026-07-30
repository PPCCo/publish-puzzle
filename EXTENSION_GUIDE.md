# Extension Guide

## Add an agent

1. Create `.claude/agents/<department>/<agent>.md` following `.claude/standards/agent-contract.md` (frontmatter: name, description, effort, permissionMode, maxTurns, tools, skills, memory, background, color; body with Mission, Invoke-when, inputs, outputs, Procedure, Quality rubric, Prohibited actions, Escalate-and-stop, Completion contract).
2. Assign the next sequential `AGT-0NN` id and add a row to `.claude/agents/CATALOG.md`.
3. A generator agent must never verify its own output; pair it with an independent verifier.

## Add a skill

1. Create `.claude/skills/<skill>/SKILL.md` following `.claude/standards/` conventions.
2. The last `allowed-tools` entry MUST be `"Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py *)"`.
3. A human-only skill must set `disable-model-invocation: true` and begin its description with `Human-only:`.

## Add a content type (generator + verifier)

1. Implement the generator under `.claude/scripts/publishing_house/generators/<type>.py`, deterministic from a seed, emitting content plus a separable answer key.
2. Implement the **independent** verifier path in `verify.py`: solvability, uniqueness where applicable, answer-key correctness, and measured-vs-labeled difficulty.
3. Never let the generator assert solvability, uniqueness, or difficulty.
4. Add a test fixture that generates and then verifies a small batch.

## Add a format or channel

- Format: implement a builder and preflight validator; extend `design_policy.json`.
- Channel: follow `PLATFORM_ADAPTERS.md`; keep live writes disabled by default.

## Add a workflow

1. Create `.claude/workflows/<name>.js` exporting `meta = {name, description}`.
2. Use `agent()` and `pipeline()` only; the runtime cannot touch the filesystem — spawned agents run `ph_cli.py` verbs.
3. Never grant an approval, freeze, release, or submission inside a workflow.
4. Add a row to `.claude/workflows/README.md`.

## Validate

Run `python3 .claude/scripts/ph_cli.py framework validate` and the test suite after any
extension. The validator enforces minimum agent/skill counts, required human-only skills,
required files, and safety settings.
