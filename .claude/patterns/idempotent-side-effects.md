# PAT-012 — Idempotent Side Effects

Every external write extension SHALL compute an idempotency key from project, edition, channel, operation, and release hash. Before retrying, query the external system. Record request, sanitized response, external ID, and reconciliation status. Never blindly retry after a timeout with an unknown outcome.
