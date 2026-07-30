# Autonomous Operation

The framework can advance a product through validated, non-gate stages on its own, but
it stops at every human gate and never performs an external side effect.

## What runs autonomously

- Niche assessment scoring (evidence must be dated).
- Content generation by code from a seed.
- Independent content verification by code.
- Structured review, bounded revision, and re-verification.
- Layout/interior/cover/digital builds and preflight.
- Accessibility, rights, and metadata audits.
- Channel package assembly (no live write).

## What always requires a human

- The six gates: niche, interior, cover, compliance, listing, release.
- Release authorization (two approvers, exact package hashes).
- Any external submission, spend, listing change, identifier purchase, or terms acceptance.

## The run loop

`/product-run` (workflow `autonomous-run-loop`) repeats:

1. `project plan <id>` → deterministic next action.
2. If the plan reports a human gate, terminal, or blocked state → STOP with a prepared packet.
3. Otherwise execute exactly one mapped stage, generate+verify, register artifacts, run the gate/validator, and `project transition`.
4. Honor `maximum_full_revision_cycles` from `quality_gates.json` and a hard cap of 5 stages.

A transition correctly fails while any blocker remains; the loop treats that as a STOP,
not something to work around. The loop never invokes an approval, freeze, release, or
submission skill.

## Guardrails

- Deterministic Python owns state, hashes, generation, and verification.
- Hooks deny out-of-scope tool use and audit subagent activity.
- Approvals bind to exact hashes and invalidate on input change.
- External writes are disabled by default.
