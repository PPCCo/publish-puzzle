export const meta = {
  name: 'marketing-asset-fanout',
  description: 'Draft per-channel listing and marketing briefs (KDP, Etsy, Gumroad, generic) in parallel from approved metadata, then synthesize a consistency-checked kit without publishing',
}

// args: { projectId, channels?: string[], context? }
const input = args ?? {}
const projectId = input.projectId
const cli = 'python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py'

if (!projectId) {
  return 'ERROR: marketing-asset-fanout requires args.projectId'
}

const channels = input.channels ?? ['kdp', 'etsy', 'gumroad', 'generic']

// FAN-OUT: one listing/marketing brief per channel from approved metadata only.
const drafts = await pipeline(channels, channel =>
  agent(`Act as the listing-copywriter and keyword-strategist drafting the "${channel}" marketing brief for project ${projectId}. Base every claim strictly on approved, code-verified metadata and content — never invent difficulty, awards, sales, or endorsements. For reference, you may run:
${cli} marketing listing ${projectId} --channel ${channel}
Respect per-channel tag limits (Etsy 13, Gumroad 10, KDP 7 keyword fields) and audience/age-band accuracy. Return a draft title/subtitle, description, keyword/tag set within the limit, and category suggestions. Do NOT publish, change a live listing, or spend on advertising.`, {
    label: channel,
    schema: {
      type: 'object',
      required: ['channel', 'title', 'description', 'tags'],
      properties: {
        channel: { type: 'string' },
        title: { type: 'string' },
        subtitle: { type: 'string' },
        description: { type: 'string' },
        tags: { type: 'array', items: { type: 'string' } },
        categories: { type: 'array', items: { type: 'string' } },
        unverifiedClaims: { type: 'array', items: { type: 'string' } },
      },
    },
  }),
)

// FAN-IN: consistency-checked kit. Canonical metadata is source of truth. No publish.
return await agent(`Act as the metadata-specialist and listing-copywriter lead. Merge these per-channel drafts for project ${projectId} into one consistency-checked marketing kit, keeping canonical metadata as the single source of truth. Flag cross-channel contradictions, tag-limit violations, unverifiable or misleading claims, and rights/trademark risk. List any claim requiring a human decision. Do not publish, do not change a live listing, do not spend on advertising, and do not grant the listing gate.
${JSON.stringify(drafts)}`, { label: 'marketing-kit-synthesis' })
