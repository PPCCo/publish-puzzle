export const meta = {
  name: 'final-red-team',
  description: 'Adversarially audit the complete release candidate across independent high-risk lenses adapted to solvability, originality, rights, accessibility, and packaging integrity',
  phases: [
    { title: 'Audit', detail: 'per-lens independent red-team audits', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8' },
    { title: 'Challenge', detail: 'adversarial verification of each audit', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8' },
    { title: 'Synthesis', detail: 'release recommendation', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8' },
  ],
}

// args: { projectId, artifacts?: [...], context? }
const input = args ?? {}
const lenses = [
  'product promise versus actual content, difficulty labels, and age-band fit',
  'solvability, solution uniqueness where applicable, and answer-key correctness re-verified by code',
  'originality and similarity risk for line art and puzzle word lists; no tracing or named-artist imitation',
  'rights, asset provenance, font/clip licensing, AI disclosure, and trademark/child-safety risk',
  'accessibility, contrast, legibility, large-print fit, and digital print-at-home page-size correctness',
  'cross-format and cross-channel title, contributor, metadata, price, territory, and file consistency',
  'release engineering: artifact hashes, approvals, placeholders, missing assets, package drift, and accidental secrets',
]

const audits = await pipeline(lenses, lens =>
  agent(`Act as an independent final red-team auditor for ${lens}. Inspect project ${input.projectId} and the exact release-candidate hashes in ${JSON.stringify(input)}. Do not trust prior summaries without spot checks and do not repair files. For solvability/uniqueness/answer-key claims, re-run code verification rather than trusting a summary. Return blocker/major/minor findings with exact evidence, untested areas, and PASS/FAIL for this lens.`, { label: lens, phase: 'Audit', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8', effort: 'xhigh' }),
)

const challenge = await pipeline(audits, audit =>
  agent(`Challenge this audit for false positives, unsupported assumptions, missed cross-artifact dependencies, and insufficient evidence. Return only upheld findings, rejected findings with reasons, and new questions. Do not downgrade a finding for schedule convenience.
${JSON.stringify(audit)}`, { label: 'adversarial-verification', phase: 'Challenge', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8', effort: 'xhigh' }),
)

return await agent(`Act as the independent red-team and final quality auditor. Merge the original and challenged audits for project ${input.projectId}. Preserve exact evidence, stale-hash problems, untested critical areas, and credible minority concerns. Return a release recommendation, residual-risk statement, deduplicated findings, and the required repair/recheck sequence. Never grant final approval, never authorize release, and never submit.
AUDITS=${JSON.stringify(audits)}
CHALLENGE=${JSON.stringify(challenge)}`, { label: 'final-red-team-synthesis', phase: 'Synthesis', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8', effort: 'xhigh' })
