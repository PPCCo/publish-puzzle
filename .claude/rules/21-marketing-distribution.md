---
paths:
  - "projects/**/marketing/**"
  - ".claude/config/marketing/**"
---

# Marketing and distribution toolkit

Applies to the post-production marketing toolkit (`marketing guide`,
`marketing tiny-links`, `marketing ad-creatives`, `marketing kit`) and its config.

- Marketing runs only after formats are built (state at/after `PLATFORM_PACKAGING`).
- Every marketing artifact carries `external_write_performed: false`, is
  schema-validated, and is registered under `projects/<id>/marketing/`.
- Upload steps, ad-creation steps, sizes, and policies are time-sensitive:
  re-verify against current official platform docs with a recorded date before
  acting. Local package readiness is not platform acceptance.
- Tiny-links are deterministic and offline. Never call a live shortener; never
  invent a live listing URL. Destinations stay `pending-live-listing` until an
  identifier resolves the pattern; short links are created manually through each
  platform's official tool.
- Ad/organic creatives are specs and briefs only — no final asset is rendered,
  posted, boosted, or paid for. Briefs reference only rights-cleared assets,
  include alt text, and follow the marketing and colour policies.
- Claims must be supported by the product or recorded evidence. No manufactured
  reviews, undisclosed synthetic testimonials, living-artist imitation, or
  manipulative persuasion targeting children (see rule 06 for child/tween audiences,
  rule 14 for marketing conduct).
- Public posting, paid spend, live uploads, and listing changes are human-only,
  require a current release authorization, and never authorize accepting legal
  terms or exceeding the approved spend/territory/channel scope.
