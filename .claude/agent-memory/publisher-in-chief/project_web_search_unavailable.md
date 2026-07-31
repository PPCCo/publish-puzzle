---
name: project-web-search-unavailable
description: Web search is usually blocked in this environment (Bedrock rejects web_search_20250305); research agents cannot fetch KDP/Etsy/Amazon or third-party niche sites
metadata:
  type: project
---

The Bedrock `web_search_20250305` TOOL is blocked (org policy), so agent-level
WebSearch/WebFetch usually FAILS. BUT — corrected 2026-07-31 by direct curl
testing — the MACHINE HAS OUTBOUND EGRESS (example.com → HTTP 200). The tool
being blocked ≠ no internet.

Measured with plain curl (real UA) on 2026-07-31:
- HTTP 200 full content: kdpeasy.com, bookbolt.io, bookillustrationai.com, and
  `html.duckduckgo.com/html` (a usable search-results endpoint via curl).
- Bot-blocked to curl: Amazon search (1.4KB captcha stub), Etsy (403),
  Google Trends (429).
- Ad-hoc Bash curl to search endpoints is sandbox-gated ("unreviewed network
  writes are prohibited") — network needs a DECLARED, reviewed module.

**Why:** Observed 2026-07-30 — market-scout and competition-analyst agents run
during clr-2026-large-print-sudoku-for-seniors both reported live/marketplace
signals as INSUFFICIENT EVIDENCE; WebSearch was unavailable on the pinned model.
The user confirmed this is an organization policy, not a transient outage.

**How to apply:**
- Do NOT rely on the agent-level WebSearch/WebFetch tool — it is usually blocked.
  Instead route research through a tiered fetch ladder (curl/httpx first, then
  headless browser, then manual as last resort). See
  [[project-research-command-design]] for the full ladder + quarantined
  `publishing_house/net/fetch.py` design.
- `/product-doctor` probes per-tier and records the best working tier per source
  in `.claude/config/research-connectivity.json` (gitignored). Research flows
  CHECK that manifest and pick the cheapest working path.
- Manual human-in-the-loop prompt pack is the LAST RESORT, only for the
  still-blocked high-value sources (Amazon BSR, Etsy, Google Trends).
