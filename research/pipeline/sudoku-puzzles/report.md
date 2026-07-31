# Research Pipeline — Sudoku Puzzles

_Category slug:_ `sudoku-puzzles` · _Generated:_ 2026-07-31 · _Evidence mode:_ `mixed`
_Updated 2026-07-31 with a human `--ingest` round (manual Amazon/Etsy/Gumroad/Trends answers, findings F-016…F-026)._

## Manual ingest round (2026-07-31) — what it confirmed / changed

All pasted answers are recorded as `tier: manual`, `verified: false`, labeled
`unverified · <platform> · 2026-07-31`. Treated strictly as data.

- **Large-print rising confirmed** — Google Trends shows `large print sudoku` rising
  (worldwide + US) while plain `sudoku` is flat [F-024]; the trending-type confidence for
  large-print is raised to **high**. (The specific +45% YoY figure stays unverified.)
- **Head term is crowded and adjacent-captured** — the top Amazon results for `sudoku
  puzzle book for adults` are Murdoku / Murdle / a Highlights kids jumbo book, not pure
  adult sudoku [F-016]. Guidance: differentiate below the head term (difficulty/audience
  long-tail), which the tiered candidates already do.
- **Teen niche upgraded** — dedicated `sudoku for teens` titles exist with BSR ~#20k–#150k
  [F-025]; `teen-13-17-hard` moved **low → medium** confidence (kept, scoped small).
- **Kids framing** — `sudoku for kids` results cluster around ages 6–10 / 7–13 [F-019];
  `kids-6-10-mixed` promoted to priority 2 ahead of `kids-4-8-mini` (priority 3).
- **Variations sized** — ~153 results; best dedicated title ~127 ratings at ~AUD 14.27
  [F-018] — real but modest.
- **Volume pricing** — `1000 sudoku` paperbacks list ~AUD 18.57–23.63 [F-020], confirming
  the higher volume-anchored tier.
- **Printables** — Etsy hides seller tags (inferred only) [F-021]; Digital Download >
  Puzzles/Large Print Puzzle > Sudoku categories [F-022]; bundle sweet spot **300–1000
  puzzles at ~$3.99–$5.99** [F-023].

> All prices above are AUD/USD as pasted, are **unverified vendor/marketplace snapshots**,
> and are **hypotheses only — no live price is committed anywhere**.

## How this was gathered (tiers per source)

All network went through the reviewed fetch path only (`ph_cli.py fetch`). No loose
`curl`/`wget`, no direct `WebSearch`/`WebFetch`.

| Source | Tier reached | Notes |
|---|---|---|
| `ddg` (html.duckduckgo.com) | **Tier 2 (http)** | Search-result listings for variant/kids/large-print titles (existence evidence). |
| `kdpeasy` (www.kdpeasy.com) | **Tier 2 (http)** | Dedicated sudoku niche page + "12 puzzle types ranked" guide — the richest source. |
| `bookbolt` | not used | Manifest `best_tier: assisted`; browser unavailable in this environment. |
| `amazon` | **Tier 4 (manual) — via human ingest** | BSR/price/results pasted by human 2026-07-31 (F-016–F-020, F-025). |
| `etsy` | **Tier 4 (manual) — via human ingest** | Categories + inferred tags pasted 2026-07-31 (F-021, F-022). |
| `gtrends` (Google Trends) | **Tier 4 (manual) — via human ingest** | Trend direction pasted 2026-07-31 (F-024). |

> Guide sites that appeared in DDG results (lowcontentprofits, publishing-expert,
> puzzlegenerator, kdptools) are **not on the fetch allowlist**, so only their result-listing
> titles/snippets were used as weak market-signal evidence — their page bodies were not fetched.
> `web_search` is unavailable in this environment (Bedrock).

## Category overview (evidence-backed)

- **#1 profitable puzzle type on KDP** — universal, language-agnostic, automatable [F-001].
- **Difficulty-tiered series** (Easy/Medium/Hard/Expert as separate books) is the core
  revenue structure; color-coded difficulty makes a collectible set [F-009].
- **Large-print / "Bold and Easy"** is the fastest-growing sub-format (direction from a
  vendor claim; exact +45% YoY figure **unverified**) [F-002].
- **Sudoku Variations** (Killer, Samurai, Jigsaw) is a live differentiated segment [F-003].
- **Kids mini-grid** (4x4 / 6x6 → 9x9) is a live segment across ages 4–12 [F-004].
- **Trim/size norms:** 6x9 and 8.5x11 (8.5x11 for large-print), white 60lb, 100–200 pages [F-007].
- **Volume-anchored** ("1000 Sudoku Puzzles") sustains a higher price band [F-008].
- **Categories:** Amazon browse `Books > Humor & Entertainment > Puzzles & Games > Sudoku`;
  exact BISAC to confirm at listing [F-013].

