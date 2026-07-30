# PAT-013 — Content Freeze and Invalidation

Content freeze (triggered at interior-approval gate) records a hash set for the verified puzzle/coloring/journal content batch, title, contributor attribution, and approved asset-provenance records. Changes to frozen content invalidate downstream cover briefs, layout, accessibility reports, metadata, proofs, and release authorization according to the dependency map.
