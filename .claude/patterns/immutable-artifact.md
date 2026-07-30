# PAT-005 — Immutable Artifact

Never mutate an approved or frozen file. Copy or generate a new revision, register its hash, update the active pointer, and invalidate dependent reviews and approvals. Interior approval is the content-freeze point for verified puzzle, coloring, journal, and printable batches. This pattern prevents stale approval and makes edition history reconstructable.
