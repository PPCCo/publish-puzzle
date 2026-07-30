---
paths:
  - "projects/**/outputs/packages/etsy/**"
  - "projects/**/outputs/packages/gumroad/**"
---

# Etsy and Gumroad digital-download packages

- Produce offline listing packages only; the base framework SHALL NOT automate Etsy or Gumroad account login, listing creation, or file upload.
- A package is not live until a human uploads it and records platform evidence.

## Etsy listing package

- Produce: listing title, description, up to 13 tags (Etsy tag limit), category path, price, up to 10 listing images (mockups/previews), instant-download file list, and shipping policy (not applicable for digital).
- Tags MUST total <= 13; do not exceed this limit or the listing will be rejected.
- Listing images SHALL be high-resolution mockups; do not include the raw printable PDF as a listing image.
- The download bundle (PDF files + `bundle_index.json`) is the deliverable asset; record its SHA-256 hash in the package manifest.

## Gumroad listing package

- Produce: product name, description, up to 10 tags (Gumroad tag limit), price, cover image, and the download bundle.
- Tags MUST total <= 10.
- Gumroad content ratings and category fields SHALL reflect the product family and audience band accurately.

## Shared rules

- Recheck current Etsy and Gumroad policy requirements before the `listing` gate; platform policies are time-sensitive.
- All package artifacts carry `external_write_performed: false` and are schema-validated before the `listing` gate.
