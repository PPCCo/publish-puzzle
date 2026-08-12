# Governance

- Follow `.claude/CLAUDE.md` and deterministic project state.
- Work from approved inputs and current artifact hashes.
- Never imply that generated content is validated, approved, cleared, submitted, or published without evidence.
- Stop autonomous work at the human-decided gates (compliance, release), at any gate whose resolved `auto_approve_gates` mode is `false`, and at legal/safety escalations. The craft/quality gates (niche, interior, cover, listing) MAY be auto-approved by policy when their deterministic evidence PASSes and no blocker/major finding is open. Where a human must decide, the gate stop MAY be resolved by an in-session interactive human decision (presented via `AskUserQuestion`) or by an explicit approval command — but a human must decide before proceeding.
- Do not use production credentials or perform live external writes.
- Use `SHALL`, `SHOULD`, and `MAY` consistently in specifications.
