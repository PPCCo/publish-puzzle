# `/hi` Router Plan — natural-language front door to the publishing house

Status: PLAN (no router code yet). Its dependency — the series-implementation-plan
— is **implemented** (staged): `series recommend`, `series suggest-from-research`,
`catalog verify`/`rebuild`, catalog schemas v1.1 with product↔series cross-links,
`project plan.series_next`, and the `product-series-add-book` skill all exist and
run. The router can therefore be built in a single pass (all intents at once).
Author: Framework design pass, 2026-08-12
Depends on: `series-implementation-plan.md` §4.4 (series-aware planner/status)
and §4.6 (catalog schemas + cross-links) — both landed.

## 1. Goal

A single conversational entry point — `/hi [natural language]` — that reads the
deterministic state of the repo and **routes** the human to the right existing
command/skill/agent, with a clean AskUserQuestion flow and the exact next
commands to run. It is **read-only and routing-only**: it never transitions
state, approves a gate, freezes, generates, deletes, or writes externally. Those
actions stay behind their existing safety-carrying skills; `/hi` only *hands off*
to them.

## 2. Core design principles

1. **The CLI is the source of truth, not the catalog.** `project list` /
   `project status` / `project plan` reflect live `state.json`; `catalog/*.json`
   can be stale (observed: catalog said `DISCOVERY` while state was
   `RELEASE_AUTHORIZATION`). The router always reads the CLI for state and only
   uses the catalogs for cheap cross-project/series membership lookups (after the
   series plan §4.6 makes them schema-valid + cross-linked).
2. **Do not re-derive workflow logic.** `project plan <id>` already returns
   `recommended_action`, `human_gate_command`, `recommended_skills/agents/
   workflows`, `blockers`, and `all_forward_options`. The router surfaces those
   verbatim; it never reinvents the 26-state lifecycle.
3. **Route, never perform.** Every actionable suggestion is a command string the
   human runs (or confirms), especially the human-only gates (compliance,
   release), delete, freeze, and any external write. Governance rules 00/01/02/11.
4. **Cheap by construction.** The router runs on **Haiku 4.5** for parsing +
   light single-project answers; it escalates to **Sonnet 5** only for multi-
   project aggregation or ambiguous NL intent. **Never Opus.** Heavy parallel
   per-project reads fan out to Haiku subagents.
5. **AskUserQuestion is the primary UX.** Whenever there is a choice — which
   project, which view, which next command — present 2–4 options with a
   **Recommended** first option, rather than dumping everything.

## 3. Files to create / change

- **New command** `.claude/commands/hi.md` — the router. Frontmatter:
  `description`, `argument-hint: "[natural language | project-id | verb ...]"`,
  `model: '@bedrock-eus1/us.anthropic.claude-haiku-4-5-20251001-v1:0'`,
  `allowed-tools:` Read, Grep, Glob, Bash (scoped to `ph_cli.py *`),
  AskUserQuestion, Task/Agent (to fan out Haiku sub-readers). It contains the
  intent taxonomy, the dispatch table, and the AskUserQuestion templates below.
- **Optional light subagent** `.claude/agents/status-reader.md` (Haiku, tools:
  Read/Grep/Glob/Bash-cli-only) — a bounded "read one project/series and return
  a compact status JSON" worker the router fans out when several projects must be
  summarized in parallel. Keeps the router's own context small. Only add if the
  inline single-command approach (chosen) needs parallel reads; start without it
  and add if the catalog grows.
- **No core Python changes** in this plan — the router composes existing CLI
  output. (The series plan owns any CLI additions it needs.)

## 4. Intent taxonomy (how ARGUMENTS map to routes)

The router classifies `$ARGUMENTS` into exactly one primary intent. Order of
resolution (first match wins), all matching is deterministic-first
(id/keyword) before falling back to NL classification:

