# Marketing & Listing (Offline)

The framework prepares listing and marketing assets offline. It never publishes, changes
a live listing, or spends on advertising.

## Assets it prepares

- Per-channel listing drafts (title, subtitle, description, tags/keywords, categories) via `marketing listing` and the `marketing-asset-fanout` workflow.
- A marketing guide (`marketing guide`) and a listing kit (`marketing kit`).
- Metadata consistency across channels via `metadata-channel-audit`.

## Channel limits

| Channel | Tag/keyword limit |
|---|---|
| Etsy | 13 tags |
| Gumroad | 10 tags |
| KDP | 7 keyword fields |

Canonical metadata is the single source of truth. Channel drafts may not contradict it,
invent difficulty/awards/sales, or imply endorsements without evidence.

## Claims discipline

Every marketing claim must trace to approved, code-verified content. Unverifiable claims
are flagged for a human decision. The listing gate (`/product-approve-listing`) is
human-only and binds to exact metadata hashes.
