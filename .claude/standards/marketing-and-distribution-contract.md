# STD-MARKETING — Marketing & Distribution Contract

Marketing and distribution artifacts are prepared **after** formats are built
(state at or past `PLATFORM_PACKAGING`) and are **offline guidance only**. The
base framework performs no external write.

## Every marketing artifact SHALL

1. carry `external_write_performed: false`;
2. identify the project, `created_at`, and source artifact hashes where material;
3. validate against its schema before registration;
4. be registered under `projects/<id>/marketing/` at stage `PLATFORM_PACKAGING`.

## Guidance is manual, current, and honest

- Upload steps, ad steps, sizes, durations, and policies are **time-sensitive**;
  each SHALL be re-verified against the platform's **current** official docs with
  a recorded retrieval date before a human acts.
- Local package readiness is distinct from platform acceptance. `packaged`,
  `ready to upload`, `uploaded`, and `published` are distinct states; a guide
  never implies an upload occurred.

## Channels and listings

- Approved channels are: kdp, etsy, gumroad, generic. Channel-specific keyword
  and category mapping is derived from canonical metadata and SHALL not alter it.
- KDP categories, Etsy tags, and Gumroad product descriptions are platform
  derivatives; they are re-checked against current platform rules before submission.

## Tiny-links

- Slugs and UTM parameters are computed deterministically and offline.
- A destination is `known` only when a URL pattern fills from a recorded
  identifier (e.g. ASIN or Etsy listing ID); otherwise it stays `pending-live-listing`.
  Live listing URLs are never invented.
- The framework SHALL NOT call a live URL shortener; `shortener_status` is
  `manual-official-only`. Short links are created by a human through each
  platform's official tool once a live listing exists.

## Creatives

- Ad/organic creatives are **specs and briefs only**; the framework does not
  render final paid assets, post, boost, or spend.
- Creatives SHALL reference only rights-cleared brand assets, provide meaningful
  alt text, and stay within the recorded marketing and colour policies.
- Claims SHALL be supported by the product or recorded evidence. No manufactured
  reviews, undisclosed synthetic testimonials, living-artist imitation, or
  manipulative persuasion — especially for children's and tween audiences.

## Human authority preserved

- Public posting, paid spend, live uploads, and listing changes require a current
  release authorization and are human-only actions outside the base framework.
- Release authorization never grants permission to accept legal terms or exceed
  the stated spend/territory/channel scope.
