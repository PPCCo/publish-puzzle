export const meta = {
  name: 'product-multi-review',
  description: 'Run independent product reviews by dimension and synthesize structured, deduplicated findings',
  phases: [
    { title: 'Review', detail: 'per-dimension independent review', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8' },
    { title: 'Integrity', detail: 'review-integrity verification', model: '@bedrock-eus1/us.anthropic.claude-sonnet-5' },
    { title: 'Synthesis', detail: 'deduplicated finding register', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8' },
  ],
}

const input = args ?? {}
const reviewTypes = input.reviewTypes ?? [
  'solvability and solution correctness (code-backed)',
  'difficulty-label accuracy and progression fit',
  'audience-band and reading-level fit',
  'originality and similarity risk',
  'rights and asset provenance',
  'accessibility, contrast, and legibility',
  'child-safety and age appropriateness',
  'layout, answer-key placement, and page-budget integrity',
]

const reviews = await pipeline(reviewTypes, reviewType =>
  agent(`Act as the independent specialist reviewer for ${reviewType}. Read project ${input.projectId}, artifact ${input.artifactPath}, and require exact hash ${input.artifactHash}. Read the approved brief, age band, design policy, and applicable standards. Do not edit the artifact. Write or return a review matching .claude/schemas/review.schema.json. Every finding must have severity, precise location, evidence, recommendation, measurable acceptance test, status=open, and confidence. Return PASS, CONDITIONAL_PASS, or FAIL. If the artifact hash differs, return a stale-artifact failure.`, {
    label: reviewType,
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

const verifier = await agent(`Act as a review-integrity verifier. Check these reviews for the required artifact hash ${input.artifactHash}, duplicate findings, vague locations, unsupported claims, reviewer scope overlap, missing critical dimensions (solvability, solution_correctness, originality, rights, accessibility, audience_fit), and contradictory recommendations. Do not erase credible minority findings. Return accepted reviews, rejected reviews with reasons, and conflicts requiring evidence or human resolution.
${JSON.stringify(reviews)}`, { label: 'review-integrity', phase: 'Integrity', model: '@bedrock-eus1/us.anthropic.claude-sonnet-5', effort: 'xhigh' })

return await agent(`Act as the quality-lead. Synthesize the verified reviews into a deduplicated finding register and revision sequence. Rank blockers and majors first, identify dependencies and conflicts, preserve exact reviewer evidence, and state which findings require independent code re-verification after repair. Enforce the configured revision-cycle and repair limits. Do not edit the artifact or declare a gate pass.
INPUT=${JSON.stringify(input)}
VERIFIED=${JSON.stringify(verifier)}`, { label: 'review-synthesis', phase: 'Synthesis', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8', effort: 'xhigh' })
