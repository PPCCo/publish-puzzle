---
paths:
  - "projects/**/outputs/packages/digital-printable/**"
  - "projects/**/outputs/packages/etsy/**"
  - "projects/**/outputs/packages/gumroad/**"
---

# Digital printables

- Page size SHALL be US Letter (8.5 x 11 in) or A4 (210 x 297 mm); record the target size in `project.yaml`; do not mix page sizes within a bundle unless the product brief explicitly requires it.
- Image resolution SHALL be >= 300 DPI at final print size; verify raster assets before packaging.
- Fonts SHALL be embedded in every exported PDF; do not rely on system font substitution.
- Print-at-home safe margins SHALL be >= 0.25 in (6 mm) on all sides to avoid clipping on consumer printers; bleed is not required for print-at-home products but MAY be added for professional-print variants.
- Every digital-printable bundle SHALL include a `bundle_index.json` listing each file by page range, content description, and SHA-256 hash.
- Etsy and Gumroad delivery is instant-download; the base framework produces the download package only and does NOT automate listing creation or upload.
- Verify the complete bundle renders correctly at the declared page size before advancing past the `interior` gate.
