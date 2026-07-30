---
paths:
  - ".claude/workflows/*.js"
---

# Dynamic workflows

- Workflows coordinate agents only; agents perform filesystem, shell, web, and MCP actions.
- Keep human approval between workflows, not inside one run; human gates (niche, interior, cover, compliance, listing, release) SHALL always occur outside a workflow execution.
- Fan-out from project inputs to parallel generation and verification tasks; cap fan-out and deduplicate work items.
- Parallel generation and verification: generation tasks and their corresponding verifier tasks MAY run concurrently within the fan-out; require structured schemas for all generation and verification results.
- Include a final synthesis or verifier phase that aggregates per-item verification results before the workflow reports completion.
- Preserve unverified claims rather than silently treating them as false.
