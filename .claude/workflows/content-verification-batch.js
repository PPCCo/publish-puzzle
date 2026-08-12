export const meta = {
  name: 'content-verification-batch',
  description: 'Independently verify already-generated content batches by code in parallel and synthesize a deduplicated solvability/uniqueness/answer-key finding register',
  phases: [
    { title: 'Verify', detail: 'independent code verification per content type', model: '@bedrock-eus1/us.anthropic.claude-sonnet-5' },
    { title: 'Synthesis', detail: 'finding register', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8' },
  ],
}

// args: { projectId, contentTypes?: string[], context? }
const input = args ?? {}
const projectId = input.projectId
const cli = '${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py'

if (!projectId) {
  return 'ERROR: content-verification-batch requires args.projectId'
}

const contentTypes = input.contentTypes ?? []
if (contentTypes.length === 0) {
  // Verify all content types at once when none are specified.
  return await agent(`Act as the independent content-verifier for project ${projectId}. Run:
${cli} verify ${projectId}
Report the overall decision and, per content type, solvability, uniqueness of solution where applicable, answer-key correctness, and difficulty-label accuracy. Return failing items with exact evidence. Never edit or regenerate content; treat not-run as fail.`, { label: 'verify-all', phase: 'Verify', model: '@bedrock-eus1/us.anthropic.claude-sonnet-5', effort: 'medium' })
}

const checks = await pipeline(contentTypes, contentType =>
  agent(`Act as the independent content-verifier for the "${contentType}" batch in project ${projectId}. Do not trust any generator summary. Run:
${cli} verify ${projectId} --type ${contentType}
Return the decision (PASS/FAIL) and per-item results for solvability, uniqueness where applicable, answer-key correctness, and difficulty-label accuracy, with exact failing-item evidence. Never edit or regenerate content.`, {
    label: contentType,
    phase: 'Verify',
    model: '@bedrock-eus1/us.anthropic.claude-sonnet-5',
    effort: 'medium',
    schema: {
      type: 'object',
      required: ['contentType', 'decision', 'results'],
      properties: {
        contentType: { type: 'string' },
        decision: { enum: ['PASS', 'FAIL'] },
        results: { type: 'array', items: { type: 'object' } },
        failingItems: { type: 'array', items: { type: 'string' } },
      },
    },
  }),
)

return await agent(`Act as the difficulty-curator and quality-lead. Merge these independent verification results into a deduplicated finding register and repair sequence for project ${projectId}. Rank any unsolvable, non-unique, key-mismatch, or mislabeled-difficulty items as blockers or majors. Preserve exact evidence and required regeneration seeds. Do not grant a gate, freeze artifacts, or declare a pass beyond what the code confirmed.
${JSON.stringify(checks)}`, { label: 'verification-synthesis', phase: 'Synthesis', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8', effort: 'high' })
