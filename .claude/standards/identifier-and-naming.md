# STD-NAMING — Identifiers and Paths

- Project IDs: `clr-YYYY-slug` where slug is a lowercase kebab-case topic descriptor, max 48 characters (e.g. `clr-2025-halloween-word-search`).
- Artifact IDs: `art-<12 hex characters>` derived from SHA-256 plus semantic type.
- Finding IDs: `fnd-<project>-<sequence>`.
- Asset source IDs: `asrc-<project>-<sequence>`.
- Rights IDs: `rgt-<project>-<sequence>`.
- Approval IDs: `apr-<gate>-<timestamp>-<nonce>`.
- Originality attestation IDs: `orig-<project>-<sequence>`.
- Files use lowercase kebab-case except standards-required names.
- Dates use ISO 8601. Timestamps use UTC with `Z`.
- Puzzle batch revisions include a three-digit sequence: `batch-001`, `batch-002`.
- Product families: puzzle-book, activity-book, coloring-book, guided-journal, workbook, planner, digital-printable.
- Audiences: kids-4-8, kids-6-10, tween-8-12, teen-13-17, adult-general, senior-large-print.
