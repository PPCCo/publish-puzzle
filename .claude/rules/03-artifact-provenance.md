# Artifact provenance

- Create new revisions instead of overwriting approved/frozen files.
- Register every content revision, cover, illustration set, metadata package, PDF interior, and retailer package.
- Record source artifacts, creator agent, model/tool version, generation method, seed, and rights status.
- Keep generated prompts and seeds when permitted by the provider and useful for reproducibility.
- Downstream build outputs (interior/cover PDFs, channel packages, launch guides) are distinct artifact types and are NOT bound by upstream gate approvals; approvals bind to the source content/design/metadata hashes. Re-rendering a downstream output from an unchanged approved source does not invalidate the approval; changing the approved source does.
