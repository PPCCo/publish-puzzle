export const meta = {
  name: 'final-red-team',
  description: 'Adversarially audit the complete release candidate across four independent high-risk lens groups (solvability, originality/rights, accessibility/audience, packaging integrity), then a single batched challenger and synthesis',
  phases: [
    { title: 'Audit', detail: 'four grouped independent red-team audits', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8' },
    { title: 'Challenge', detail: 'one batched adversarial verification of all audits', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8' },
    { title: 'Synthesis', detail: 'release recommendation', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8' },
  ],
}

// args: { projectId, artifacts?: [...], context?, spotCheckCap? }
const input = args ?? {}
// Fixed spot-check cap: audit a bounded number of items, NOT a percentage of the
// book, so cost does not scale with page count. Default 20; override via args.
const spotCheckCap = Number(input.spotCheckCap) || 20

// Four grouped lens bundles. Each grouped auditor MUST still emit findings per
// underlying dimension (severity/location/evidence/recommendation/acceptance-test/
// status) so the quality gate's per-dimension thresholds still evaluate. Grouping
// changes WHO audits, not WHAT is scored.
const lensGroups = [
  {
    key: 'solvability-and-correctness',
    focus: 'solvability, solution uniqueness where applicable, and answer-key correctness, plus product-promise vs actual content, difficulty labels, and age-band fit. RE-RUN code verification for every solvability/uniqueness/answer-key claim; do not trust prior summaries.',
  },
  {
    key: 'originality-and-rights',
    focus: 'originality and similarity risk for line art and puzzle word lists (no tracing, no named-artist imitation) AND rights, asset provenance, font/clip licensing, AI disclosure, and trademark/child-safety risk.',
  },
  {
    key: 'accessibility-and-audience',
    focus: 'accessibility, contrast, legibility, large-print fit, digital print-at-home page-size correctness, AND cross-format/cross-channel title, contributor, metadata, price, territory, and file consistency.',
  },
  {
    key: 'packaging-integrity',
    focus: 'release engineering: artifact hashes, approvals, placeholders, missing assets, package drift, and accidental secrets.',
  },
]

const audits = await pipeline(lensGroups, group =>
  agent(`Act as an independent final red-team auditor for: ${group.focus}
Inspect project ${input.projectId} and the exact release-candidate hashes in ${JSON.stringify(input)}. Do not trust prior summaries without spot checks and do not repair files. Where a claim can be re-verified by code (solvability, uniqueness, answer-key), re-run the code verification rather than trusting a summary. Cap any per-item spot-check at ${spotCheckCap} items (a FIXED count, not a percentage of the book); if you sample rather than exhaustively check, state exactly which items you checked and how many you skipped — never imply full coverage you did not perform. Emit a finding PER underlying dimension in this group (do not collapse dimensions) with blocker/major/minor severity, exact evidence, untested areas, and a PASS/FAIL per dimension.`, { label: group.key, phase: 'Audit', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8', effort: 'high' }),
)

// ONE batched challenger reviews all grouped audits together (replaces the former
// per-audit adversary fan-out).
const challenge = await agent(`Challenge these grouped audits for false positives, unsupported assumptions, missed cross-artifact dependencies, and insufficient evidence. Return, per audit group, only upheld findings, rejected findings with reasons, and new questions. Do not downgrade a finding for schedule convenience, and do not treat an unverified claim as false.
AUDITS=${JSON.stringify(audits)}`, { label: 'batched-adversarial-verification', phase: 'Challenge', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8', effort: 'high' })

return await agent(`Act as the independent red-team and final quality auditor. Merge the original and challenged audits for project ${input.projectId}. Preserve exact evidence, stale-hash problems, untested critical areas, and credible minority concerns. Return a release recommendation, residual-risk statement, deduplicated findings (per dimension), and the required repair/recheck sequence. Never grant final approval, never authorize release, and never submit.
AUDITS=${JSON.stringify(audits)}
CHALLENGE=${JSON.stringify(challenge)}`, { label: 'final-red-team-synthesis', phase: 'Synthesis', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8', effort: 'high' })
