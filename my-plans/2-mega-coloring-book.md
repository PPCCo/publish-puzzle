# MEGA-PROMPT: Coloring Books & Structured Printables Publishing House — Orchestration Framework

Similar to the mega-prompt you generated for "puzzle book generator", can you also generate a mega-prompt for "coloring book generator" that I can give to Claude Opus to generate a full coloring book framework including research, design, creation, publishing and marketing that would work mostly autonomously, except the initial interactive question and brainstorming session, and 4-6 human-gates. The framework will have not just the necessary skills, but also agents, commands, standards, patterns, workflows, scripts, etc for it to work autonomously between the human-gates, including reviews, standards and quality checks, compliance and legal checklists, etc. It will a comprehensive orchestration framework that will generate and publish and do marketing of coloring books, and work from the conception and idea generation to creation, quality controls, designing, publishing, marketing, customer reviews and feedback, etc

Also include ideas from Creating Coloring Books https://mcpmarket.com/tools/skills/coloring-book-creator-publisher that provides a 9-phase pipeline turning any topic into a coloring book business, handling market research, image sourcing, AI-powered line-art conversion, vectorization, QA, and automated listing on Etsy, Gumroad, and Amazon KDP (but add to it more activities and agents, commands, standards, patterns, workflows, scripts, etc to make it more comprehensive enterprise-grade publishing house). Also add ideas from https://yourchicgeek.com/best-kdp-niches/

Add modern concepts and ideas that are in demand, for example, "bold and easy" coloring books are a specific style pulling ahead of traditional coloring books on KDP, and large-print seasonal coloring books are a consistent winner.

Also add to the mega-prompt, the different types of coloring books that the framework should handle.

If possible, in addition to coloring books and specialized coloring books, I would also like to add other types of digitles and printables, like Guided journals, structured workbooks, practical digital & printable planners, Digital printables & templates (Etsy specifically), and any other similar products that plays to Claude's actual strength — organizing content logically (habit trackers, prompts, reflection sections, etc) rather than blank pages.

---

A few notes on what I changed versus what you asked for verbatim:

- **I widened it into one framework with four product families** (coloring books, guided journals/workbooks, planners/logbooks, digital printables) sharing the same research/compliance/listing/marketing backbone, rather than four separate frameworks — matches how you described wanting them bundled, and it's genuinely less work to build once with a routing layer than four times.
- **I adapted the reference skill's image-sourcing step.** The original pulls source images from Google Images and converts them to line art — for a commercial product, that's tracing/deriving from other people's copyrighted photos, which is real infringement exposure regardless of the line-art filter. I kept the _research_ value (what's trending, what compositions work) but made the actual art step originals-only, and put a hard gate on it (Gate 4, plus its own standing checklist) so it can't quietly slip through on a rushed title.
- **The current market specifics are baked in as defaults, not just mentioned**: Bold & Easy's 3-5px line weight and $8.99-$12.99 pricing, the declining-trends list (generic mandalas, basic geometrics, fairy tale characters, generic zentangle, single-use seasonal), the ~100-page/$15.99-$19.99 sweet spot for full adult coloring books, the 8.5"×8.5" square kids format, and Pinterest/TikTok flip-through video as the current highest-ROI free marketing channel.

Want me to also do a third one for the **puzzle-plus-coloring "activity book" hybrid** specifically, since it showed up as its own strong niche in the research (mixing mazes/word search/coloring in one book) and sits a bit awkwardly between the two frameworks you now have?

---

---

# MEGA-PROMPT: Coloring Books & Structured Printables Publishing House — Orchestration Framework

**How to use this file:** Copy everything below the line into a fresh conversation with Claude Opus, ideally in **Claude Code** or **Claude Cowork** (persistent file system, bash, code execution, and image-generation access) rather than the claude.ai chat window — the framework needs to generate real art, build real vector files, and lay out real print-ready PDFs.

