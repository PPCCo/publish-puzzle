# Design policy

Craft parameters are DERIVED, not hand-picked per product.

- The design-policy engine (`publishing_house.design_policy.derive_design`,
  driven by `.claude/config/design_policy.json` and `.claude/config/age_bands.json`)
  and expert agents SHALL derive craft parameters from `audience` + `product_family`
  + the numeric age band.
- Derived parameters include: `trim_size` (and candidate set), colour policy
  (`colour_interior` + `colour_policy`), tone register, visual density,
  grid/cell size minimums, emotional-intensity ceiling, difficulty progression
  approach, and binding/paper hints.
- Humans SHALL NOT pick these values per product. Human judgment sets the
  audience and product_family inputs, and the human approval gates (niche, interior,
  cover, compliance, listing, release) approve the resulting product; humans do not
  override individual craft literals per project outside a recorded revision.
- Every derived field SHALL carry a recorded `rationale` and `provenance`
  (which config key and which input produced it), stored under
  `production.design` in `project.yaml`.
- Expert agents (audience strategist, art director, puzzle-difficulty designer)
  MAY refine values WITHIN the recorded policy and MUST record why;
  they do not invent craft parameters from scratch.
- The engine is deterministic and offline: no network, no clock reads, stable
  key ordering, no state mutation. It runs at project init inside the pre-niche
  autonomous zone and never mutates workflow state or approvals.

## Derivation examples (not hard-coded literals)

- A coloring-book for `kids-4-8` resolves to a square trim and large open line-art
  cells BECAUSE the config crosses an illustration-led product_family with a young
  band, not because specific measurements are written into any module.
- A puzzle-book for `adult-general` resolves to a standard `8.5x11` or `6x9` trim
  because it is the derived default for a grid-forward form and audience.

## Backward compatibility

- `production.colour_interior` remains a boolean and MUST stay consistent with
  `production.colour_policy.colour_interior_default`. Both are single-sourced
  from `publishing_house.project.default_colour_policy`, which the engine reuses
  verbatim. The colour deriver is never duplicated.

## Constraints preserved

- The engine SHALL NOT weaken `state.transition_blockers` or `required_gate`.
- The engine SHALL NOT approve, freeze, release, or perform external writes.
- Trim values SHALL be keys present in `publishing_house.print_pdf.TRIM_SIZES`
  so the print builder can render the derived trim.
