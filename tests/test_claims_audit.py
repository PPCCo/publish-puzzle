from __future__ import annotations

import unittest
from pathlib import Path

import common  # noqa: F401  -- sets up sys.path for the publishing_house package

from publishing_house.claims import audit_claims
from publishing_house.paths import ProjectPaths
from publishing_house.util import atomic_write_json, atomic_write_yaml, load_yaml


class ClaimsAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = common.RepoFixture()
        self.root = self.fixture.root

    def tearDown(self) -> None:
        self.fixture.close()

    def _project(self, audience: str, band: str, count: int, verified_count: int) -> str:
        pid, _ = self.fixture.project(
            project_id="clr-2026-claims-demo", audience=audience, product_type="puzzle-book"
        )
        paths = ProjectPaths(self.root, pid).require()
        project = load_yaml(paths.config)
        project.setdefault("content_plan", {})["target_content_count"] = count
        project.setdefault("production", {}).setdefault("design", {}).setdefault(
            "reading_level_target", {}
        )["band"] = band
        atomic_write_yaml(paths.config, project)
        atomic_write_json(
            paths.directory / "verification" / "content-verification-latest.json",
            {"decision": "PASS", "item_count": verified_count, "batches": []},
        )
        return pid

    def _set_metadata(self, pid: str, description: str) -> None:
        paths = ProjectPaths(self.root, pid).require()
        atomic_write_json(
            paths.directory / "metadata" / "book.json",
            {"title": "Demo", "description": description},
        )

    def test_pass_when_claims_match_facts(self) -> None:
        pid = self._project("adult-general", "adult-general", count=100, verified_count=100)
        self._set_metadata(pid, "100 puzzles with complete solutions at the back.")
        report = audit_claims(self.root, pid)
        self.assertEqual(report["decision"], "PASS", report["issues"])
        self.assertTrue(report["checks"]["count_matches"])
        self.assertTrue(report["checks"]["large_print_valid"])

    def test_fail_on_count_mismatch(self) -> None:
        # Cover derives "200 Puzzles" from content_plan; verified count is 100.
        pid = self._project("adult-general", "adult-general", count=200, verified_count=100)
        self._set_metadata(pid, "200 puzzles inside.")
        report = audit_claims(self.root, pid)
        self.assertEqual(report["decision"], "FAIL")
        self.assertFalse(report["checks"]["count_matches"])

    def test_fail_on_large_print_for_adult_band(self) -> None:
        pid = self._project("adult-general", "adult-general", count=100, verified_count=100)
        self._set_metadata(pid, "A large print puzzle book, 100 puzzles.")
        report = audit_claims(self.root, pid)
        self.assertEqual(report["decision"], "FAIL")
        self.assertFalse(report["checks"]["large_print_valid"])

    def test_large_print_valid_for_senior_band(self) -> None:
        pid = self._project("senior-large-print", "senior-large-print", count=100, verified_count=100)
        self._set_metadata(pid, "Large print, 100 puzzles.")
        report = audit_claims(self.root, pid)
        self.assertTrue(report["checks"]["large_print_valid"])
        self.assertEqual(report["decision"], "PASS", report["issues"])


if __name__ == "__main__":
    unittest.main()
