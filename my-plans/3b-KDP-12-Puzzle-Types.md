Can you create a document with the 12 KDP Puzzle Book Types mentioned in https://www.kdpeasy.com/blog/best-puzzle-book-types-kdp along with any specific agents, commands, standards, patterns, workflows, scripts, etc that the Publishing-House-Claude-Framework should consider and cover in the framework specific to these Puzzle Book Types

---

A few things worth flagging about how this extends the original framework:

- **Crossword and Picture Puzzles are the two types that actually need something beyond "generator + validator."** Automated crossword clues are genuinely weak per the current data, so I added a dedicated clue-quality-agent rather than pretending grid-fill correctness is enough. Picture puzzles need two near-identical copies of a specific image, which makes them the highest source-art risk in the whole set — I routed that one through the IP checklist with no exceptions, not just a general "use good judgment" note.
- **Cryptograms got their own quote-clearance-agent** — a themed cryptogram book is only as legally clean as its quote sourcing, and that's easy to wave through as "just text" if it's not called out separately from image-based IP concerns.
- **"Bold and Easy" isn't one spec** — it means something different for a sudoku grid than a maze path than a word search font size, so I built it as a per-type parameter table rather than a single global "large print" flag, otherwise the validator would happily pass a bold-and-easy label on a book that doesn't actually meet the standard for its type.
- **Fill-In and Jumbles are built but deliberately not recommended** — the data on both is weak enough that I had the roadmap route them to "bonus content inside other books" rather than standalone titles, and said so explicitly so a future instance of this framework doesn't default to building them as first titles.

Want me to do the same kind of extension pass for the **coloring book styles** (the equivalent per-style breakdown — Bold & Easy line-art specs vs. grayscale photo-coloring pipeline vs. mandala-progressive-complexity — the way this document did for puzzle types), so both frameworks have matching depth?

---

# The 12 KDP Puzzle Book Types — Framework Extension for the Publishing-House-Claude-Framework

This document extends the puzzle-book orchestration framework (`puzzle-empire/`) built earlier so it can competently handle all 12 recognized KDP puzzle categories, not just sudoku/word search/crossword/maze. For each type it specifies: market data, the generator + validator scripts needed, any special agent behavior required, and standards/compliance notes specific to that type. Section 7 shows exactly how this plugs into the existing directory structure.

---

## 1. The 12 Types — Reference Table

| #   | Type                                                 | Competition                                       | Profit Potential | Creation Difficulty                              | Typical Price | Repeat Purchase              |
| --- | ---------------------------------------------------- | ------------------------------------------------- | ---------------- | ------------------------------------------------ | ------------- | ---------------------------- |
| 1   | **Sudoku**                                           | Medium (10,000+ books, but demand absorbs supply) | Very High        | Easy — fully automatable                         | $8–$12        | Excellent (3–10 books/yr)    |
| 2   | **Word Search**                                      | High (30,000+ books)                              | High             | Easy–Medium (needs theme research)               | $6–$10        | Good (2–5 books/yr)          |
| 3   | **Crossword**                                        | Very High, dominated by established publishers    | Medium           | Hard — automated clue generation is poor quality | $7–$10        | Excellent                    |
| 4   | **Mazes**                                            | Low–Medium                                        | High             | Easy                                             | $6–$9         | Medium                       |
| 5   | Logic Puzzles / Brain Teasers (incl. Kakuro, KenKen) | Low                                               | Very High        | Medium–Hard                                      | $9–$14        | Good                         |
| 6   | **Coloring Books**                                   | Very High overall, but niches remain open         | Medium–High      | Medium (needs art)                               | $6–$12        | Medium                       |
| 7   | **Dot-to-Dot**                                       | Medium                                            | Medium           | Easy–Medium                                      | $5–$8         | Low–Medium                   |
| 8   | **Cryptograms**                                      | Low                                               | Medium           | Easy                                             | $6–$9         | Very Good                    |
| 9   | **Picture Puzzles / Spot-the-Difference**            | Medium                                            | Medium           | Medium–Hard                                      | $6–$10        | Medium                       |
| 10  | **Fill-In Puzzles**                                  | Low                                               | Low–Medium       | Hard                                             | —             | Small, dedicated             |
| 11  | **Jumbles / Anagrams**                               | Low                                               | Low              | Easy                                             | —             | Niche; best as bonus content |
| 12  | **Number Search**                                    | Very Low (hidden gem)                             | Medium–High      | Easy                                             | $6–$10        | —                            |

