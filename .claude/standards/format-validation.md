# STD-FORMAT — Validation Contract

Every release format SHALL produce a machine-readable preflight report. A release artifact must pass required structural validation and manual checks appropriate to the format.

- Print (paperback/hardcover): trim size, bleed, margins, fonts, image resolution, colour handling (per colour_policy), page count, cover dimensions, and physical proof.
- Digital PDF (printable): page size (US Letter or A4), DPI >= 300, bleed as specified, all fonts embedded, no crop marks bleed past safe zone, file list complete.
- Puzzle interior: every puzzle independently verified for solvability and unique solution (where applicable); difficulty labels match measured difficulty; answer key completeness and page accuracy verified by script.
- Coloring interior: all line art original-only attestation on record; minimum line weight met; contrast ratio verified at target trim.
- Journal/workbook/planner interior: page-space targets met; reading-level check for prompts at stated audience band; print safe zone observed.
- Accessibility: contrast ratio, legible type size, and alt text or documented decorative designation required before compliance gate.
