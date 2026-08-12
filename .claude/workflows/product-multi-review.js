export const meta = {
  name: 'product-multi-review',
  description: 'Run independent product reviews by grouped dimension and synthesize structured, deduplicated findings',
  phases: [
    { title: 'Review', detail: 'grouped independent review (per-dimension findings preserved)', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8' },
    { title: 'Integrity', detail: 'review-integrity verification', model: '@bedrock-eus1/us.anthropic.claude-sonnet-5' },
    { title: 'Synthesis', detail: 'deduplicated finding register', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8' },
  ],
}

const input = args ?? {}
// Grouped reviewers. Each group's agent MUST emit a SEPARATE finding per underlying
// dimension (severity/location/evidence/recommendation/acceptance-test/status/
// confidence) so the quality gate's per-dimension thresholds still evaluate.
// Grouping changes WHO reviews, not WHAT is scored. Child-safety and originality keep
// their own dimension inside group B. Callers may override with input.reviewGroups.
const reviewGroups = input.reviewGroups ?? [
  {
    key: 'solvability-and-difficulty',
    dimensions: ['solvability and solution correctness (code-backed)', 'difficulty-label accuracy and progression fit'],
  },
  {
    key: 'audience-safety-originality',
    dimensions: ['audience-band and reading-level fit', 'child-safety and age appropriateness', 'originality and similarity risk'],
  },
  {
    key: 'rights-and-accessibility',
    dimensions: ['rights and asset provenance', 'accessibility, contrast, and legibility'],
  },
  {
    key: 'structure-and-layout',
    dimensions: ['layout and answer-key placement', 'page-budget integrity'],
  },
]

const reviews = await pipeline(reviewGroups, group =>
  agent(`Act as the independent specialist reviewer for this GROUP of dimensions: ${group.dimensions.join('; ')}. Read project ${input.projectId}, artifact ${input.artifactPath}, and require exact hash ${input.artifactHash}. Read the approved brief, age band, design policy, and applicable standards. Do not edit the artifact. Return a review matching .claude/schemas/review.schema.json. Emit findings PER dimension (do not merge dimensions): every finding must have severity, precise location, evidence, recommendation, measurable acceptance test, status=open, confidence, and the dimension it belongs to. Score EACH dimension in this group separately. Return PASS, CONDITIONAL_PASS, or FAIL for the group. If the artifact hash differs, return a stale-artifact failure.`, {
    label: group.key,
    phase: 'Review',
    model: '@bedrock-eus2/us.anthropic.claude-opus-4-8',
    effort: 'high',
    schema: {
      type: 'object',
      required: ['reviewerRole', 'artifactHash', 'decision', 'scores', 'findings', 'summary'],
      properties: {
        reviewerRole: { type: 'string' },
        artifactHash: { type: 'string' },
        decision: { enum: ['PASS', 'CONDITIONAL_PASS', 'FAIL'] },
        scores: { type: 'object' },
        findings: { type: 'array', items: { type: 'object' } },
        summary: { type: 'string' },
        limitations: { type: 'array', items: { type: 'string' } },
      },
    },
  }),
)

const verifier = await agent(`Act as a review-integrity verifier. Check these grouped reviews for the required artifact hash ${input.artifactHash}, duplicate findings, vague locations, unsupported claims, reviewer scope overlap, missing critical dimensions (solvability, solution_correctness, originality, rights, accessibility, audience_fit), and contradictory recommendations. Do not erase credible minority findings. Return accepted reviews, rejected reviews with reasons, and conflicts requiring evidence or human resolution.
${JSON.stringify(reviews)}`, { label: 'review-integrity', phase: 'Integrity', model: '@bedrock-eus1/us.anthropic.claude-sonnet-5', effort: 'high' })

return await agent(`Act as the quality-lead. Synthesize the verified reviews into a deduplicated finding register and revision sequence. Rank blockers and majors first, identify dependencies and conflicts, preserve exact reviewer evidence, and state which findings require independent code re-verification after repair. Enforce the configured revision-cycle and repair limits. Do not edit the artifact or declare a gate pass.
INPUT=${JSON.stringify(input)}
VERIFIED=${JSON.stringify(verifier)}`, { label: 'review-synthesis', phase: 'Synthesis', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8', effort: 'high' })
