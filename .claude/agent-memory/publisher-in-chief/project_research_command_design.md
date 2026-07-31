---
name: project-research-command-design
description: Agreed design for the /research + pipeline + connectivity-manifest feature; plan lives in my-plans/research-pipeline-plan.md
metadata:
  type: project
---

Design agreed 2026-07-31 for two coordinated features. Full plan:
`my-plans/research-pipeline-plan.md`. Also mirrored for the pub-bk repo at
`/Users/qaiser.abbas/Dev/my-repos/pub-bk/my-plans/research-pipeline-plan.md`.

**Why:** web research usually fails here ([[project-web-search-unavailable]]),
and per-product research at `/product-new` time is redundant. Decouple research
into a reusable category-level command that produces a product backlog.

**MEASURED ENVIRONMENT FACTS (2026-07-31, verified by curl in this repo):**
- Bedrock `web_search` tool is blocked, BUT the machine HAS outbound egress
  (example.com → 200; curl + node v26 present, no browser binary preinstalled).
- Plain curl (real UA) gets HTTP 200 full HTML from kdpeasy.com, bookbolt.io,
  bookillustrationai.com, AND `html.duckduckgo.com/html` (a usable SEARCH engine).
- Amazon search returns a 1.4KB captcha stub (bot-blocked); Etsy 403; Google
  Trends 429 — these are hard-blocked to curl.
- Ad-hoc Bash curl to search endpoints is sandbox-gated ("unreviewed network
  writes are prohibited") → network must go through a DECLARED, reviewed module,
  not loose shell.

**Key decisions locked by the user (do not re-litigate):**
- Manual search is the LAST RESORT, not the default. Use a TIERED retrieval
  ladder: Tier0 cache → Tier1 web_search tool (if manifest says available) →
  Tier2 HTTP fetcher (curl/httpx: DuckDuckGo-HTML search + direct GETs of
  200-OK allowlisted sites) [DEFAULT WORKHORSE] → Tier3 headless browser
  (Playwright/Puppeteer via npx — INCLUDE it, but always prefer curl) → Tier4
  manual prompt pack (only for still-blocked high-value sources: Amazon BSR,
  Etsy, Google Trends), minimal queries only.
- Fetcher lives in a QUARANTINED module `publishing_house/net/fetch.py` — the
  SOLE sanctioned network path. Carve it out in rule 18; grant egress in
  settings.json permissions. GET-only, host-allowlisted from research-sources,
  cached, timeouts+backoff, robots.txt respected, NO credentials. Offline core
  (state/generator/verifier) stays network-free.
- Doctor probe is PER-TIER: records the best working tier per source
  (`web_search|http|browser|manual`) in the connectivity manifest so /research
  picks the cheapest working path and never wastes a turn.
- The SKILL orchestrates; the fetcher module is the only network code. CLI stays
  read/validate/scaffold/merge only.
- Connectivity manifest: single `.claude/config/research-connectivity.json`,
  repo-level, **gitignored** (env-specific). Fields: `web_search_available`,
  per-source `best_tier` + `status`, `checked_at`, `checked_under`.
- Probe target list in version-controlled `.claude/config/research-sources.json`.
  Seed: kdpeasy (free tier ok), bookbolt (PAID — see below), amazon/etsy/ddg.
  DROP bookillustrationai from research sources (it is an image-GEN service, not
  a data source).
- Focus research on TRENDING puzzle/book types, categories/subgenres, and
  title/SEO (keyword phrasing, title/subtitle patterns, BISAC/browse nodes,
  trim/size norms). PRICING is DEPRIORITIZED (optional field only).
- Subscriptions (HUMAN-CONFIRMED 2026-07-31): bookbolt = YES (only sanctioned way
  to get Amazon BSR/rank/keyword-volume data curl can't scrape; login-gated).
  bookillustrationai = HOLD/DROP (image gen, not a data source; complicates rule-07
  originality attestation; prefer code/SVG/reportlab art origination + art-direction
  briefs; revisit only after a rights review). Claude CAN do original vector/SVG line
  art + briefs but CANNOT produce rights-clean print-ready RASTER illustration.
  Credentialed bookbolt access = assisted/browser tier with interactive login,
  NEVER credentials in the Python fetcher (rule 17).
- Staleness: manifest trusted until doctor is re-run MANUALLY (no auto-expiry).
- Pipeline is grouped **per puzzle-type/category**, not per product:
  `research/<category>/pipeline.json`, a JSON object keyed by PRODUCT_ID (book
  slug). Each entry carries FULL context (title, audience, product_type, formats,
  trim pref, difficulty, cover style, categories/keywords, positioning, series
  grouping, pricing hypothesis, evidence_refs) so `/product-new <cat> <PRODUCT_ID>`
  needs ZERO further research.
- Craft literals in the pipeline are ADVISORY only; the design-policy engine
  stays authoritative at project init (rule 20). product-new passes only
  human-input points (topic/audience/product-type/formats/title) to `project init`.
- research/ lives at repo ROOT, outside projects/; never touches the 26-state
  machine, gates, freezes, or artifact registry.
- Mode B (web blocked): emit `research/<cat>/queries.md`, a prompt pack capped at
  **≤10 queries per round**, each tagged `[Q<n>-<topic>]`, stating platform +
  exact text + expected answer shape. Human fills answers in-file (file-based, not
  inline). `/research --ingest <file>` analyzes; may append a round-2 query block.
- Target **15–20 product candidates** per category run.
- Pasted content is UNTRUSTED data; human-sourced numbers labeled
  `unverified · human-sourced · <platform> · <date>`; never promoted to verified.

**How to apply:** when implementing, follow the plan's build order (Feature 1 →
verify → Feature 2 → verify). Sequencing is required because /research reads the
connectivity manifest.
