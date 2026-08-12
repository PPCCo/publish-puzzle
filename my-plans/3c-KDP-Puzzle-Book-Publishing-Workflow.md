can you summarise, without missing any important piece of information, the Workflow for Publishing a Puzzle Book on Amazon KDP from https://www.kdpeasy.com/blog/publish-puzzle-book-amazon-kdp but do it so that this can be given to an ClaudeCode AI Agent to make an autonomous Workflow from it

---

This is meaty enough that I built it as a structured markdown spec — easy for a Claude Code agent to parse into discrete tasks/functions.Structured it as a 10-step pipeline with explicit YAML-style parameters, decision tables, hard validation gates, and failure-mode guardrails — designed so a Claude Code agent can map each step to a discrete task/function and knows exactly when to stop-and-retry (e.g., odd page counts, unembedded fonts, mismatched cover spine width, failed proof QC).

Key things preserved from the source:

- The niche-stacking formula (puzzle type + theme + audience) and why generic titles fail
- Full puzzle-type economics table (build time, royalty, audience size)
- Exact page-count math and the even-page/79-page/200-page thresholds
- Full cover and PDF export specs (bleed, DPI, CMYK, embedded fonts, etc.) plus the exact KDP error messages and fixes
- Upload metadata rules (title formula, 7 keyword slots, 2+8 categories, activity-book vs. low-content classification)
- Pricing table and royalty bands
- Proof-copy QC checklist (5 checks)
- 90-day launch plan broken into three phases
- The three worked examples for calibration, and the "common mistakes" list

One thing worth flagging: this source is a vendor content-marketing page (KDPEasy sells a puzzle-generation tool), so the specific dollar figures and sales projections are illustrative/marketing claims rather than verified data — good to build the _process_ around, but I'd treat the revenue numbers as optimistic ballpark rather than guaranteed.

---

# KDP Puzzle Book Publishing — Autonomous Agent Workflow

Source reference: kdpeasy.com "Publish a Puzzle Book on Amazon KDP" (2026 guide). Rewritten as a sequential, decision-driven pipeline suitable for an agent to execute step-by-step, with explicit inputs, outputs, validation rules, and stop/retry conditions.

---

## GLOBAL PARAMETERS (agent should collect/confirm before Step 1)

```yaml
niche:
  puzzle_type: null # word_search | sudoku | maze | crossword | mixed_activity
  theme: null # e.g. "bird watching", "dinosaurs"
  audience: null # e.g. "kids 6-8", "large print seniors"
target_volumes_at_launch: 3 # launch as a series, not a single title
book_classification: "activity_book" # NOT low_content — must contain puzzles + solutions
```

---

## STEP 1 — Niche Selection

**Goal:** produce a 3-layer niche string: `{puzzle_type} + {theme} + {audience}`.

**Rule:** a generic single-word niche (e.g. "Word Search Vol 1") is disqualified — too much competition. A valid niche should map to an estimated 50–800 competing Amazon listings, not tens of thousands.

**Action:**

1. Choose one puzzle type (see Step 2 table for tradeoffs).
2. Choose one specific theme (hobby, fandom, season, profession).
3. Choose one audience/use case (age band, accessibility tier, or use case like travel/gift/dementia-care).
4. Concatenate into a working title stem.
5. (Optional/if tool available) Run keyword/competition research to confirm the niche falls in the "publishable zone."

**Output:** `niche_string`, `working_title_stem`

---

## STEP 2 — Puzzle Type Selection

Decision table (use to pick/validate `puzzle_type`):

| Type           | Build time | Audience size      | Royalty/sale | Beginner difficulty                           |
| -------------- | ---------- | ------------------ | ------------ | --------------------------------------------- |
| Word search    | 3–5 hrs    | Very large (8–90)  | $2.00–$4.50  | Easiest — recommended default for first title |
| Sudoku         | 4–6 hrs    | Large, dedicated   | $2.50–$4.00  | Easy                                          |
| Maze           | 3–6 hrs    | Strong for kids    | $2.40–$4.00  | Easy                                          |
| Crossword      | 30–60 hrs  | Medium, loyal      | $3.00–$5.00  | Hard (all clues original)                     |
| Mixed activity | 5–8 hrs    | Strong gift market | $3.00–$5.50  | Medium                                        |

**Rule:** do not bundle multiple puzzle types or mixed difficulty in one book on a first release — single-type/single-difficulty titles sell ~3x better.

**Default for agent if no strong preference given:** word_search.

---

## STEP 3 — Generate Puzzles + Solutions

**Options (choose one path):**

| Path                                                                                                     | Cost                                                 | Throughput                                           | Notes                                                                       |
| -------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | ---------------------------------------------------- | --------------------------------------------------------------------------- |
| Free generators (QQWing for sudoku, Discovery Puzzle Maker for word search, MazeGenerator.net for mazes) | $0                                                   | Slow — 12–20 hrs manual layout for a 200-puzzle book | Requires manual layout in InDesign/Affinity after generation                |
| Paid all-in-one tool (e.g. KDPEasy)                                                                      | subscription                                         | Fast — 4–6 hrs full book including layout            | Outputs print-ready PDF directly with solutions, page numbers, front matter |
| Commissioned/custom (Fiverr/Upwork)                                                                      | $30–$80/book (grids), $80–$200 (crossword clue sets) | Medium                                               | Best for crossword where clues must be original                             |