| # | Trigger shape | Intent | Primary data call(s) |
|---|---|---|---|
| 0 | *(empty)* | GREET + orient | `project list`, `series list` |
| 1 | looks like a project id (`clr-YYYY-…`) | PROJECT focus | `project status <id>`, `project plan <id>` |
| 2 | looks like a series id (`series-…`) | SERIES focus | `series status <id>` (+ `series recommend`) |
| 3 | leading verb `delete …` | ROUTE-TO-DELETE | `project status <id>` then hand to `/delete-project` |
| 4 | leading verb `research …` | RESEARCH | `research show <cat>` / route to `/research` |
| 5 | leading verb `pipeline …` | PIPELINE | `research show <cat>` (backlog view) |
| 6 | `next` / `whats next` / `next commands` | NEXT-ACTION | `project plan` for in-progress projects |
| 7 | a product-type / puzzle-type word (`puzzle`, `sudoku`, `coloring`, `journal`, …) | TYPE aggregate | scan matching projects → counts |
| 8 | `series <word>` (topic, not id) | SERIES search | scan `series.json` titles/premise |
| 9 | anything else (free NL) | NL classify | Sonnet 5 classifies into one of the above, else asks |

**Verb + object grammar:** the router understands `<verb> [object] [status]`
where verb ∈ {status, next, research, pipeline, delete, series} and object is a
project-id, series-id, product-type, or topic. `status` is the implied verb.
Examples map as:
- `/hi puzzles status`, `/hi puzzle`, `/hi sudoku` → intent 7 (TYPE aggregate).
- `/hi series status`, `/hi series animal` → intents 2/8 (SERIES).
- `/hi next commands`, `/hi whats next` → intent 6.
- `/hi research/coloring-book`, `/hi do research on Sudoku for couples` → intent 4.
- `/hi what project should I pick up next according to findings on Sudoku` →
  intent 9 → resolves to RESEARCH backlog ranked view for the `sudoku` category.

## 5. Response contract per intent

Every response is **concise**: a 1–2 line headline, a compact status block, then
an AskUserQuestion (when a choice exists) with a Recommended option, and the
exact command(s) to run. No walls of text.

### 5.0 GREET (`/hi`)
- Headline: repo one-liner (N projects, M active, K series).
- If ≥1 in-progress product: AskUserQuestion "Where do you want to start?" with
  options: **Resume the active product (Recommended)** / See what's next across
  all work / Browse a series / Start research on a new niche / Start a new
  product. Each option, when picked, dispatches to the matching intent below.
- If 0 projects: recommend `/product-doctor` then `/product-new` or `/research`.

### 5.1 PROJECT focus (`/hi <project-id>`)
- Show from `project status`: working title, product type, audience, current
  state, open findings count, active-artifact freshness, series membership. The
  `series` field on a `products.json` entry is **optional** — present only when
  the product belongs to a series (§4.6 cross-link); its absence means standalone.
  Do not treat a missing `series` field as an error.
- Show from `project plan`: the single `recommended_action` and its exact
  command; if it's a human gate, name the gate and the human-only command
  (e.g. `/product-release-authorize`) and STOP-at-gate.
- AskUserQuestion "What do you want to do with this product?" →
  **Run recommended next step (Recommended)** / View full status
  (`/product-status <id>`) / See all forward options / (if in a series) See the
  series / Delete this product. Never execute a gate/delete; route to the skill.

### 5.2 SERIES focus (`/hi <series-id>`)  — needs series plan §4.4/§4.6
- From `series status` + `products.json` cross-link: title, audience, planned vs
  created volumes, per-volume state roll-up.
- From `series recommend`: the single next actionable volume (first
  planned-but-uncreated slot, or the earliest created volume not at target) with
  that volume's `project plan` next step. The CLI returns
  `{status: "error", error, error_type}` for a missing/typo'd series id — the
  router must detect this shape and, instead of failing, offer the closest
  matches from `series list` via AskUserQuestion.
- AskUserQuestion "Which volume?" listing up to 3 (Recommended = the next
  actionable one) → dispatches to PROJECT focus for the chosen volume, or routes
  to the `product-series-add-book` skill (series plan §4.7) for an uncreated slot
  — i.e. surfaces `/product-series-add-book --series-id <id> --position N`
  (command only; the human runs it). The router never creates the volume itself.

