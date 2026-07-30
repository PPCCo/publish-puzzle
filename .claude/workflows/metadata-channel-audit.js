export const meta = {
  name: 'metadata-channel-audit',
  description: 'Audit canonical and channel metadata for accuracy, consistency, discoverability, rights, and per-channel profile compliance across KDP, Etsy, Gumroad, and generic',
}

// args: { projectId, channels?: string[], context? }
const input = args ?? {}
const channels = input.channels ?? ['kdp', 'etsy', 'gumroad', 'generic']

// FAN-OUT: one independent audit per channel profile. No live listing writes.
const reviews = await pipeline(channels, channel =>
  agent(`Act as the packaging-engineer and metadata-specialist auditing the "${channel}" channel for project ${input.projectId}. Read canonical metadata, the current ${channel} channel profile, the cover/title/copyright pages, and the assembled package files. Check required fields, title/subtitle/contributor consistency, description accuracy, keyword/subject relevance and per-channel tag limits (Etsy 13, Gumroad 10, KDP 7 keyword fields), audience/age band, identifiers, rights and territories, accessibility/AI disclosure, pricing scope, print-at-home page size for digital printables, file naming, and rule freshness. Do NOT publish or change any live listing. Return the profile date, PASS/FAIL, findings with exact evidence, and any missing human decisions.`, {
    label: channel,
    schema: {
      type: 'object',
      required: ['channel', 'decision', 'findings'],
      properties: {
        channel: { type: 'string' },
        profileDate: { type: 'string' },
        decision: { enum: ['PASS', 'FAIL'] },
        findings: { type: 'array', items: { type: 'object' } },
        missingHumanDecisions: { type: 'array', items: { type: 'string' } },
      },
    },
  }),
)

// FAN-IN: canonical remains source of truth. No listing gate.
return await agent(`Act as the metadata-specialist and keyword-strategist. Merge these channel reviews while treating canonical metadata as the single source of truth for project ${input.projectId}. Identify contradictions across channels, misleading or unverifiable claims, rights/trademark risk, tag-limit violations, stale profiles, and fields that require a human decision. Return a correction matrix by canonical-versus-channel field. Do not publish, do not change a live listing, and do not grant the listing gate.
${JSON.stringify(reviews)}`, { label: 'metadata-synthesis' })
