export const meta = {
  name: 'accessibility-audit-batch',
  description: 'Independently audit accessibility, contrast, legibility, large-print fit, and alt-text/decorative designation across all lenses in a single pass over the deterministic audit, returning a deduplicated finding register',
  phases: [
    { title: 'Audit', detail: 'single accessibility audit covering all lenses (code runs once)', model: '@bedrock-eus1/us.anthropic.claude-sonnet-5' },
  ],
}

// args: { projectId, targets?: string[], context? }
const input = args ?? {}
const projectId = input.projectId
const cli = '${CLAUDE_PROJECT_DIR}/.venv/bin/python3 .claude/scripts/ph_cli.py'

if (!projectId) {
  return 'ERROR: accessibility-audit-batch requires args.projectId'
}

// The four lenses all read the SAME deterministic `audit accessibility` result and the
// same design policy, so fanning them into separate agents re-ran identical work. One
// auditor now covers every lens after the code runs once; it MUST still return a
// per-lens decision + evidence so the finding register keeps per-lens granularity.
const lenses = input.targets ?? [
  'grid, cell, and rule contrast and legibility at target trim',
  'type size, font, and large-print/senior band conformance',
  'alt text or documented decorative designation for cover and interior art',
  'digital printable DPI and print-at-home page size (US Letter / A4)',
]

return await agent(`Act as the independent accessibility-auditor for project ${projectId}. Run the deterministic accessibility audit ONCE for evidence:
${cli} audit accessibility ${projectId}
Then evaluate EVERY lens below against that evidence and the resolved design policy + age band. Do NOT edit any artifact. Emit a SEPARATE decision (PASS/WARNING/FAIL) and per-artifact evidence for EACH lens; do not collapse them. Treat not-run as fail. Merge into one deduplicated finding register and repair sequence: any FAIL blocks the compliance gate; state which repaired artifacts require re-audit by code. Do not grant the compliance gate — this workflow reports, it does not approve.
LENSES=${JSON.stringify(lenses)}`, {
  label: 'accessibility-audit-all-lenses',
  phase: 'Audit',
  model: '@bedrock-eus1/us.anthropic.claude-sonnet-5',
  effort: 'high',
  schema: {
    type: 'object',
    required: ['decision', 'lensResults', 'findings'],
    properties: {
      decision: { enum: ['PASS', 'WARNING', 'FAIL'] },
      lensResults: {
        type: 'array',
        items: {
          type: 'object',
          required: ['lens', 'decision'],
          properties: {
            lens: { type: 'string' },
            decision: { enum: ['PASS', 'WARNING', 'FAIL'] },
            evidence: { type: 'string' },
          },
        },
      },
      findings: { type: 'array', items: { type: 'object' } },
    },
  },
})