**Market context to encode as defaults:** the puzzle book category exceeds $450M annually on Amazon with sustained double-digit year-over-year growth, and pricing at $9.99+ unlocks KDP's 60% royalty tier — the pricing-strategy skill should treat $9.99 as a floor to test against, not just a suggestion. The **"Bold and Easy"** large-print format is the single fastest-growing cross-category trend (roughly +45% YoY), commanding a $1–$3 premium over standard formats, and it doesn't apply equally well to every type (see Section 3).

**Declining, for the avoid-list:** generic newspaper-style crosswords and simple, undifferentiated kids' activity books are both trending down — the research skill should flag these rather than default to them.

---

## 2. Per-Type Framework Specs

Each entry below is what needs to exist in `scripts/generators/`, `scripts/validators/`, and any special agent/skill behavior, on top of what the base framework already has.

### Sudoku

- **Generator**: `sudoku_gen.py` — must generate a solved grid, remove cells according to a target difficulty band, and confirm the resulting puzzle still has exactly one solution (uniqueness is not optional — this is the whole value proposition of the category).
- **Validator**: `sudoku_uniqueness_check.py` — independently re-solves every puzzle in the manuscript and rejects any with 0 or 2+ solutions before Gate 2.
- **No special agent needed.** This is the most fully automatable type in the catalog — flag it in the research skill as the default "beginner / fast series-building" recommendation.
- **Bold and Easy variant**: extra-large 9×9 grids, 20–24pt numbers, one puzzle per page — a distinct layout template, not just a font-size setting on the standard template.

### Word Search

- **Generator**: `wordsearch_gen.py` — word-fit algorithm (8-directional placement, overlap resolution), themed word-list intake.
- **Validator**: `wordsearch_solvability_check.py` — confirms every listed word is actually present and findable in the final grid (a word can get silently clipped during placement-algorithm edge cases; check for this explicitly).
- **Theme-sourcing step**: word lists need a "theme research" input (dog breeds, Bible verses, travel terms, etc.) — this is where niche differentiation actually happens, so the niche-research skill should hand off a vetted word list, not just a topic name.
- **Bold and Easy variant**: 14–18pt letters, 12×12 or 15×15 grids (down from a standard 20×20), one puzzle per page. This is currently the strongest-performing Bold and Easy sub-format — treat it as a first-class template, not an afterthought.

### Crossword

- **Generator**: `crossword_gen.py` — grid-fill algorithm plus clue generation.
- **The one type in this framework that genuinely needs a human-in-the-loop or specialist step**: automated clue generation tends to produce weak, ambiguous, or repetitive clues. Add a dedicated **clue-quality-agent** whose only job is to score every generated clue against a rubric (ambiguity, redundancy with other clues, appropriate difficulty) and flag the weak ones for either regeneration or manual rewrite — do not let a crossword pass QA on grid-fill correctness alone.
- **Validator**: `crossword_grid_check.py` (structural — symmetry, black-square ratio, no orphaned cells) plus the clue-quality-agent's report.
- **Recommendation to encode in the research skill**: flag crossword as an "advanced publisher" type (15–30 hours creation time) rather than a starting point, and route new users toward sudoku/word search first.

### Mazes

