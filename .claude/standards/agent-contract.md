# STD-AGENT — Agent Contract

Every agent definition SHALL identify a stable ID, role, department, mission, trigger conditions, required inputs, outputs, tool boundaries, prohibited actions, quality rubric, stop conditions, and escalation conditions.

An agent SHALL:

1. Read the active project state and relevant approved artifacts before acting.
2. Work within a bounded assignment and produce artifacts only in the assigned project.
3. Distinguish evidence, inference, recommendation, and uncertainty.
4. Emit structured findings or deliverables at the declared path.
5. Register material artifacts or instruct the orchestrator to register them.
6. Avoid approving its own work.
7. Stop on missing approvals, rights ambiguity, safety risk, conflicting requirements, or inability to verify a material claim.
8. Preserve confidential and unpublished material.

Review agents SHALL not silently edit the reviewed artifact during the first pass. Producer agents SHALL not close findings without independent verification.

A generator agent SHALL NOT verify its own puzzle solutions or coloring-art originality; verification is a separate agent or script. Verification results must reference the script exit code and output hash, not the agent's own judgment.

## Completion contract (STD-AGENT-COMPLETION)

Every agent SHALL end its run by returning a concise completion summary containing:

- exact input and output paths/hashes;
- actions performed and tools used;
- findings by severity;
- rubric scores and confidence;
- unresolved questions, limitations, and risks;
- PASS, CONDITIONAL_PASS, FAIL, or ESCALATE;
- the next valid action.

An agent definition MAY cite this block in one line (e.g. "Completion contract:
follow STD-AGENT-COMPLETION in `.claude/standards/agent-contract.md`.") instead
of restating it, and MAY add role-specific fields to the summary where its work
requires them.
