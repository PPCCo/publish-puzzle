export const meta = {
  name: 'difficulty-audit',
  description: 'Independently measure whether each content batch\'s difficulty matches its label by code, in parallel, and synthesize a progression-fit report',
  phases: [
    { title: 'Measure', detail: 'measured-vs-labeled difficulty per content type', model: '@bedrock-eus1/us.anthropic.claude-sonnet-5' },
    { title: 'Synthesis', detail: 'progression-fit report', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8' },
  ],
}

// args: { projectId, contentTypes?: string[], context? }
const input = args ?? {}
const projectId = input.projectId
const contentTypes = input.contentTypes ?? []
const cli = 'python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py'

if (!projectId) {
  return 'ERROR: difficulty-audit requires args.projectId'
}

if (contentTypes.length === 0) {
  return await agent(`Act as the independent difficulty-curator for project ${projectId}. Run:
${cli} verify ${projectId}
From the verifier output, report per content type whether the MEASURED difficulty matches the LABELED difficulty and whether the easy->hard progression is monotonic and appropriate for the audience band. Return failing items with exact measured-vs-labeled evidence. Never edit or regenerate content; treat not-run as fail.`, { label: 'difficulty-all', phase: 'Measure', model: '@bedrock-eus1/us.anthropic.claude-sonnet-5', effort: 'high' })
}

// FAN-OUT: one measured difficulty check per content type, by code.
const measured = await pipeline(contentTypes, contentType =>
  agent(`Act as the independent difficulty-curator for the "${contentType}" batch in project ${projectId}. Do not trust any generator or prior summary. Run:
${cli} verify ${projectId} --type ${contentType}
Report, per item: the measured difficulty, the labeled difficulty, and whether they match. Return decision PASS/FAIL and every mislabeled item with exact evidence. Never edit or regenerate content.`, {
    label: contentType,
    phase: 'Measure',
    model: '@bedrock-eus1/us.anthropic.claude-sonnet-5',
    effort: 'high',
    schema: {
      type: 'object',
      required: ['contentType', 'decision', 'results'],
      properties: {
        contentType: { type: 'string' },
        decision: { enum: ['PASS', 'FAIL'] },
        results: { type: 'array', items: { type: 'object' } },
        mislabeledItems: { type: 'array', items: { type: 'string' } },
      },
    },
  }),
)

// FAN-IN: progression-fit synthesis across the whole product. No gate.
return await agent(`Act as the difficulty-curator and quality-lead. Merge these measured-difficulty results for project ${projectId} into one progression-fit report. Confirm each batch's labels match measured difficulty and that the cross-batch progression fits the audience band. Rank every mislabeled or non-monotonic item as a blocker or major with exact evidence and the required regeneration/relabel. Do not grant a gate, freeze artifacts, or declare the interior approved.
${JSON.stringify(measured)}`, { label: 'difficulty-synthesis', phase: 'Synthesis', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8', effort: 'high' })
