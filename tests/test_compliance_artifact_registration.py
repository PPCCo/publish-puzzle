from __future__ import annotations

import unittest

import common  # noqa: F401  -- sets up sys.path for the publishing_house package

from publishing_house.accessibility import audit_accessibility
from publishing_house.artifacts import list_artifacts
from publishing_house.paths import ProjectPaths
from publishing_house.rights import check_rights
from publishing_house.util import load_json


class ComplianceArtifactRegistrationTests(unittest.TestCase):
    """After the rights and accessibility audits run, the three compliance-bound
    artifact TYPES (rights-gate, rights-ledger, accessibility-gate) must be
    registered and active, so the compliance packet has something to bind — with
    no manual `artifact register`. Re-running must be idempotent."""

    def setUp(self) -> None:
        self.fixture = common.RepoFixture()
        self.root = self.fixture.root
        self.pid, _ = self.fixture.project(project_id="clr-2026-compliance-demo")
        self.paths = ProjectPaths(self.root, self.pid).require()

    def tearDown(self) -> None:
        self.fixture.close()

    def _active(self) -> dict:
        return load_json(self.paths.state).get("active_artifacts", {})

    def _types(self) -> set[str]:
        return {a["type"] for a in list_artifacts(self.root, self.pid)}

    def test_rights_and_accessibility_register_compliance_types(self) -> None:
        check_rights(self.root, self.pid)  # writes + registers rights-gate (ledger absent -> skipped)
        audit_accessibility(self.root, self.pid)  # writes + registers accessibility-gate

        types = self._types()
        self.assertIn("rights-gate", types)
        self.assertIn("accessibility-gate", types)

        active = self._active()
        self.assertIn("rights-gate", active)
        self.assertIn("accessibility-gate", active)

    def test_rights_ledger_registered_when_present(self) -> None:
        # Create a rights ledger so check_rights registers rights-ledger too.
        from publishing_house.util import atomic_write_json

        atomic_write_json(
            self.paths.rights_ledger,
            {"schema_version": "1.0", "project_id": self.pid, "records": []},
        )
        check_rights(self.root, self.pid)
        self.assertIn("rights-ledger", self._types())
        self.assertIn("rights-ledger", self._active())

    def test_reregistration_is_idempotent(self) -> None:
        check_rights(self.root, self.pid)
        audit_accessibility(self.root, self.pid)
        first = len(list_artifacts(self.root, self.pid))
        # Unchanged reports -> dedup, no new manifest entries.
        check_rights(self.root, self.pid)
        audit_accessibility(self.root, self.pid)
        second = len(list_artifacts(self.root, self.pid))
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
