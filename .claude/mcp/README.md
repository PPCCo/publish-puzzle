# Publishing House MCP server

The local stdio server (`publishing-house`) exposes read-only state, generation, verification, and gate tools plus two local-write tools:

- channel package assembly inside `projects/<id>/outputs/packages/` (KDP, Etsy, Gumroad, generic);
- submission dry-run records inside `projects/<id>/release/`.

Content tools generate puzzle/journal/printable content deterministically from a seed (`content_generate`) and independently verify it by code (`content_verify`) — uniqueness, solvability, and answer-key correctness. Generation and verification are separate tools; a generator never signs off its own verification.

It exposes no marketplace credential, upload, purchase, advertising, legal-acceptance, deletion, or publication tool. Add live connectors as separate, narrowly scoped MCP servers only after implementing platform-specific authentication, idempotency, release-authorization verification, audit evidence, and a human permission boundary.
