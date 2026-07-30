# STD-REVIEW — Review Contract

Each finding SHALL contain:

- unique finding ID;
- reviewer role;
- reviewed artifact ID and hash;
- severity: blocker, major, minor, or note;
- dimension;
- precise location;
- observation;
- evidence or rationale;
- recommended action;
- measurable acceptance test;
- status: open, accepted, rejected-with-rationale, fixed-awaiting-verification, or closed;
- confidence from 0.0 to 1.0.

A reviewer SHALL issue PASS, CONDITIONAL_PASS, or FAIL. The review is invalid when the artifact hash differs from the current artifact or required fields are absent.

Critical dimensions for puzzle/coloring/journal products are: solvability, solution correctness, originality, rights, accessibility, and audience fit. These dimensions require a higher score threshold (per config) and zero open blockers or majors before a gate passes. A reviewer may not close a solvability or originality finding without a corresponding script verification result.
