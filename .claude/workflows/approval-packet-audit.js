export const meta = {
  name: 'approval-packet-audit',
  description: 'Check that a proposed human approval packet (niche, interior, cover, compliance, listing, or release) contains current hashes, evidence, scope, risks, and valid decision options without granting anything',
  phases: [
    { title: 'Audit', detail: 'per-lens readiness checks', model: '@bedrock-eus1/us.anthropic.claude-sonnet-5' },
    { title: 'Synthesis', detail: 'readiness verdict', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8' },
  ],
}

// args: { projectId, gate, packet?, context? }
const input = args ?? {}
const lenses = [
  'state and transition validity for the requested gate',
  'artifact hash freshness and downstream dependency invalidation',
  'code-verified solvability/uniqueness/answer-key, originality, rights, accessibility, and preflight evidence completeness',
  'scope, exclusions, approver role and count, expiry, and downstream consequences',
]

// FAN-OUT: independent readiness lenses. None may grant approval.
const checks = await pipeline(lenses, lens =>
  agent(`Audit the proposed approval packet for the "${input.gate}" gate on project ${input.projectId} through this lens: ${lens}. Inputs: ${JSON.stringify(input)}. Do not grant approval, freeze, release, or transition. Return missing evidence, stale inputs, ambiguous scope, and the exact corrections required.`, { label: lens, phase: 'Audit', model: '@bedrock-eus1/us.anthropic.claude-sonnet-5', effort: 'high' }),
)

// FAN-IN: readiness verdict only. Never infers consent.
return await agent(`Merge these checks into a human-readable approval-packet readiness result for the "${input.gate}" gate on project ${input.projectId}. Return READY or NOT_READY, the exact hashes and scope that would be approved, unresolved risks, and the available decision options plus the exact /product-approve-* (or /product-freeze, /product-release-authorize) command a human would run. Never infer consent and never invoke any human-only skill.
${JSON.stringify(checks)}`, { label: 'approval-readiness', phase: 'Synthesis', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8', effort: 'high' })
