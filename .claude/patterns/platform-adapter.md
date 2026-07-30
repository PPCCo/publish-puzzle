# PAT-010 — Platform Adapter

Each channel adapter (KDP, Etsy, Gumroad, generic) accepts canonical metadata and registered format artifacts (paperback, hardcover, digital-pdf), validates a versioned platform profile, and writes a self-contained package. The base adapter never authenticates or publishes. A live extension must add dry-run, idempotency, exact-scope authorization, redaction, and reconciliation.
