---
name: project-cover-colour-permission
description: For senior-large-print / greyscale-interior products, a full-colour cover is permitted and is NOT a design-policy deviation
metadata:
  type: project
---

For products whose derived `production.colour_interior = false` (e.g. `senior-large-print`, greyscale bands), a **full-colour cover is still permitted** and does NOT require a design-policy deviation rationale.

**Why:** `.claude/rules/22-colour-policy.md` scopes the greyscale/high-contrast rule to the *print interior*. It explicitly states coloring-book covers "MAY be full colour," and the same reasoning applies to greyscale puzzle-book interiors. The `colour_interior` boolean governs interior pages only, not the cover wrap.

**How to apply:** When writing a cover art-direction brief for a greyscale-interior product, state affirmatively that cover colour is permitted (cite rule 22) and that no `colour_interior` contradiction or deviation is being taken. Do not treat a colour cover as an override needing the derived-value/proposed-value/evidence rationale.