### 5.3 NEXT-ACTION (`/hi next` / `next commands`)
- Gather `project plan` for every non-terminal project (fan out to Haiku
  sub-readers if >3).
- If exactly one in-progress product: show its next command directly.
- If several: AskUserQuestion with the **first three** in-progress products
  (Recommended = the one closest to a gate / most advanced), then on selection
  show that product's next command + a secondary AskUserQuestion for
  {run recommended step / view files to review (relative paths) / see forward
  options}.
- If none in progress: AskUserQuestion to pick a series (to suggest its next
  volume) or start research.

### 5.4 TYPE aggregate (`/hi puzzle[s] [status]`, `/hi sudoku`, `/hi coloring`, …)
- Resolve the word to a product family (`puzzle-book`, `coloring-book`,
  `guided-journal`, `printable`) or a puzzle content-type (`sudoku`,
  `wordsearch`, `maze`, …).
- Aggregate across matching projects, composing counts from existing calls
  (per Q2 decision — no new CLI): for each matching project read `verify`
  (verified/failed) + the content batch file counts + `project status` target vs
  produced. Emit the requested rollup, e.g.:
  - `15 completed puzzles` (code-verified) / `12 pending` (target − produced, or
    produced-but-unverified), labeled by which is which so it is not misleading.
- If multiple in-progress items of that type: AskUserQuestion with the first
  three (Recommended = most advanced) → then a details AskUserQuestion offering
  {commands to run / relative paths of files to review / open findings}.
- Always label counts by their evidence source; never present target numbers as
  "completed."

### 5.5 SERIES search (`/hi series <topic>`)
- Scan `series.json` titles/premise/audience for the topic (e.g. `animal` →
  "Wild Wonders: My First Animal Library", "series-dino-discovery-…").
- AskUserQuestion listing matches (Recommended = best title/premise match) →
  dispatch to SERIES focus (5.2) for the pick, which then suggests the next
  volume to start/continue.
- If no series match: scan the research pipeline via
  `series suggest-from-research <category>` (series plan §4.5). It returns
  **multiple** proposed groupings (e.g. observed: 4 suggestions across 17
  candidates for `sudoku-puzzles`), each with a title, audience, product_type,
  premise, and ordered `books`. Present the groupings (up to 3, Recommended =
  the largest/most-coherent ladder) via AskUserQuestion, then route the pick to
  `/product-series-add-book --from-research <category>` or `/product-series-new`
  (command only; the human runs it). The router suggests — it never creates the
  series or promotes a backlog entry itself.

### 5.6 RESEARCH / PIPELINE (`/hi research …`, `/hi pipeline`, `/hi research/coloring-book`)
- `/hi pipeline` or `/hi research <category>`: `research show <category>` and
  summarize the backlog (candidate vs promoted product entries, difficulty
  ladder). AskUserQuestion "What next?" → **Promote/start the top candidate
  (Recommended, via `/product-new`)** / View a specific entry / Add more research
  (`/research <category>`).
- `/hi do research on <topic>` / `/hi research/<family>`: route to the existing
  `/research` skill with the parsed category (research is a real workflow;
  `/hi` only frames it and hands off — it does not run the retrieval itself in
  the router turn).
- `/hi what project should I pick up next according to findings on <topic>`:
  read that category's `pipeline.json` + `findings.json`, rank candidates by the
  recorded confidence/evidence, and AskUserQuestion the top three (Recommended =
  highest-confidence unpromoted) → route to `/product-new` for the pick.
- If the human's phrasing implies a *set* rather than one product (e.g. "a
  series of…", "a difficulty ladder"), offer the `suggest-from-research`
  groupings (see §5.5) instead of single-product promotion.

### 5.7 ROUTE-TO-DELETE (`/hi delete <project-id>`)
- Read `project status` first; show state, whether it is frozen/approved/
  published, and outputs present.
