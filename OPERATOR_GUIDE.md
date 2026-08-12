# Operator Guide

This guide is for the human publisher operating the puzzle/printable publishing house.

## 1. First run

```bash
cp .claude/settings.local.example.json .claude/settings.local.json
python3 -m venv .venv && . .venv/bin/activate
.venv/bin/python -m pip install -e '.[dev,mcp]'
python3 .claude/scripts/ph_cli.py doctor
python3 .claude/scripts/ph_cli.py framework validate
```

`doctor` checks dependencies, the model pin, and optional tools. `framework validate`
confirms the agent/skill/workflow/schema inventory and safety settings.

## 2. Daily loop

1. `/product-status <id>` or `python3 .claude/scripts/ph_cli.py project status <id>`.
2. `/product-plan <id>` (`project plan <id>`) for the deterministic next action.
3. `/product-run <id> --until human-gate --max-stages 3` to advance validated non-gate stages.
4. Inspect the prepared gate packet, then run the matching human-only approval skill.

## 3. The six gates

There are six gate checkpoints. A human MUST decide **compliance** and **release**. The
craft/quality gates (**niche, interior, cover, listing**) MAY be auto-approved by the
configured `auto_approve_gates` policy when their deterministic gate evidence PASSes and
no blocker or major finding is open; you keep override and review the final product.
Auto-approvals are recorded with the configured default approver and remain fully
auditable in `events.ndjson`. Any safety override (evidence not PASS, an open
blocker/major, or a rights/child-safety concern) forces the interactive human path
regardless of policy.

| Gate | Decision | Skill | What is approved |
|---|---|---|---|
| Niche | auto-approvable | `/product-approve-niche` | The niche is worth producing; evidence is dated |
| Interior | auto-approvable | `/product-approve-interior` | Code-verified content batches; freezes them by hash |
| Cover | auto-approvable | `/product-approve-cover` | Original line art / cover design |
| Compliance | **human** | `/product-approve-compliance` | Accessibility, rights, child-safety, AI disclosure |
| Listing | auto-approvable | `/product-approve-listing` | Metadata and channel listings |
| Release | **human** (two approvers) | `/product-release-authorize` | Final packages |

Each gate binds to exact **source** artifact hashes (the content/design/metadata it
approves). Approvals are invalidated automatically when a bound source hash changes;
re-rendering a downstream build output (interior/cover PDF, channel package) from an
unchanged approved source does NOT invalidate the approval.

## 4. Reading a gate packet

Run `approval packet <id> --gate <gate>` (or `/product-gate-packet`). The packet lists
the exact hashes, evidence, open findings, and available decisions. Never approve a
packet with open blockers, majors, stale hashes, or a not-run verification.

## 5. Content: generate then verify

Never trust a generator's own claim. After `generate`, always run `verify`:

```bash
python3 .claude/scripts/ph_cli.py generate <id> --type wordsearch --count 40 --difficulty medium --seed 777 --actor puzzle-generator
python3 .claude/scripts/ph_cli.py verify <id> --type wordsearch
```

Use the `content-generation-fanout` workflow for large parallel batches; it always
verifies independently before synthesis.

## 6. When to escalate

- Verification FAIL, non-unique solutions, or answer-key mismatches.
- Any originality/similarity or rights concern.
- Accessibility FAIL for the audience band.
- Revision limits exceeded (3 full cycles / 5 targeted repairs).

## 7. Release

Release authorization is human-only and needs two approvers, exact package hashes, and a
zero-blocker final red-team. External submission is disabled by default; `product-submit`
records the manual action.
