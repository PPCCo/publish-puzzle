# Colour policy

Colour is governed per project by `production.colour_policy` in `project.yaml`.
`project init` sets a default colour policy from the product family and audience band; a human may
override it. The legacy boolean `production.colour_interior` is retained for
backward compatibility and MUST stay consistent with the policy below.

## Print interior defaults by product family and audience band

- `coloring-book` (all audience bands) — full colour interior is not required; the interior is black-and-white line-art by design. `colour_interior = false`. Covers MAY be full colour.
- `colour-by-number` activity pages — treated as a colour product because colour coding is the activity itself. `colour_interior = true`.
- `kids-4-8` puzzle-book or activity-book — full colour interior: both text and images in colour (young readers respond to coloured text). `colour_interior = true`.
- `kids-6-10` puzzle-book or activity-book — images mostly colour, or at least where colour carries meaning. `colour_interior = true`.
- `tween-8-12`, `teen-13-17` — mostly greyscale. Use colour only where it carries meaning (e.g. a colour-coded map, a diagram that depends on colour). `colour_interior = false` unless meaningful-colour images are used, in which case set it true and record why.
- `adult-general`, `senior-large-print`, `guided-journal`, `planner`, `workbook` — greyscale default; overridden per project need. `senior-large-print` SHALL use high-contrast black-on-white or white-on-black regardless.

## Digital-PDF editions

- SHALL be full colour (text and images) unless the product family requires black-and-white (coloring-book). Colour carries no marginal cost in digital editions; do not downgrade to greyscale for cost reasons.

## Global page rule (all print bands)

- Whenever a page contains a colour image, treat the WHOLE page as a colour page. Do not place a single colour image on an otherwise-greyscale page and expect mixed colour within one printed page — print colour is applied per page/signature. Group colour content to control cost.

## Image colour test (SHOULD, all print bands)

- An image is coloured only when colour carries meaning. Line diagrams, decorative borders, and puzzle grids MAY be greyscale in print where colour adds nothing.

## Agent responsibilities

- `art-director` — encodes the colour system in the visual bible consistent with this policy and the project's `colour_policy`.
- `illustration-diagram-producer` — briefs and produces assets at the colour level the policy requires; flags any image whose meaning depends on colour so its page is treated as colour.
- `product-designer-layout-engineer` — lays out pages so colour and greyscale content are grouped per the global page rule; keeps `colour_interior` and any print cost assumptions consistent with the policy.

## Consistency requirement

- `production.colour_interior` (boolean) MUST equal whether the print interior is colour under the policy. If a human overrides `colour_policy`, update `colour_interior` to match in the same revision.
