# Human approval

- A human MUST decide every gate. The decision MAY be collected two ways, both valid:
  - **Interactively in-session** — the assistant presents the gate (scope, exact
    artifact hashes, open findings, risks) and offers the choices via `AskUserQuestion`
    with a Recommended option where applicable, then records the human's selection on
    their behalf. Prefer this in an active project session.
  - **By explicit command** — the human invokes `/approve-*`, `/content-freeze`, or
    `/release-authorize` directly. This remains fully supported (and is the path for
    headless or non-interactive runs).
- In both paths the recording goes through the CLI and is bound to the exact artifact
  hashes and scope in the gate packet.
- A human's `AskUserQuestion` selection is an explicit decision, not inferred approval.
  Never infer approval from silence, from a conversational phrase that does not name the
  gate and artifact scope, or from a prior approval of a different scope.
- Report invalidated approvals immediately after material changes.
- Release authorization never grants permission to accept legal terms or exceed stated
  spend/territory/channel scope.
