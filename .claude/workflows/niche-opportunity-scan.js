export const meta = {
  name: 'niche-opportunity-scan',
  description: 'Discover and cross-check current puzzle/coloring/journal/printable niche opportunities across independent evidence lenses',
}

const input = args ?? {}
const lenses = input.lenses ?? [
  'durable audience needs and recurring puzzle/activity demand',
  'seasonal and event-driven printable and journal opportunities',
  'category saturation and pricing norms on KDP, Etsy, and Gumroad',
  'audience-band fit and large-print/senior accessibility openings',
  'format opportunities across paperback, hardcover, and digital-pdf printables',
  'rights, trademark, child-safety, and feasibility risks',
]

const findings = await pipeline(lenses, lens =>
  agent(`Act as the specialist best suited to this lens: ${lens}.
Research niche opportunities for ${JSON.stringify(input)}. Use current, dated, credible evidence. Separate event date from publication date. Return an object with an opportunities array. Each opportunity must include niche, productType, audience, evidence, evidenceDates, durability, saturation, feasibility, rightsRisk, safetyRisk, confidence, and sources. Do not claim demand without dated evidence.`, {
    label: lens,
    schema: {
      type: 'object',
      required: ['opportunities'],
      properties: {
        opportunities: {
          type: 'array',
          items: {
            type: 'object',
            required: ['niche', 'productType', 'audience', 'evidence', 'durability', 'confidence', 'sources'],
            properties: {
              niche: { type: 'string' },
              productType: { type: 'string' },
              audience: { type: 'string' },
              evidence: { type: 'array', items: { type: 'string' } },
              evidenceDates: { type: 'array', items: { type: 'string' } },
              durability: { type: 'string' },
              saturation: { type: 'string' },
              feasibility: { type: 'string' },
              rightsRisk: { type: 'string' },
              safetyRisk: { type: 'string' },
              confidence: { type: 'number' },
              sources: { type: 'array', items: { type: 'string' } },
            },
          },
        },
      },
    },
  }),
)

return await agent(`Act as the Market Scout and Competition Analyst.
Deduplicate and challenge these independent findings:
${JSON.stringify(findings)}
Return 5-12 ranked niche opportunities. Reject claims without dated evidence. Preserve disagreements and identify which claims remain unverified. Score audience value, evidence strength, durability, saturation, production feasibility, accessibility opportunity, rights complexity, and child-safety risk from 0-5. Do not select a niche or record any approval.`, {
  label: 'cross-check-and-rank',
  schema: {
    type: 'object',
    required: ['rankedOpportunities', 'rejectedClaims', 'limitations'],
    properties: {
      rankedOpportunities: { type: 'array', items: { type: 'object' } },
      rejectedClaims: { type: 'array', items: { type: 'object' } },
      limitations: { type: 'array', items: { type: 'string' } },
    },
  },
})
