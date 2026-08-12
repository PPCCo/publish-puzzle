export const meta = {
  name: 'content-generation-fanout',
  description: 'Deterministically generate many content batches in parallel by code, then independently verify every batch by code and synthesize a solvability/uniqueness/answer-key report',
  phases: [
    { title: 'Generate', detail: 'seeded code generation per batch', model: '@bedrock-eus1/us.anthropic.claude-haiku-4-5-20251001-v1:0' },
    { title: 'Verify', detail: 'independent code verification per batch', model: '@bedrock-eus1/us.anthropic.claude-sonnet-5' },
    { title: 'Synthesis', detail: 'content report', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8' },
  ],
}

// args: { projectId, batches: [{ contentType, count, difficulty, seed? }], context? }
const input = args ?? {}
const projectId = input.projectId
const batches = input.batches ?? []
const cli = '${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py'

if (!projectId || batches.length === 0) {
  return 'ERROR: content-generation-fanout requires args.projectId and a non-empty args.batches array'
}

// FAN-OUT: generate each batch deterministically from a seed. Generation is by
// code; the generating agent must NOT assert solvability, uniqueness, or
// difficulty — that is the verifier's job.
const generated = await pipeline(batches, batch =>
  agent(`Act as the puzzle-generator/printable-designer. For project ${projectId}, deterministically generate one content batch by running:
${cli} generate ${projectId} --type ${batch.contentType} --count ${batch.count ?? 1} --difficulty ${batch.difficulty ?? 'mixed'}${batch.seed != null ? ` --seed ${batch.seed}` : ''} --actor content-generation-fanout
Preserve the base seed and provenance. Register the produced artifact. Return the artifact id, artifact hash, base seed, content type, and count. Do NOT claim the content is solvable, unique, or correctly labeled — verification is a separate, independent step.`, {
    label: `generate-${batch.contentType}`,
    phase: 'Generate',
    model: '@bedrock-eus1/us.anthropic.claude-haiku-4-5-20251001-v1:0',
    effort: 'medium',
    schema: {
      type: 'object',
      required: ['contentType', 'artifactId', 'artifactHash'],
      properties: {
        contentType: { type: 'string' },
        artifactId: { type: 'string' },
        artifactHash: { type: 'string' },
        baseSeed: { type: 'number' },
        count: { type: 'number' },
      },
    },
  }),
)

// INDEPENDENT VERIFICATION: code checks what code produced. A separate agent
// runs the deterministic verifier per content type and trusts no generator claim.
const verified = await pipeline(generated, gen =>
  agent(`Act as the independent content-verifier. Do not trust the generator summary. For project ${projectId}, independently verify the "${gen.contentType}" batch (artifact ${gen.artifactId}, hash ${gen.artifactHash}) by running:
${cli} verify ${projectId} --type ${gen.contentType}
Report, per item: solvability, uniqueness of solution where applicable, answer-key correctness, and whether the measured difficulty matches the label. Return the verifier decision (PASS/FAIL), per-item results, and any failing item identifiers with exact evidence. Never edit or regenerate content.`, {
    label: `verify-${gen.contentType}`,
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

// FAN-IN: synthesize a batch-level report. No approval, no freeze.
return await agent(`Act as the difficulty-curator and quality-lead. Merge the independent verification results into a single content report for project ${projectId}. Confirm every batch has a current PASS from code before recommending progress; treat any FAIL, stale hash, or not-run as a blocker. Summarize solvability, uniqueness, answer-key correctness, and difficulty-label accuracy across all batches; list every failing item with its evidence and the required regeneration/repair. Do not grant the interior gate, do not freeze artifacts, and do not declare the interior approved.
GENERATED=${JSON.stringify(generated)}
VERIFIED=${JSON.stringify(verified)}`, { label: 'content-verification-synthesis', phase: 'Synthesis', model: '@bedrock-eus2/us.anthropic.claude-opus-4-8', effort: 'high' })
