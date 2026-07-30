export const meta = {
  name: 'coloring-line-art-review',
  description: 'Independently review coloring line-art assets per-asset for originality, printability, contrast/legibility, and age appropriateness, then synthesize a deduplicated finding register',
}

// args: { projectId, assets: [{ assetId, artifactPath, artifactHash, subject? }], ageBand?, context? }
const input = args ?? {}
const projectId = input.projectId
const assets = input.assets ?? []

if (!projectId || assets.length === 0) {
  return 'ERROR: coloring-line-art-review requires args.projectId and a non-empty args.assets array'
}

// FAN-OUT: each asset gets an independent visual + originality review. Reviewers
// never edit the asset; they require the exact registered hash.
const reviews = await pipeline(assets, asset =>
  agent(`Act as the independent originality-auditor and art-director reviewing one coloring line-art asset in project ${projectId}. Review asset ${asset.assetId} at ${asset.artifactPath} and require exact hash ${asset.artifactHash}. Read the approved brief, age band ${input.ageBand ?? '(load from project)'}, and design policy. Do NOT edit the asset.
Assess, with exact evidence: (1) ORIGINALITY — no tracing, no derivative of a protected image, no imitation of a named living artist's style; flag any similarity risk. (2) PRINTABILITY — closed shapes, clean fills, line weight, no unintended gray/half-tones, DPI/trim fit. (3) CONTRAST and LEGIBILITY at target trim. (4) AGE APPROPRIATENESS and child-safety for the band. Return decision PASS/CONDITIONAL_PASS/FAIL and findings; treat unverifiable provenance as a blocker.`, {
    label: asset.assetId ?? asset.artifactPath,
    schema: {
      type: 'object',
      required: ['assetId', 'artifactHash', 'decision', 'findings'],
      properties: {
        assetId: { type: 'string' },
        artifactHash: { type: 'string' },
        decision: { enum: ['PASS', 'CONDITIONAL_PASS', 'FAIL'] },
        originalityRisk: { type: 'string' },
        findings: { type: 'array', items: { type: 'object' } },
        summary: { type: 'string' },
      },
    },
  }),
)

// FAN-IN: art-director + originality-auditor synthesize. No cover/interior gate.
return await agent(`Act as the art-director and originality-auditor lead. Merge these independent per-asset reviews for project ${projectId} into one deduplicated finding register and repair sequence. Rank any originality/similarity, provenance, unprintable-line, low-contrast, or age-inappropriate finding as a blocker or major. Preserve each reviewer's exact evidence and asset hash. State which repaired assets require independent re-review. Do not edit any asset, do not grant the cover or interior gate, and do not freeze artifacts.
${JSON.stringify(reviews)}`, { label: 'line-art-review-synthesis' })
