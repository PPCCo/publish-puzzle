# STD-ARTIFACT — Artifact Contract

Every material artifact SHALL have:

- project ID;
- artifact ID;
- semantic type;
- stage;
- version or revision;
- relative path;
- SHA-256 hash;
- byte size;
- creator identity;
- creation timestamp;
- source artifact IDs;
- model/tool provenance when generated;
- rights status;
- validation status.

Approved or frozen artifacts are immutable. Corrections create a new artifact. Any change to content, cover, metadata, price, territory, or package invalidates approvals whose scope includes the changed material.

Approvals bind to the *source* content, design, and metadata artifacts they approve — not to downstream build outputs. Re-rendering a downstream build output (interior or cover PDF, channel package, launch guide) from an unchanged approved source does NOT invalidate the approval. Changing the approved source itself still does. Each human gate binds only its own material artifact types; a later rebuild of a *different* artifact type never intersects an earlier gate's bound hashes.

For puzzle content, the generator seed and puzzle-type parameters are part of the provenance record and SHALL be stored alongside the artifact. For coloring line art, the originality attestation record ID is a required provenance field. Verified solvability and solution correctness are required validation-status fields for puzzle artifacts.
