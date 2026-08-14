from __future__ import annotations

import json
import unittest
from pathlib import Path

import common  # noqa: F401  -- sets up sys.path for the publishing_house package

from publishing_house import maintenance
from publishing_house.util import atomic_write_text


class MaintenanceScanTests(unittest.TestCase):
    """`scan_signals`/`scan` read logs read-only, rank deny reasons, flag a
    ph_cli.py external-writes false positive, and land the report under
    maintenance/ (never under projects/)."""

    def setUp(self) -> None:
        self.fixture = common.RepoFixture()
        self.root = self.fixture.root

    def tearDown(self) -> None:
        self.fixture.close()

    def _write_hooks(self, records: list[dict]) -> Path:
        path = self.root / ".claude" / "logs" / "hooks.ndjson"
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(path, "\n".join(json.dumps(r) for r in records) + "\n")
        return path

    def test_ranks_deny_reasons_and_tolerates_garbage(self) -> None:
        path = self.root / ".claude" / "logs" / "hooks.ndjson"
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            json.dumps({"decision": "deny", "reason": "A", "command": "x"}),
            "not json at all",
            "",
            json.dumps({"decision": "deny", "reason": "A", "command": "y"}),
            json.dumps({"decision": "ask", "reason": "B", "command": "z"}),
        ]
        atomic_write_text(path, "\n".join(lines) + "\n")
        signals = maintenance.scan_signals(self.root)
        self.assertEqual(signals["hook_record_count"], 3)  # garbage/blank skipped
        self.assertEqual(signals["deny_reasons"][0], {"reason": "A", "count": 2})
        self.assertEqual(signals["ask_reasons"][0], {"reason": "B", "count": 1})

    def test_flags_ph_cli_external_write_false_positive(self) -> None:
        self._write_hooks(
            [
                {
                    "decision": "deny",
                    "reason": "external writes are disabled; create a package or dry-run record instead",
                    "command": ".venv/bin/python3 .claude/scripts/ph_cli.py approval release-authorize x --operation submit",
                    "project_id": "clr-2026-x",
                },
                {
                    "decision": "deny",
                    "reason": "external writes are disabled; create a package or dry-run record instead",
                    "command": "curl -X POST https://example.com/publish",
                },
            ]
        )
        signals = maintenance.scan_signals(self.root)
        fps = signals["false_positive_denies"]
        self.assertEqual(len(fps), 1)
        self.assertIn("ph_cli.py", fps[0]["command"])

    def test_scan_writes_under_maintenance_not_projects(self) -> None:
        self._write_hooks([{"decision": "deny", "reason": "A", "command": "x"}])
        maintenance.scan(self.root, write=True)
        self.assertTrue((self.root / "maintenance" / "scan-latest.json").is_file())
        self.assertTrue((self.root / "maintenance" / "maintenance-log.ndjson").is_file())
        # Nothing was written under projects/.
        self.assertEqual(list((self.root / "projects").glob("*")), [])

    def test_missing_memory_dir_degrades_to_empty(self) -> None:
        result = maintenance.scan_memories(self.root, self.root / "no-such-memory")
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
