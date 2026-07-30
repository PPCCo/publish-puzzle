# Deterministic hooks

These command hooks enforce repository boundaries and produce local audit records.

| Hook | Responsibility |
|---|---|
| `session_start.py` | Inject model pin, external-write state, and project-count context at session start; remind operators to run `/product-status` or `/product-resume` before modifying a product. |
| `pre_tool_policy.py` | Block destructive commands, secrets, configuration tampering, unapproved network writes, and write-capable MCP tools. |
| `post_tool_audit.py` | Record successful tool use and hash files written inside a project. |
| `subagent_event.py` | Record specialist-agent start and stop events. |
| `stop_audit.py` | Record changed-file inventory when a turn ends. |

The policy hook returns a structured `PreToolUse` denial. It tightens permissions and does not auto-approve tools. Hooks cannot replace marketplace-side permissions (KDP, Etsy, Gumroad), API scopes, legal review, rights clearance, or human release authorization.
