---
paths:
  - "projects/**/content/**"
  - "projects/**/puzzles/**"
---

# Puzzle and activity content

- Follow the approved brief, audience profile, difficulty progression spec, style sheet, and canon.
- **Grid legibility** — cell size, line weight, and font size SHALL meet the minimum dimensions for the target audience band and format (print or digital-printable); never reduce cell size to fit more puzzles per page.
- **Difficulty progression** — puzzles are ordered easy-to-hard front-to-back within each section; do not interleave difficulty levels without a documented design rationale.
  - **Single-tier plans** — when the approved content plan is a single difficulty tier (e.g. "single-tier easy", one uniform difficulty band with no sub-tiers), a monotonic *within-tier* gradient (such as a rising givens count per puzzle) is NOT required and SHALL NOT be flagged as a defect. A flat givens count / uniform metric is the correct, intended output for a single-tier plan. Difficulty-progression findings apply only to multi-tier plans or plans whose brief explicitly specifies an intra-section gradient. Verifying that every puzzle actually sits within the labeled tier still applies.
- **Solutions placement** — answer keys and solutions are placed at the back of the product by default; never print a solution adjacent to its puzzle unless the product brief explicitly requires it.
- **Instruction clarity** — every puzzle type includes a concise, self-contained instruction block written for the target audience band; do not assume prior puzzle experience.
- Mark unresolved layout dependencies, missing clue sets, and incomplete verifications explicitly; do not hide gaps in content coverage.
- Keep drafts and revisions versioned; do not overwrite a reviewed hash.
