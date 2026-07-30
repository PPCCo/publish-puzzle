# Human approval

- Human approval requires an explicit `/approve-*`, `/content-freeze`, or `/release-authorize` invocation.
- Bind approval to exact artifact hashes and scope.
- Never infer approval from conversational phrases that do not specify the gate and artifact scope.
- Report invalidated approvals immediately after material changes.
- Release authorization never grants permission to accept legal terms or exceed stated spend/territory/channel scope.
