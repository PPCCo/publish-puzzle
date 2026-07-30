---
paths:
  - "projects/**/accessibility/**"
---

# Accessibility

- Record both automated and manual checks.
- Print and digital-PDF products require: sufficient colour contrast (WCAG AA minimum for text), legible font sizes per audience band, and meaningful alt text for all non-decorative images.
- `senior-large-print` audience band SHALL use high-contrast black-on-white (or white-on-black) interiors; minimum body type 18 pt; puzzle cells sized for low-vision use.
- Digital-printable PDFs require logical reading order, language metadata, and accessible tag structure where tooling supports it.
- A tool warning MAY be a false positive; document the resolution. A missing tool check is `not-run`, never `pass`.
