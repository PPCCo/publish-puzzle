# Channel Adapters

The framework prepares upload-ready packages for each sales channel. It never performs
a live write. Channel profiles under `.claude/config/platforms/` are documentation and
constraint references; the deterministic packager in `publishing_house/packages.py`
assembles and checksums the package.

## Supported channels

| Channel | Products | Key constraints |
|---|---|---|
| `kdp` | paperback, hardcover | Amazon KDP interior + cover-wrap specs, trim/bleed, up to 7 keyword fields |
| `etsy` | digital-printable | Print-at-home PDF at stated DPI, US Letter / A4, up to 13 tags |
| `gumroad` | digital-printable | Downloadable PDF bundle, up to 10 tags |
| `generic` | any | Portable package for other retailers |

## Adapter contract

Each channel package assembled by `package <id> --channel <channel>` MUST:

1. Include only registered, current-hash artifacts.
2. Respect the channel's tag/keyword limit and required metadata fields.
3. Include the resolved trim, bleed, spine, and page-size for the product format.
4. Emit a package manifest with per-file SHA-256 checksums.
5. Register the package-manifest hash as an artifact.
6. Perform no network call and no credentialed operation.

## Adding a channel

1. Add a profile JSON under `.claude/config/platforms/<channel>.json` describing fields, limits, and file requirements (documentation for reviewers).
2. Extend the packager to assemble the channel's file set and manifest.
3. Extend `metadata-channel-audit` and `marketing-asset-fanout` to cover the channel.
4. Keep live writes disabled. A live connector requires a separately reviewed extension, explicit environment enablement, a valid release authorization, and channel credentials.
