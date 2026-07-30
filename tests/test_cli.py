from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout

from common import RepoFixture, SOURCE_ROOT

from publishing_house import cli


def run_cli(root, *argv) -> tuple[int, str]:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = cli.main(["--root", str(root), *argv])
    return code, buffer.getvalue()


class CliSmokeTests(unittest.TestCase):
    def test_framework_validate_passes_on_source_tree(self) -> None:
        code, out = run_cli(SOURCE_ROOT, "framework", "validate")
        self.assertEqual(0, code)
        payload = json.loads(out)
        self.assertEqual("pass", payload["status"])

    def test_generate_then_verify_via_cli(self) -> None:
        fixture = RepoFixture()
        try:
            pid, _ = fixture.project()
            code, _ = run_cli(
                fixture.root, "generate", pid, "--type", "sudoku",
                "--count", "4", "--difficulty", "easy", "--seed", "7", "--actor", "test",
            )
            self.assertEqual(0, code)
            code, out = run_cli(fixture.root, "verify", pid, "--type", "sudoku")
            self.assertEqual(0, code)
            payload = json.loads(out)
            self.assertEqual("PASS", payload["decision"], payload)
        finally:
            fixture.close()


if __name__ == "__main__":
    unittest.main()