**Validation checks after generation (must pass before proceeding):**

- [ ] No duplicate puzzles (spot-check ≥10 random puzzles against full set)
- [ ] Difficulty is consistent throughout (no mixing)
- [ ] Grid size/layout is legible at print size (1 puzzle per page for premium, 2/page max for economy; never 4/page)
- [ ] Solutions verified against puzzles (spot check ≥5)

**Output:** raw puzzle set + verified solutions, ready for interior layout.

---

## STEP 4 — Page Count / Interior Structure

**Target trim size:** 8.5 x 11 in (standard for puzzle books).

**Target total page count:** 80–160 pages.

- Hard floor: 79 pages minimum if spine text is required (KDP cannot print spine text below this).
- Hard ceiling: ~200 pages before print cost erodes margin (unless priced $9.99+).
- Must be an EVEN number (KDP rejects odd-page-count PDFs).
- Absolute KDP limits: min 24 pages, max 828 pages.

**Reference structure (100-puzzle word search example):**

| Section             | Pages   | Notes                             |
| ------------------- | ------- | --------------------------------- |
| Title page          | 1       | Title, subtitle, volume, author   |
| Copyright page      | 1       | Always page 2                     |
| Instructions        | 1       | Mention solutions are at the back |
| Blank/"Let's begin" | 1       | Ensures puzzles start on odd page |
| Puzzles             | 100     | 1 grid per page                   |
| Solutions divider   | 2       | Divider + blank                   |
| Solutions           | 50      | 2 solutions/page, compact         |
| Back matter         | 2       | "Other books in this series"      |
| **Total**           | **158** | Even; spine ≈0.36" on white paper |

**Difficulty-to-count calibration guide:** 200 easy / 100 medium / 50 hard puzzles as rough targets depending on chosen difficulty.

**Critical rule:** solutions ALWAYS go in a single section at the back — never interleaved with puzzles (interleaving causes accidental solution spoilers → bad reviews).

**Output:** finalized page count, interior structure map.

---

## STEP 5 — Cover Design

**Technical spec (must all be satisfied):**

- Single continuous PDF spread: front + spine + back in one file
- 0.125 in bleed on the three outer edges
- CMYK color, ≥300 DPI
- Spine width computed from final page count + paper type (use a spine-width calculator)
- No spine text permitted if page count < 79

**Content/conversion conventions:**

- Title large and legible at ~200px thumbnail width; bold sans-serif, high contrast
- Volume number prominent if part of a series
- One clear theme-matching image/illustration (avoid generic pencil/paper stock imagery)
- "Large Print" badge/ribbon if applicable
- Display puzzle count on cover (e.g. "100 Puzzles") — perceived value signal

**Output:** print-ready cover PDF matching the exact spine width of the finalized interior page count. (If page count changes later, cover MUST be regenerated.)

---

## STEP 6 — Export Print-Ready Interior PDF

**Pre-export checklist (validate all before export):**

- [ ] Format: PDF/X-1a:2001 preferred (PDF 1.4–1.7 acceptable)
- [ ] Resolution: 300 DPI minimum for grids, 600 DPI for fine crossword numbering
- [ ] Color mode: grayscale for interior; CMYK for cover only
- [ ] All fonts embedded (subset embedding OK)
- [ ] No bleed on interior unless using full-page decorative borders
- [ ] Page count even, between 24–828
- [ ] File size < 650 MB
- [ ] No trim/crop marks included
- [ ] All transparency flattened

**Common rejection errors and fixes:**
| Error | Fix |
|---|---|
| "Page count must be even" | Add a blank back page |
| "Interior text not embedded" | Re-export with embed-all-fonts enabled |
| "Cover dimensions do not match interior" | Page count changed after cover was made — regenerate cover with correct spine width |

**Output:** validated interior PDF + validated cover PDF, page counts matched.

---

## STEP 7 — Upload to KDP (kdp.amazon.com)

Flow: sign in → "Create new title" → Paperback → fill metadata.

### 7a. Title/Subtitle

Order fields: primary keyword → audience → format descriptor.
Example patterns:

- "{Theme} {Puzzle Type} for {Audience}: {N} {Difficulty} Puzzles with Solutions, Volume {X}"

### 7b. Description (1,500–2,000 characters, HTML formatted)

Structure: hook for audience → value bullets (puzzle count, print size, themed lists) → use cases (gift/travel/relaxation) → soft CTA.
Avoid: em dashes, all-caps "FREE" claims (may trigger editorial flags).

### 7c. Keywords (exactly 7 slots — fill all)

Rules:

- Use long-tail phrases
- Never repeat a word already in the title (KDP de-dupes automatically, wasting the slot)

### 7d. Categories (2 at upload, up to 8 more via support request post-publish)