- **Generator**: `maze_gen.py` — standard maze algorithms (recursive backtracker, Prim's, etc.) plus theming (dinosaur/vehicle/holiday shapes as maze borders).
- **Validator**: `maze_solvability_check.py` — path-finding confirmation from start to finish, plus a "single reasonable path vs. absurd complexity for the target age" check.
- **Bold and Easy variant**: wide paths (0.5"+), fewer dead ends, clear start/finish markers — a kids/seniors crossover format.
- **Composability note**: mazes pair very well with coloring (maze border becomes a colorable illustration) — the orchestrator should support a "maze + coloring" hybrid page type shared with the coloring-book skill set.

### Logic Puzzles / Brain Teasers (Kakuro, KenKen, lateral thinking, number sequences)

- **Generator**: `logic_puzzle_gen.py` — this needs per-subtype generation logic (Kakuro and KenKen are structurally different from pattern-recognition or lateral-thinking puzzles), so build this as a family of generators behind one skill rather than a single script.
- **Validator**: subtype-specific solvers, same uniqueness-of-solution principle as sudoku.
- **Positioning note**: this is the highest price-ceiling category ($9–$14) with the lowest competition — worth a dedicated "premium tier" pricing template, and worth flagging to the research skill as the natural next step after a publisher has 5–10 titles established, not a starting point (medium–hard creation difficulty).

### Coloring Books

- **This type shares infrastructure with the separate coloring-book framework already built** (`skills/coloring-books/` in the publishing-house structure) — don't duplicate it here. The puzzle-empire orchestrator should call that skill set directly when a title or hybrid page needs coloring content, and inherit its "originals only, no scraped source art" rule without exception.
- **Puzzle-specific niches to flag in research**: profitable sub-niches skew toward specific themes (specific animals/breeds, occupation-based) and away from generic "adult coloring book" listings, consistent with the standalone coloring framework's avoid-list.

### Dot-to-Dot

- **Generator**: `dot_to_dot_gen.py` — takes a target silhouette/shape and produces a numbered dot sequence around its outline at a controllable density (fewer dots = easier/younger audience).
- **Validator**: `dot_to_dot_clarity_check.py` — confirms the connected sequence actually resolves into a recognizable image at the target dot density (a sparse dot count can produce an ambiguous blob rather than the intended shape).
- **Composability note**: pairs naturally with coloring (dot-to-dot reveal, then color the result) — build as a shared hybrid page type, same as the maze+coloring pairing above.
- **Source-art rule applies here too**: the target silhouette must be an original or public-domain/generic shape, not traced from a specific copyrighted illustration.

### Cryptograms

- **Generator**: `cryptogram_gen.py` — substitution-cipher encoder for a supplied quote/text bank.
- **Content-sourcing agent requirement**: add a **quote-clearance-agent** to the compliance pass specifically for this type. Quotes are only usable if they are public domain, properly attributed, or original — a themed cryptogram book built on copyrighted or ambiguously-sourced quotes is a real IP exposure, and this needs its own checklist item (`docs/compliance/quote-clearance-checklist.md`), not a generic "IP check" wave-through.
- **Validator**: `cryptogram_decode_check.py` — confirms the cipher is solvable and the answer key matches.
- **Positioning note**: low competition, very good repeat-purchase rate — a strong candidate for a themed series (e.g., a specific historical figure's public-domain quotes) once the quote-sourcing pipeline is solid.

### Picture Puzzles / Spot-the-Difference

- **Generator**: this is the one type that requires an actual image-editing pipeline, not a text/grid algorithm — `picture_puzzle_gen.py` takes an original base image and produces a modified duplicate with a controlled number of deliberate differences (color shifts, object removal/addition, size changes).
- **Validator**: `picture_puzzle_diff_check.py` — a programmatic image-diff that confirms exactly the intended number of differences exist and are neither too subtle to find nor so obvious they trivialize the puzzle.
- **Hard IP dependency**: the base image absolutely must be original (AI-generated from a text prompt) or properly licensed — this type has the highest source-art risk of the twelve, because the whole mechanic requires two near-identical copies of a specific image, which makes "just used it for inspiration" not a viable defense if the base image wasn't cleared. Route every title through the ip-and-source-art-clearance-checklist with no exceptions.
- **Audience note**: kids' versions currently outperform adult versions — weight the research skill's recommendations accordingly.

### Fill-In Puzzles

- **Generator**: `fillin_gen.py` — grid-fill from a supplied word bank (structurally related to crossword generation, without needing clues).
- **Validator**: same grid-structure check as crossword, minus the clue-quality-agent (no clues to score).
- **Portfolio note**: research flags this as low profit potential and not recommended as a beginner or even a mid-catalog choice — build the skill for completeness, but the research/orchestrator skill should not surface it as a default recommendation.

### Jumbles / Anagrams

- **Generator**: `jumble_gen.py` — letter-scramble generator from a word/phrase bank, with an optional reveal-phrase mechanic (scrambled letters spell a bonus answer).
- **Validator**: `jumble_uniqueness_check.py` — confirms the scramble doesn't accidentally spell a second valid word that would make the puzzle ambiguous.
- **Recommended usage pattern**: build this primarily as **bonus content** the assembly skill can append to a word search or mixed puzzle book, not as a standalone product — this matches the market data showing weak standalone demand but genuine value as filler/bonus pages.

### Number Search

- **Generator**: `numbersearch_gen.py` — same underlying algorithm as `wordsearch_gen.py`, parameterized for numeric strings (phone numbers, dates, sequences) instead of words.
- **Validator**: reuse `wordsearch_solvability_check.py` with a numeric-token mode rather than building a parallel script.
- **Positioning note**: flagged in the research data as a genuine "hidden gem" — very low competition, medium-high profit. Worth the research skill actively surfacing this as a first-mover opportunity to me rather than waiting for me to ask about it.

---

## 3. The "Bold and Easy" Standard — Applies Differently Per Type

Build `docs/standards/bold-and-easy-specs.md` as a per-type parameter table rather than one global rule, since "large print" means something structurally different for a grid puzzle than for a maze:

| Type                    | Font/number size                      | Grid/path spec                            | Layout rule                                                                                                  |
| ----------------------- | ------------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Word Search             | 14–18pt letters                       | 12×12 or 15×15 (down from standard 20×20) | One puzzle per page, mandatory                                                                               |
| Sudoku                  | 20–24pt numbers                       | Extra-large 9×9                           | One puzzle per page                                                                                          |
| Mazes                   | —                                     | Paths 0.5"+ wide, fewer dead ends         | Clear start/finish markers                                                                                   |
| Number Search           | Large-format numerals                 | Reduced grid density                      | One puzzle per page                                                                                          |
| General body/title text | 16pt+ body, 14pt minimum grid content | 2–3pt grid lines, 4pt+ borders            | Generous white space; "Bold and Easy" and "Large Print" both included in title/subtitle for keyword coverage |

The `print_spec_check.py` validator (already in the base framework) needs a per-type parameter set, not a single global font-size threshold, or it will pass a technically-large-print sudoku book that's actually a normal-print word search book.

---

## 4. Mixed / Hybrid Puzzle Books

Add explicit support for combined-type titles, since these are a distinct product with their own tradeoffs (broader audience and higher price ceiling, but lower repeat-purchase rate and harder series-building):

- **New command**: `/build-mixed-book` — takes a list of puzzle types + a target trim size and calls each relevant generator, then hands off to a shared assembly pass.
- **New agent responsibility for the orchestrator**: when assembling a mixed book, enforce a **balance check** (no single puzzle type should dominate the page count unless the concept explicitly calls for it) and a **difficulty-progression check** across the whole book, not just within each puzzle type section.
- **Recommended combinations to encode as starting templates** (from current market data): travel puzzles (word search + sudoku + mazes, 6"×9" trim), senior brain games (large-print word search + easy sudoku + crosswords), kids mega book (mazes + dot-to-dot + word search + coloring), logic challenge (sudoku + KenKen + logic puzzles + cryptograms).
- **Pricing note**: mixed books justify $9–$14 pricing and perform well as gift-market "all-in-one" purchases — the pricing-strategy skill should treat "mixed" as its own pricing tier, not average the component types' price ranges.

---

## 5. New/Updated Agents Beyond the Base Framework

| Agent                     | Trigger                   | Responsibility                                                                                          |
| ------------------------- | ------------------------- | ------------------------------------------------------------------------------------------------------- |
| **clue-quality-agent**    | Crossword generation      | Independently scores every clue for ambiguity/redundancy/difficulty-fit; blocks weak clues from Gate 2  |
| **quote-clearance-agent** | Cryptogram generation     | Confirms every source quote is public domain, properly licensed, or original; feeds the compliance pass |
| **image-diff-agent**      | Picture puzzle generation | Confirms the intended number of differences exist at an appropriate difficulty level                    |
| **hybrid-balance-agent**  | Mixed book assembly       | Confirms page-count balance and difficulty progression across a multi-type title                        |

These sit alongside (not instead of) the existing `visual-qa-agent` and `content-qa-agent` from the base framework — they're type-specific specialists the orchestrator invokes conditionally based on which puzzle type(s) a title contains.

---

## 6. New/Updated Commands

Extend the base framework's command set with:

- `/generate-sudoku`, `/generate-wordsearch`, `/generate-crossword`, `/generate-maze`, `/generate-logic-puzzle`, `/generate-dot-to-dot`, `/generate-cryptogram`, `/generate-picture-puzzle`, `/generate-fillin`, `/generate-jumble`, `/generate-numbersearch` — one thin command per type, each calling its generator + matching validator in sequence and refusing to report "done" until the validator passes.
- `/build-mixed-book` (Section 4).
- `/apply-bold-and-easy` — takes an existing standard-format manuscript and re-renders it against the per-type Bold and Easy spec table in Section 3, rather than requiring a from-scratch regeneration.
- `/run-clue-quality-check`, `/run-quote-clearance`, `/run-image-diff-check` — standalone invocations of the three new specialist agents above, so they can be re-run independently during revision cycles without repeating the full pipeline.

---

## 7. Where This Plugs Into the Existing Directory Structure

```
puzzle-empire/
├── docs/
│   ├── standards/
│   │   ├── bold-and-easy-specs.md          # NEW — per-type table, Section 3
│   │   └── mixed-book-composition-standards.md   # NEW — Section 4
│   └── compliance/
│       └── quote-clearance-checklist.md    # NEW — cryptogram-specific, Section 2
├── agents/
│   ├── clue-quality-agent.md               # NEW
│   ├── quote-clearance-agent.md            # NEW
│   ├── image-diff-agent.md                 # NEW
│   └── hybrid-balance-agent.md             # NEW
├── commands/
│   ├── generate-{sudoku,wordsearch,crossword,maze,logic-puzzle,
│   │   dot-to-dot,cryptogram,picture-puzzle,fillin,jumble,numbersearch}.md   # NEW (11 files)
│   ├── build-mixed-book.md                 # NEW
│   ├── apply-bold-and-easy.md              # NEW
│   └── run-{clue-quality-check,quote-clearance,image-diff-check}.md          # NEW (3 files)
└── scripts/
    ├── generators/
    │   ├── sudoku_gen.py                   # already specified in base framework
    │   ├── wordsearch_gen.py               # already specified
    │   ├── crossword_gen.py                # already specified
    │   ├── maze_gen.py                     # already specified
    │   ├── logic_puzzle_gen.py             # NEW (family: kakuro/kenken/lateral-thinking)
    │   ├── dot_to_dot_gen.py                # NEW
    │   ├── cryptogram_gen.py                # NEW
    │   ├── picture_puzzle_gen.py            # NEW
    │   ├── fillin_gen.py                    # NEW
    │   ├── jumble_gen.py                    # NEW
    │   └── numbersearch_gen.py              # NEW (parameterizes wordsearch_gen.py)
    └── validators/
        ├── sudoku_uniqueness_check.py       # already specified
        ├── wordsearch_solvability_check.py  # already specified (extended for numeric mode)
        ├── crossword_grid_check.py          # already specified
        ├── maze_solvability_check.py        # already specified
        ├── dot_to_dot_clarity_check.py       # NEW
        ├── cryptogram_decode_check.py        # NEW
        ├── picture_puzzle_diff_check.py      # NEW
        └── jumble_uniqueness_check.py         # NEW
```

Coloring-book generation is deliberately not duplicated here — it's a call-out to the separate coloring-book skill set, invoked whenever a title (standalone or hybrid) needs colorable content.

---

## 8. Catalog Roadmap (What to Actually Build First)

Encode this sequencing logic into the research/orchestrator skill's default recommendation, based on current profitability-vs-effort data:

1. **Start**: Sudoku and/or Bold and Easy Word Search — both fully automatable, weekend-buildable, strong margins.
2. **Next**: themed Word Search series (2–3 specific themes) and Mazes for kids — low-medium competition, moderate effort.
3. **Then**: Number Search and Cryptograms — genuinely underserved niches, low effort, worth a first-mover push once the core pipeline is proven.
4. **Later (once the clue-quality-agent and picture-puzzle pipeline are mature)**: Crossword, Logic Puzzles (Kakuro/KenKen), Picture Puzzles — higher effort and/or higher IP-diligence categories, but the strongest margins in the catalog.
5. **Ongoing**: Fill-In and Jumbles as bonus/filler content inside other titles rather than standalone products, per the market data showing weak standalone demand for both.
6. **Portfolio move once 5–10 single-type titles exist**: layer in Mixed/Hybrid books across established types to capture the gift-market/variety-seeker segment without cannibalizing the specialist series.

This roadmap should live in `docs/workflows/catalog-roadmap.md` and feed directly into what the research skill proposes at Gate 1 for each new title.