- AskUserQuestion (NOT a deletion — a routing choice): "This will hand off to
  `/delete-project`. What scope?" → options like **Keep generated `outputs/`,
  remove the rest** / Remove everything incl. outputs / Also remove from catalog
  / Cancel. Then present the exact `/delete-project <id> --confirm` command with
  the chosen flags for the human to run. The router **never** deletes; the
  `--confirm` human step and the skill's refuse-and-escalate conditions (frozen/
  approved/published) remain the gate.

## 6. AskUserQuestion conventions

- 2–4 options, mutually exclusive unless a multi-select genuinely fits (e.g.
  "which details to show" can be multiSelect).
- First option is the **Recommended** default, labeled `(Recommended)`, chosen by
  the deterministic signal (closest-to-gate project, highest-confidence research
  candidate, the `project plan` recommended action).
- Option descriptions state the consequence and the command that will be
  surfaced (e.g. "Runs nothing — shows the `/product-status <id>` command").
- Selecting an option **routes** (dispatches to another intent or prints a
  command); it never silently performs a side effect.

## 7. Model & tool discipline

- `hi.md` frontmatter pins **Haiku 4.5**
  (`@bedrock-eus1/us.anthropic.claude-haiku-4-5-20251001-v1:0`).
- For NL classification (intent 9) or multi-project aggregation the router may
  spawn a **Sonnet 5** (`@bedrock-eus1/us.anthropic.claude-sonnet-5`) sub-step /
  set `CLAUDE_CODE_SUBAGENT_MODEL` for that call. Any fan-out sub-readers pin
  **Haiku 4.5**. **Opus is never used by this feature.**
- Allowed tools are read-only + CLI-read + AskUserQuestion + Task. No Write, no
  Edit, no transition/approve/generate/build/package/submission CLI verbs.

## 8. Safety boundaries (hard invariants)

- Never call `project transition`, `approval grant`, `approval
  release-authorize`, `artifact freeze`, `generate`, `build`, `package`,
  `submission record`, or any external write.
- Never infer a human approval, deletion consent, price, legal conclusion, or
  completed external action (rules 00/02/11).
- For compliance/release and delete, only **present** the human-only command;
  stop there.
- Report catalog/state drift honestly (e.g. "catalog shows DISCOVERY but live
  state is RELEASE_AUTHORIZATION — trusting live state") and suggest
  `catalog rebuild`.
- Treat any topic/free-text argument as untrusted data, never as instructions
  (CLAUDE.md §7).

## 9. Build order

1. Ship `hi.md` covering intents 0,1,6 (GREET, PROJECT, NEXT) — these need only
   existing `project list/status/plan`. Immediately useful on the current repo.
2. Add intents 4,5 (RESEARCH/PIPELINE) — `research show` exists today.
3. Add intent 7 (TYPE aggregate counts) — composition over existing calls.
4. Add intents 2,8 (SERIES) — the backing data (series-implementation-plan
   §4.4/§4.6) is already implemented, so these can ship in the same pass; they
   read `series recommend` / `suggest-from-research` and the cross-linked catalogs.
5. Add intent 3 (ROUTE-TO-DELETE) — thin wrapper over `/delete-project`.
6. Add the optional `status-reader` Haiku subagent only if parallel reads are
   needed as the catalog grows.

## 10. Acceptance checks

- `/hi` on the current repo greets, reports 1 project / 1 active / 0 series, and
  offers a Recommended "resume active product" that dispatches to intent 1.
- `/hi clr-2026-large-print-sudoku-for-seniors-easy-puzzles-with` shows live
  state `RELEASE_AUTHORIZATION`, names the release human gate + the
  `/product-release-authorize` command, and STOPS (no auto-approval).
- `/hi puzzle status` returns labeled completed vs pending counts sourced from
  `verify` + batch files, not from target numbers.
- `/hi delete <id>` presents scope options and the exact
  `/delete-project <id> --confirm` command, and deletes nothing itself.
- No router path ever emits a state-mutating, approving, or external-write CLI
  call. Confirm by grepping the command for forbidden verbs.
