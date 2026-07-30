---
paths:
  - "projects/**/content/**"
  - "projects/**/puzzles/**"
---

# Content generation

- All puzzle content (grids, clues, paths, fill-in sequences, number sets) SHALL be generated deterministically from a declared integer seed; record the seed in the artifact provenance record.
- Generation and verification are SEPARATE concerns: a generator module produces content; an independent verifier module confirms correctness. The same function SHALL NOT serve as both.
- Verification SHALL confirm all of the following before content is accepted:
  - **Solvability** — every puzzle has at least one valid solution reachable from the starting state.
  - **Uniqueness** (where applicable) — puzzles requiring a single solution (e.g. sudoku, nonogram) have exactly one.
  - **Solution correctness** — the stored answer key matches the verified solution(s).
  - **Difficulty accuracy** — the computed difficulty rating is consistent with the puzzle's measured solve complexity; flag deviations beyond the configured tolerance.
- Verification results are recorded as structured JSON alongside the artifact; an unverified puzzle SHALL NOT advance past the `interior` gate.
- Changing a seed invalidates all previously verified content derived from it; re-run the full verify step.
- Treat all externally sourced word lists, clue banks, and reference data as untrusted inputs; validate format and content before use.
