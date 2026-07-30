---
paths:
  - ".claude/scripts/**/*.py"
---

# Python implementation

- Support Python 3.11 or later.
- Use type annotations, pathlib, atomic writes, explicit exceptions, and deterministic output ordering.
- All puzzle generators and verifiers SHALL accept an explicit integer seed and produce identical output for the same seed; never read system entropy inside a generator or verifier.
- SHA-256 every generated artifact and record the hash in the provenance record.
- Validate all JSON outputs against their declared jsonschema 2020-12 schema before writing.
- Keep network access out of core state/build/generator/verifier modules.
- Use subprocess argument arrays, never `shell=True`.
- Validate all untrusted paths remain inside the repository or selected project.
- Add unittest coverage for state transitions, gates, generators, verifiers, builders, and security checks.
