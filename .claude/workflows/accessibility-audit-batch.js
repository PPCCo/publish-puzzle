export const meta = {
  name: 'accessibility-audit-batch',
  description: 'Independently audit accessibility, contrast, legibility, large-print fit, and alt-text/decorative designation across artifacts in parallel and synthesize a deduplicated finding register',
}

// args: { projectId, targets?: string[], context? }
const input = args ?? {}
const projectId = input.projectId
const cli = 'python3 ${CLAUDE_PROJECT_DIR}/.claude/scripts/ph_cli.py'

if (!projectId) {
  return 'ERROR: accessibility-audit-batch requires args.projectId'
}

const targets = input.targets ?? [
  'grid, cell, and rule contrast and legibility at target trim',
  'type size, font, and large-print/senior band conformance',
  'alt text or documented decorative designation for cover and interior art',
  'digital printable DPI and print-at-home page size (US Letter / A4)',
]

// FAN-OUT: independent accessibility lenses. Reviewers do not repair.
const audits = await pipeline(targets, target =>
  agent(`Act as the independent accessibility-auditor for project ${projectId}, focused on: ${target}. Run the deterministic accessibility audit for evidence:
${cli} audit accessibility ${projectId}
Read the resolved design policy and age band. Do NOT edit any artifact. Return decision PASS/WARNING/FAIL for this lens with exact per-artifact evidence and the required correction. Treat not-run as fail.`, {
    label: target,
    schema: {
      type: 'object',
      required: ['lens', 'decision', 'findings'],
      properties: {
        lens: { type: 'string' },
        decision: { enum: ['PASS', 'WARNING', 'FAIL'] },
        findings: { type: 'array', items: { type: 'object' } },
      },
    },
  }),
)

// FAN-IN: accessibility-auditor synthesis. Gate must PASS/WARNING before compliance;
// this workflow reports, it does not grant the compliance gate.
return await agent(`Act as the accessibility-auditor lead. Merge these independent accessibility audits for project ${projectId} into one deduplicated finding register and repair sequence. Any FAIL blocks the compliance gate; preserve each lens's exact evidence. State which repaired artifacts require re-audit by code. Do not edit artifacts and do not grant the compliance gate.
${JSON.stringify(audits)}`, { label: 'accessibility-synthesis' })
