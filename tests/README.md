# Tests

Run from the repository root:

```bash
python -m unittest discover -s tests -v
```

The suite copies `.claude` into a throwaway repository (`common.RepoFixture`) so tests
never mutate real projects. It exercises the framework's safety-critical invariants:

| File | Covers |
|---|---|
| `test_framework_structure.py` | `framework validate` passes; agent frontmatter; human-only skills; disabled external writes; workflow shape; required boundary files |
| `test_project_lifecycle.py` | Init, allowed transitions, illegal-transition rejection, configured gate edges, deterministic `plan next` |
| `test_content_generation_and_verification.py` | Deterministic seeded generation, independent code verification PASS, not-run is not a silent pass |
| `test_cli.py` | `framework validate` and `generate`→`verify` through the CLI entry point |
| `test_gate_integrity.py` | Human-only skills disable model invocation; the niche gate refuses without recorded evidence; `CLAUDE.md` present for repo-root resolution |