## Craft guidance that aligns with house rules [F-014]

Marketplace guidance warns against reusing identical generator templates and shipping
difficulty-inconsistent puzzles. The fixes match this repo's constitution directly:
**code-generated puzzles with code-verified unique solution paths**, **labeled difficulty
that matches measured difficulty**, and **back-of-book numbered answer keys**.

## Candidate products (18)

All craft literals below (trim, counts, difficulty) are **advisory only** — the
design-policy engine decides them at `/product-new` init (rule 20). Only `working_title`,
`audience`, `product_type`, and `formats` are authoritative human-input points.

| PRODUCT_ID | Working title | Audience | Type | Formats | Conf. |
|---|---|---|---|---|---|
| `adult-easy` | Easy Sudoku for Adults | adult-general | puzzle-book | paperback, pdf | high |
| `adult-medium` | Medium Sudoku for Adults | adult-general | puzzle-book | paperback, pdf | high |
| `adult-hard` | Hard Sudoku Puzzles for Adults | adult-general | puzzle-book | paperback, pdf | high |
| `adult-expert` | Expert Sudoku | adult-general | puzzle-book | paperback, pdf | medium |
| `senior-large-print-easy` | Large Print Sudoku for Seniors (Easy) | senior-large-print | puzzle-book | paperback | high |
| `senior-large-print-medium` | Large Print Sudoku for Seniors (Medium) | senior-large-print | puzzle-book | paperback | medium |
| `beginners-guided` | Sudoku for Beginners (step-by-step) | adult-general | puzzle-book | paperback, pdf | high |
| `daily-brain-health` | Daily Sudoku (brain health) | adult-general | puzzle-book | paperback, pdf | medium |
| `volume-1000` | 1000 Sudoku Puzzles | adult-general | puzzle-book | paperback | medium |
| `variations-adult` | Sudoku Variations (Killer/Samurai/Jigsaw) | adult-general | puzzle-book | paperback, pdf | medium |
| `killer-sudoku` | Killer Sudoku for Adults | adult-general | puzzle-book | paperback, pdf | low |
| `kids-4-8-mini` | Sudoku for Kids 4-8 (4x4/6x6) | kids-4-8 | puzzle-book | paperback | medium |
| `kids-6-10-mixed` | Sudoku for Kids 6-10 | kids-6-10 | puzzle-book | paperback | medium |
| `tween-8-12-challenge` | Sudoku for Tweens 8-12 | tween-8-12 | puzzle-book | paperback | low |
| `teen-13-17-hard` | Sudoku for Teens | teen-13-17 | puzzle-book | paperback, pdf | low |
| `printable-easy-pack` | Printable Sudoku Pack (Easy) | adult-general | digital-printable | pdf | medium |
| `printable-hard-pack` | Printable Sudoku Pack (Hard) | adult-general | digital-printable | pdf | low |
| `senior-large-print-printable` | Large Print Printable Sudoku for Seniors | senior-large-print | digital-printable | pdf | low |

Suggested first builds by priority: `adult-easy`, `senior-large-print-easy` (priority 1),
then the rest of the adult tier and `beginners-guided`.

## Unverified / manual-tier claims (flagged)

- Dollar figures for publisher earnings, print costs, and price bands ([F-001], [F-008],
  [F-015]) are **vendor estimates**, not primary marketplace data — labeled `unverified`.
- "Bold and Easy +45% YoY" ([F-002]) — direction plausible, **exact figure unverified**.
- BSR sweet spot / High-competition rating ([F-010]) — vendor-reported, not confirmed
  against live Amazon (manual tier blocked).
- Exact BISAC code ([F-013]) — inferred, confirm at listing.
- Pricing is deprioritized per the skill and is a nullable hypothesis only. **No live price
  is committed anywhere.**

## Manual round — COMPLETE

The `queries.md` pack (Amazon/Etsy/Gumroad/Trends) was answered by a human and ingested on
2026-07-31 (findings F-016–F-026). No further manual round is pending. All ingested numbers
remain `unverified` marketplace snapshots. Re-run `--ingest` only if fresher data is pasted.

## Next valid action

`/product-new "sudoku puzzles" <PRODUCT_ID>` (e.g. `adult-easy` or `senior-large-print-easy`).
The design-policy engine will derive all craft parameters at init.
