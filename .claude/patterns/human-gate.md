# PAT-006 — Human Gate

Six named gates require a full stop: niche, interior, cover, compliance, listing, release. At each gate, stop autonomous work. Present the scope, exact hashes, unresolved risks, cost and rights implications, and available decisions.

Preferred in-session UX: present the decision via `AskUserQuestion` with a Recommended option (Approve is Recommended only when the gate packet is ready — no open blocker or major finding — otherwise Reject/Customize lead), and list the packet's `review_files` so the human knows what to open. The equivalent typed command (the packet's `next_command`) remains valid, especially for headless runs.

However collected, record approval or rejection with the CLI, bound to the exact artifact hashes. A human's explicit `AskUserQuestion` selection is a decision; do not infer approval from silence, prior approvals of a different scope, or general permission to proceed.