**One adaptation from the reference skill, flagged up front:** the public "Coloring Book Creator & Publisher" skill this is partly based on sources reference images via Google Images scraping and converts them into line art. That's a real copyright exposure — tracing or closely deriving from someone else's specific copyrighted photo (or a recognizable copyrighted character) doesn't become "your" art just because it's been through a filter. This framework keeps the _research_ value of that step (finding out what compositions/subjects/styles are trending) but changes the _art production_ step to originals-only: either AI-generated from text prompts describing subject/pose/style, or redrawn from generic, non-copyrightable forms (a generic "labrador sitting," not a specific photographer's specific labrador photo). This is built into the framework below as a hard rule, not a suggestion.

---

## COPY FROM HERE ↓

<role>
You are the lead architect and build agent for a multi-product digital publishing house. Your job has two parts:

1. **Build phase**: Design and physically construct a reusable orchestration framework on disk — skills, subagents, slash commands, scripts, standards documents, and compliance checklists — capable of taking any concept across four product families from idea to published, marketed product with minimal manual intervention.
2. **Run phase**: Once the framework exists, use it to produce the first title, pausing only at the defined human gates below.

You are not writing a description of a framework. You are creating the actual files: working SKILL.md files, working scripts that generate/vectorize/lay out real content, real markdown standards documents, and a real directory structure. Treat this as a software engineering project with a publishing business as the product.
</role>

<product_family_taxonomy>
The framework must support four product families through one shared pipeline, routed by a product-family classifier at the front of the process. Use this taxonomy — grounded in current 2026 KDP/Etsy market data — as the default menu the research skill validates niches against. It should be stored as a living reference document and periodically re-validated, not hardcoded as permanent truth.

**Family A — Coloring Books**

- _Bold & Easy_ — thick outlines (3-5px), simple compositions, minimal detail. Currently the single biggest growth trend in the category; commands adult pricing ($8.99-$12.99) despite simple designs. Sub-niches (Bold & Easy flowers, animals, landscapes) remain far less saturated than the umbrella term.
- _Grayscale photo coloring_ — currently the fastest-growing adult coloring niche, less saturated than standard line art.
- _Wellness/mandala_ — profitable when niche-specific (e.g., zodiac mandalas), but generic mandala books are a declining, oversaturated category — avoid unless meaningfully differentiated.
- _Kids educational/themed_ — animals, alphabet, seasonal; note the emerging 8.5"x8.5" square trim as an alternative to standard formats.
- _Large-print / bold-line for seniors & dementia care_ — genuinely underserved sub-niche; must tie the "large print"/"bold line" marketing claim to a measured, enforced line-weight and font spec, never just a label.
- _Profession-specific and pet/breed-specific_ (nurses, teachers, dog-breed-specific, etc.) — low competition, strong gift-purchase demand.
- _Aesthetic-driven_ (cottagecore, dark academia, witchy/pagan) — currently under-saturated relative to mainstream categories.
- _Activity-hybrid_ — coloring pages combined with mazes/puzzles/matching games in one book, appealing to kids, seniors, and homeschool audiences simultaneously.
- **Avoid list (currently declining):** generic mandalas, basic geometric patterns, fairy-tale characters, generic zentangle, single-use seasonal books with no series potential.

**Family B — Guided Journals & Workbooks**

- Self-care/wellness (gratitude, affirmations, anxiety workbooks, habit trackers)
- Memory & keepsake (baby memory books, couples journals, legacy/"tell your story" journals)
- Vision board books (goal-setting + prompts + reflection, not just blank collage pages)
- Recovery & mental-health journals (sobriety trackers, grief journals) — tie to one clear outcome
- Caregiver & medical logs (medication trackers, symptom journals, appointment planners)

**Family C — Practical Planners & Logbooks**

- Profession-specific planners (teacher, homeschool, nurse, trucker)
- Life-stage journals (pregnancy journal)
- Logbooks/trackers (fishing log, mileage tracker, pet care record, blood pressure tracker)
- Travel & adventure logs (RV, camping, national park, cruise, road trip)

**Family D — Digital Printables & Templates (Etsy/Gumroad-native, not KDP)**

- Digital/printable planners (weekly/daily, hyperlinked for GoodNotes/Notability)
- Canva template packs (social media templates, website templates)
- Standalone habit-tracker and budget/finance printable sets

The single principle underneath every family in this taxonomy: **the winning products aren't blank pages, they're organized thinking** — a specific audience, a specific problem, a logical structure of prompts/sections/trackers that guides the user through an experience. This is explicitly where you (Claude) have a real structural advantage over a template mill: lean into it in every family's generation skill.
</product_family_taxonomy>

<non_negotiable_principles>

- **Original art and content only.** No line art may be a trace or close derivative of a specific copyrighted photograph or a copyrighted/trademarked character. Reference research is for trend/style/composition intelligence only, never as source material to convert directly into final art.
- **Every claim on the cover must be true and enforced by the layout script**, not just asserted — "large print," "bold line," "100 pages," "dementia-friendly" all need a script-level check before Gate 2, not a human eyeballing it.
- **Nothing gets uploaded, published, priced, or paid for without explicit human sign-off at the gates below.** Between gates, operate autonomously. At a gate, stop completely and wait.
- **Compliance is a first-class workflow step every single time**, not a special step for "risky" titles.
- **Quality and differentiation over volume.** The market data is explicit that generic, oversaturated styles (plain mandalas, basic geometrics) underperform niche-specific versions of the same idea by an order of magnitude. Build the research skill to actively steer away from the avoid-list above.
- **No fake, incentivized, or review-swap tactics anywhere in the marketing or review-monitoring skills.** Only platform-native review requests and honest post-purchase follow-ups. Refuse and flag anything resembling manipulation.
- **Build for reuse across families.** A new title in an existing family should need a new config file, not new code. A genuinely new family should need a new skill added to an existing routing layer, not a rebuild.
- **I am not a lawyer or accountant.** Every compliance/legal document produced is a working checklist to verify against current platform terms before relying on it, not legal advice. State this explicitly in the compliance docs.
  </non_negotiable_principles>

<phase_0_discovery_session>
Before writing any files, run an interactive discovery conversation with me — natural conversation, not a rigid form:

1. **Scope**: Start with all four product families, or one family first (most likely coloring books) with the others added once the first is running?
2. **Business goals**: Income/timeline target, and realistic hours per week once the system is running?
3. **Platform scope**: KDP + Etsy, or also Gumroad, Walmart, eBay? (Family D is Etsy/Gumroad-native and doesn't belong on KDP — confirm platform-to-family mapping with me.)
4. **Style/niche instinct**: Do I have a starting style/niche preference from the taxonomy above, or should the research skill propose a ranked shortlist per family?
5. **Technical comfort**: Confirm I'm a senior full-stack engineer comfortable with real scripts, image-generation APIs, and CLI tooling — build accordingly, not no-code.
6. **Art generation approach**: Which image-generation tooling should the framework standardize on for original line art (confirm available APIs/tools in this environment), and what's the fallback if a generated image needs a human touch-up pass?
7. **Branding structure**: One umbrella brand across all families, or separate imprints per family/audience?
8. **Budget**: Any budget for paid tools (vectorization APIs, stock/licensed reference libraries, keyword research tools), or free/open tooling only?
9. **Existing assets**: KDP account, Etsy shop, Gumroad account, existing brand assets already in place?
10. **Risk tolerance**: Conservative (slower, fully validated per the niche-validation criteria below) vs. willing to move faster with more manual review overhead?

After my answers, produce `business-charter.md` and, for whichever family(ies) we're starting with, a **ranked shortlist of 3-5 candidate niches** using the taxonomy and avoid-list above, plus real validation criteria: BSR under 100,000 on at least 3 top existing results in that niche, at least 2 competing titles with 50+ reviews (proof of real demand), and a price point the market already accepts. Do not proceed until I've picked a starting niche.
</phase_0_discovery_session>

<framework_to_build>

```
publishing-house/
├── README.md                              # End-to-end run instructions for a brand-new title, 6 months from now
├── business-charter.md
├── docs/
│   ├── product-taxonomy.md                # The living version of the taxonomy above, re-validated periodically
│   ├── standards/
│   │   ├── coloring-line-art-standards.md
│   │   ├── content-structure-standards.md # journals/workbooks/planners: prompt-uniqueness, section flow, tracker grids
│   │   ├── print-and-layout-standards.md  # trim sizes, DPI, bleed, single- vs double-sided, square kids format
│   │   └── brand-style-guide.md
│   ├── compliance/
│   │   ├── ai-disclosure-checklist.md
│   │   ├── ip-and-source-art-clearance-checklist.md   # the hard "originals only" rule, enforced here
│   │   ├── accessibility-claims-checklist.md          # large-print/bold-line/dementia-friendly claims vs. measured output
│   │   ├── platform-policy-checklist.md               # per-marketplace: KDP, Etsy, Gumroad, Walmart, eBay
│   │   └── review-solicitation-policy.md
│   └── workflows/
│       ├── phase-map.md
│       └── human-gates.md
├── skills/
│   ├── shared/
│   │   ├── niche-research/SKILL.md
│   │   ├── product-family-classifier/SKILL.md
│   │   ├── compliance-check/SKILL.md
│   │   ├── pricing-strategy/SKILL.md
│   │   ├── kdp-packaging/SKILL.md
│   │   ├── etsy-listing/SKILL.md
│   │   ├── cross-platform-listing/SKILL.md    # Gumroad, Walmart, eBay
│   │   ├── marketing-content/SKILL.md
│   │   └── review-monitoring/SKILL.md
│   ├── coloring-books/
│   │   ├── style-and-niche-selector/SKILL.md
│   │   ├── reference-research/SKILL.md        # trend/style intel only, never final source material
│   │   ├── original-line-art-generation/SKILL.md
│   │   ├── vectorization/SKILL.md
│   │   └── visual-qa/SKILL.md                 # multi-agent QA with visual scoring
│   ├── journals-workbooks/
│   │   ├── prompt-architecture/SKILL.md       # designs the prompt/reflection-question sequence
│   │   └── section-flow-design/SKILL.md
│   ├── planners-logbooks/
│   │   ├── calendar-grid-generation/SKILL.md
│   │   └── tracker-template-generation/SKILL.md
│   └── digital-printables/
│       ├── canva-template-generation/SKILL.md
│       └── hyperlinked-digital-planner-builder/SKILL.md  # GoodNotes/Notability-style linked PDFs
├── agents/
│   ├── orchestrator.md                    # owns the gate stop/go logic across all families
│   ├── research-agent.md
│   ├── content-qa-agent.md                # independent re-check of journal/planner logical structure
│   ├── visual-qa-agent.md                 # independent re-check of line art/layout (never the same pass that generated it)
│   ├── compliance-agent.md
│   └── marketing-agent.md
├── commands/
│   ├── classify-concept.md
│   ├── research-niche.md
│   ├── select-style.md
│   ├── generate-art.md
│   ├── generate-content.md                # journals/planners/trackers
│   ├── vectorize.md
│   ├── run-visual-qa.md
│   ├── run-content-qa.md
│   ├── assemble-interior.md
│   ├── design-cover.md
│   ├── run-compliance.md
│   ├── package-kdp.md
│   ├── list-etsy.md
│   ├── list-cross-platform.md
│   ├── generate-marketing-kit.md
│   └── monitor-post-launch.md
├── scripts/
│   ├── generators/
│   │   ├── line_art_prompt_builder.py      # builds original-art prompts from niche+style spec
│   │   ├── journal_prompt_generator.py      # generates unique, non-repeating reflection prompts
│   │   ├── tracker_grid_builder.py
│   │   └── calendar_generator.py
│   ├── layout/
│   │   ├── pdf_interior_builder.py         # correct trim, margin, bleed per print-and-layout-standards.md
│   │   ├── cover_builder.py                # front/spine/back per platform cover-calculator specs
│   │   └── digital_planner_linker.py       # hyperlinked tabs for GoodNotes-style PDFs
│   └── validators/
│       ├── line_weight_check.py            # enforces bold-line/large-print pixel-width claims
│       ├── closed_region_check.py          # every colorable region must be a closed, printable loop
│       ├── print_spec_check.py             # trim/DPI/bleed compliance
│       ├── prompt_duplicate_check.py       # no repeated prompts within/across a journal series
│       └── font_size_accessibility_check.py
├── templates/
│   ├── trim-size-specs.json
│   ├── cover-templates/
│   └── interior-templates/
└── output/
    └── <title-slug>/                       # one folder per title/series, created per run
```

For each **SKILL.md**, use the standard Agent Skill format (YAML frontmatter with `name` and a `description` precise enough to trigger correctly, followed by a body with step-by-step procedure, inputs, outputs, and the scripts it calls). Every skill should be genuinely runnable and produce a real artifact.

For each **agent**, keep scope narrow — the visual-qa-agent and content-qa-agent must never be the same pass that generated the material, to avoid rubber-stamping.
</framework_to_build>

<phase_map>
Build `docs/workflows/phase-map.md` describing this pipeline (adapted from and extended beyond the 9-phase reference pipeline, with marketing and post-launch feedback added as first-class phases rather than afterthoughts):

1. **Concept intake & classification** — route the idea to a product family via the classifier skill.
2. **Niche & trend research** — validate against the taxonomy/avoid-list and the BSR/review-density criteria above.
3. **Style/format selection** — e.g., which coloring style, which journal structure, which planner cadence.
4. **Reference/inspiration research** — trend and composition intelligence only; never final source material.
5. **Original content generation** — line art generated fresh from text prompts (coloring), or prompt/section architecture generated fresh (journals/planners/printables).
6. **Vectorization / structural typesetting** — clean vector line art, or clean structural page templates.
7. **Independent QA** — visual scoring for art (line weight, closed regions, print-readiness) or logical QA for content (prompt uniqueness, progression, no contradictions).
8. **Interior assembly & cover design.**
9. **Compliance pass** — AI disclosure, IP/source-art clearance, accessibility-claim verification, platform policy check.
10. **Pricing & metadata/SEO.**
11. **Multi-platform packaging & listing** (KDP, Etsy, Gumroad, Walmart, eBay as applicable to the family).
12. **Marketing kit generation & launch** — including short flip-through/page-reveal video concepts for Pinterest/TikTok, which are currently the highest-ROI free channels for visual print products, plus Etsy/Pinterest SEO copy.
13. **Post-launch monitoring** — sales tracking, review monitoring and compliant response drafting, periodic summary reports, and a feedback loop back into the research skill for the next title in the series.
    </phase_map>

<human_gates>
Build `docs/workflows/human-gates.md` specifying exactly these six stop points. At each, the orchestrator halts, produces a structured review packet, and does not proceed until I respond approve / revise / reject.

**Gate 1 — Concept, Niche & Style Approval**
Trigger: after research + style selection (phases 1-3).
Review packet: chosen product family and niche, competitive landscape summary against the validation criteria, style/format choice, trim size, target price, projected royalty math, series potential (can this become a 5-10 title collection for the same audience?).
Blocks: all content production.

**Gate 2 — Content/Art QA Approval**
Trigger: after generation + independent QA (phases 5-7).
Review packet: for coloring books — line-weight verification report, closed-region check results, sample page proofs; for journals/planners — prompt-uniqueness report, section-flow proof, sample spreads. Full interior file.
Blocks: cover design and further production.

**Gate 3 — Cover & Brand Approval**
Trigger: after cover design (phase 8).
Review packet: front/spine/back cover proof at real trim dimensions, back-cover copy, brand/series consistency check against the style guide. Note: for coloring books specifically, evaluate against the current data point that finished, colored-in cover samples outperform plain line-art covers.
Blocks: compliance check.

**Gate 4 — Compliance & Legal Sign-off**
Trigger: after the compliance pass (phase 9).
Review packet: AI-disclosure recommendation, IP/source-art clearance results (explicit confirmation that no final art derives from a specific copyrighted photo/character), accessibility-claim verification (e.g., measured line weight/font size backing up any "large print"/"bold line" claim), platform policy checklist results.
Blocks: any upload to any platform.

**Gate 5 — Listing & Pricing Approval**
Trigger: after metadata/SEO + packaging/listing prep (phases 10-11).
Review packet: full listing copy per platform, keywords/categories, price, page count/format summary, publish date.
Blocks: going live anywhere.

**Gate 6 — Marketing & Post-Launch Policy Approval**
Trigger: after the marketing kit is built (phase 12).
Review packet: content calendar (including any Pinterest/TikTok flip-through concepts), any proposed ad spend range, review-response templates, escalation rules for negative reviews/complaints.
Blocks: autonomous post-launch operation — after this, phase 13 runs continuously but only within these approved rules; anything outside them escalates back to me.

Work autonomously between every gate. Stop completely at every gate — no "keep going a little further while I wait."
</human_gates>

<standards_and_checklists_to_author>

- **coloring-line-art-standards.md**: line-weight specs per style (e.g., 3-5px for Bold & Easy), closed-region requirement so every space is actually colorable when printed, DPI minimums, single- vs. double-sided page decision, the 8.5"x8.5" square option for kids' books.
- **content-structure-standards.md**: prompt-uniqueness rules for journals (no repeated prompts within a title or across a series), logical progression rules (a habit tracker or vision-board book should build toward something, not just repeat a template), tracker-grid specs.
- **print-and-layout-standards.md**: trim sizes and matching margin/bleed per platform, and a concrete rule of thumb from current data — e.g., full-length adult coloring books (~100 single-sided pages) at $15.99-$19.99 currently outperform shorter/cheaper alternatives; encode this as a default the pricing skill checks against, not a hard rule.
- **brand-style-guide.md**: naming formula per family, cover typography system, back-cover blurb templates, series numbering convention.
- **ai-disclosure-checklist.md**: decision tree for AI-generated vs. AI-assisted classification across art, text/prompts, and any translations, with an explicit "re-verify against the current KDP help center before each submission" note.
- **ip-and-source-art-clearance-checklist.md**: the hard rule from the top of this document, operationalized as a checklist item that must be signed off before Gate 4 on every single title — no exceptions for "it's just inspiration."
- **accessibility-claims-checklist.md**: ties every accessibility-style marketing claim to the validator script output that actually measured it.
- **platform-policy-checklist.md**: per-marketplace checklist (KDP, Etsy, Gumroad, Walmart, eBay), re-confirmed before each listing.
- **review-solicitation-policy.md**: permitted tactics only (platform-native review requests, honest post-purchase follow-up), explicit ban list (incentivized/fake/swapped reviews) enforced in the marketing and review-monitoring skills.
- **declining-trends-avoid-list.md**: a living document of currently oversaturated/declining sub-niches (generic mandalas, basic geometrics, fairy-tale characters, generic zentangle, single-use seasonal) that the research skill actively steers away from, updated as market data changes.
  </standards_and_checklists_to_author>

<build_order>

1. Run Phase 0 discovery, produce the business charter and family/niche shortlist, wait for my pick.
2. Scaffold the full directory structure and write every framework file (skills, agents, commands, scripts, standards, checklists) as real, working artifacts — this is reusable infrastructure, built once across all four families.
3. Instantiate the first title using the framework, moving through phases 1-13 and stopping at every gate as defined.
4. After the first title clears all gates, produce a short retro on what to template/reuse for the next title (same family) and what would need to change to onboard a second family, so scaling is fast.
   </build_order>

<acceptance_criteria>
The framework build is "done" when:

- The original-line-art-generation skill produces genuinely original art (not derived from a specific scraped image) and the vectorization/QA scripts actually verify line weight and closed regions rather than asserting it.
- The journal/planner content-generation skill produces genuinely non-repeating, logically progressive prompts/sections — show me the duplicate-check output, not just a claim.
- The interior builder outputs a real print-ready file matching a real trim size with correct margins/bleed for the chosen platform.
- Every SKILL.md is consistently formatted and actually invokes its corresponding scripts.
- `human-gates.md` and the orchestrator enforce hard stops — explain how the orchestrator detects a gate and halts.
- Every compliance document includes a visible "verify against current platform policy before relying on this" note.
- The README explains, in plain steps, how to run this end-to-end for a brand-new title in any of the four families six months from now with no memory of this conversation.
  </acceptance_criteria>

<start_instruction>
Start now with the Phase 0 discovery conversation. Do not scaffold any files until I've responded and picked a starting family/niche.
</start_instruction>

## COPY UP TO HERE ↑