Pick the 2 most specific from KDP's Puzzles & Games tree (or Activity Books for kids, or Memory Improvement/Mental Health for senior large-print titles). After going live, email KDP support to request the remaining category additions.

### 7e. Classification flag

Mark as **Activity Book**, not Low Content — required since the book contains solvable puzzles + a solutions section. This unlocks the Humor & Entertainment > Puzzles & Games browse tree; Low Content gets filed under stationery, away from puzzle buyers.

**Output:** live (pending review) KDP listing draft.

---

## STEP 8 — Pricing

**Reference pricing table:**

| Book type                      | Pages | Price  | Print cost | Royalty (60% tier) |
| ------------------------------ | ----- | ------ | ---------- | ------------------ |
| Kids puzzle book 4–8           | 80    | $6.99  | $2.30      | $1.89              |
| Standard adult word search     | 158   | $7.99  | $2.86      | $1.93              |
| Standard sudoku 200pc          | 200   | $8.99  | $3.26      | $2.13              |
| Large print senior word search | 120   | $11.99 | $2.50      | $4.69              |
| Themed mixed activity kids     | 100   | $9.99  | $2.50      | $3.49              |

**General bands:** price floor $5.99; sweet spot $7.99; large print $11.99–$14.99.
**Rule:** below $5.99 royalty drops below acceptable margin and signals low quality; large-print/senior is the highest-royalty segment of the category.

**Output:** confirmed list price per volume.

---

## STEP 9 — Order and QC a Proof Copy

**Action:** in KDP bookshelf → "Request Proof Copy" → Paperback → pay print+shipping (~$7–$15) → wait 5–10 days.

**Mandatory QC checklist on physical proof (all must pass):**

- [ ] Open to a center page — gutter-side letters/grid readable without forcing the book flat
- [ ] Hold a puzzle page to light — no significant bleed-through from the next page
- [ ] Check first/last puzzle pages for print artifacts (toner streaks, faint lines)
- [ ] Spot-check 5 random puzzles against printed solutions — must solve correctly
- [ ] Inspect cover spine — title centered, no CMYK color shift vs. digital preview

**Failure branch:** if any check fails → fix interior/cover → re-upload → order a second proof. Do not proceed to launch until proof passes.

---

## STEP 10 — Launch (First 90 Days)

### Phase A — Week 1 (launch week)

- Do NOT run ads yet — wait for KDP indexing (5–10 days post-approval)
- Publish all 3 launch volumes together (single-volume series reads as a hobby project)
- Set up Amazon Author Central page (bio, photo, series list)
- Email 10–20 personal contacts matching target audience, request honest reviews

### Phase B — Weeks 2–4

- Launch Amazon Ads at $5–$10/day, manual targeting, 10–15 long-tail keywords (expected CPC $0.20–$0.50)
- Run a Goodreads giveaway: 10–25 paperback copies (~$80–$200 print cost) to seed early reviews
- Post in relevant communities (e.g. r/puzzles, niche Facebook groups) — lead with value, not promotion

### Phase C — Weeks 5–12

- Publish 1–2 new volumes/month to stay in "New Releases" and lift older volumes
- Prune ad keywords with CTR < 0.5% after 1,000 impressions; increase bids on top 2–3 converting keywords
- Outreach to 5–10 micro-influencers in-niche with free copies
- Expect ~60–80% of steady-state sales by month 3; curve typically flattens month 4–5

---

## VALIDATION GATES SUMMARY (agent should treat these as hard stop/retry conditions)

1. Niche must not be generic (competition estimate 50–800 listings, not 50,000+).
2. Puzzle set must be duplicate-free and difficulty-consistent.
3. Page count must be even, 24–828 (practically 80–160 for first titles), ≥79 if spine text wanted.
4. Interior/cover PDFs must pass the full export checklist (Step 6) before upload.
5. Cover spine width must exactly match final interior page count — regenerate cover on any page-count change.
6. Physical proof copy must pass all 5 QC checks before any marketing spend.
7. No ad spend until Amazon indexing completes (~5–10 days post-approval).

---

## COMMON FAILURE MODES TO AVOID (agent should actively guard against these)

- Mixing puzzle difficulty/types in a single book (cuts sell-through ~3x)
- Any duplicate puzzle in the set (draws 1-star reviews)
- More than 2 puzzles per page for standard grids (illegible cell size)
- Generic, non-niched titles
- Skipping the physical proof copy
- Running ads before the listing is indexed
- Interleaving solutions with puzzles instead of a single back section

---

## THREE REFERENCE EXAMPLES (for calibration/sanity-checking agent output)

**A. Large-print senior word search:** 100 puzzles, 124 pages, 8.5x11 white paper, $11.99, print cost $2.50, royalty $4.69/sale, ~5 hr build, 200–400 copies/month at steady state.

**B. Kids maze book:** 80 mazes, 100 pages, $7.99, print cost $2.35, royalty $2.44/sale, ~4 hr build, 150–300 copies/month with Q4 gift spikes.

**C. Adult sudoku:** 200 hard puzzles, 256 pages, $8.99, print cost $3.78, royalty $1.62/sale, ~5 hr build, 100–250 copies/month, high repeat-volume purchase rate.
