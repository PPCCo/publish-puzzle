# STD-APPROVAL — Human Approval Contract

An approval SHALL record approver identity, role, timestamp, gate, exact artifact hashes, scope, exclusions, decision, notes, and optional expiry. It SHALL be stored as a separate JSON record and appended to the event log.

A material change to the approved *source* material invalidates the approval. An approval binds to the source content, design, or metadata artifacts it approves — not to downstream build outputs (interior/cover PDF, channel package); re-rendering a downstream output from an unchanged approved source does NOT invalidate the approval. Release authorization additionally binds channel, edition, product types, territories, pricing scope, permitted operations, maximum spend, and a one-time nonce. The base framework does not execute live external publication.

The six required gates are: niche, interior, cover, compliance, listing, release. An approval at the niche gate does not authorize interior generation; an approval at the interior gate does not authorize cover production. Each gate must be independently satisfied before the next stage begins.
