"""Tests for gate-approval hash scoping (Workstream A).

These verify that a human gate approval binds only to its SOURCE artifact types
(gate_packet._GATE_ARTIFACT_TYPES) and that re-registering a pure downstream build
output (artifacts._DOWNSTREAM_BUILD_TYPES) never invalidates that approval, while a
change to the approved SOURCE content still does.

The suite builds a real, schema-validated scratch project in a temporary repo root
whose ``.claude`` directory is symlinked to the real one (so schemas and company
config resolve normally) and whose ``projects`` tree is disposable — no side effect
on the working repository.

Run:
    .venv/bin/python3 -m unittest discover -s .claude/scripts/tests -p "test_*.py"
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

# Real repository root: .../pub-clr  (this file is at .claude/scripts/tests/).
REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / ".claude" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from publishing_house.approvals import (  # noqa: E402
    approval_is_current,
    grant_approval,
    list_approvals,
)
from publishing_house.artifacts import register_artifact  # noqa: E402
from publishing_house.gate_packet import build_gate_packet  # noqa: E402
from publishing_house.paths import ProjectPaths  # noqa: E402
from publishing_house.project import init_project  # noqa: E402
from publishing_house.util import atomic_write_json, load_json  # noqa: E402


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class ApprovalScopingTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        # Symlink the real .claude so schemas + company config resolve; keep a
        # disposable projects/ tree in the temp root.
        (self.root / ".claude").symlink_to(REPO_ROOT / ".claude")
        (self.root / "projects").mkdir()

        result = init_project(
            self.root,
            topic="Scratch scoping fixture",
            audience="adult-general",
            book_type="puzzle-book",
            project_id="scratch-scoping",
            created_by="test",
        )
        self.project_id = result["project"]["project_id"]
        self.paths = ProjectPaths(self.root, self.project_id).require()

        # Register the interior gate's SOURCE artifacts + one downstream PDF.
        self.content_hash = self._register(
            "content-sudoku", "content/batch-1.json", '{"batch": 1}', stage="CONTENT_GENERATION"
        )
        self.verify_hash = self._register(
            "content-verification",
            "verification/verify-1.json",
            '{"decision": "PASS"}',
            stage="CONTENT_VERIFICATION",
        )
        self._register("content-plan", "content/plan.json", '{"plan": true}', stage="PLANNING")
        self.interior_pdf_hash = self._register(
            "interior-pdf",
            "outputs/interior/interior-v1.pdf",
            "%PDF-1.7 v1",
            stage="LAYOUT_AND_FORMAT_BUILD",
        )

        # Sit the project at the interior gate so the packet targets it.
        self._set_state("INTERIOR_APPROVAL")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # --- helpers -----------------------------------------------------------
    def _register(self, artifact_type: str, rel_path: str, body: str, stage: str = "CONTENT_GENERATION") -> str:
        _write(self.paths.directory / rel_path, body)
        art = register_artifact(
            self.root,
            self.project_id,
            rel_path,
            artifact_type=artifact_type,
            stage=stage,
            actor="test",
        )
        return art["sha256"]

    def _set_state(self, current_state: str) -> None:
        state = load_json(self.paths.state)
        state["current_state"] = current_state
        atomic_write_json(self.paths.state, state)

    def _grant_interior(self) -> dict:
        return grant_approval(
            self.root,
            self.project_id,
            gate="interior",
            approver="PPC",
            approver_role="publisher",
            artifacts=[self.content_hash, self.verify_hash],
            scope="interior content freeze",
        )

    def _find(self, approval_id: str) -> dict:
        return next(a for a in list_approvals(self.root, self.project_id) if a["approval_id"] == approval_id)

    # --- tests -------------------------------------------------------------
    def test_downstream_pdf_rebuild_does_not_invalidate_interior_approval(self) -> None:
        approval = self._grant_interior()
        # Rebuild the interior PDF with new content -> new hash, re-register.
        self._register("interior-pdf", "outputs/interior/interior-v1.pdf", "%PDF-1.7 v2-rebuilt")

        record = self._find(approval["approval_id"])
        self.assertTrue(approval_is_current(record), "interior approval must survive a PDF rebuild")
        self.assertIsNone(record.get("invalidated_at"))
        state = load_json(self.paths.state)
        self.assertNotIn(approval["approval_id"], state.get("invalidated_approvals", []))

    def test_source_content_change_still_invalidates_interior_approval(self) -> None:
        approval = self._grant_interior()
        # Change the SOURCE content batch -> new hash, re-register.
        self._register("content-sudoku", "content/batch-1.json", '{"batch": 1, "revised": true}')

        record = self._find(approval["approval_id"])
        self.assertFalse(
            approval_is_current(record),
            "changing approved source content MUST invalidate the interior approval",
        )
        self.assertIsNotNone(record.get("invalidated_at"))
        state = load_json(self.paths.state)
        self.assertIn(approval["approval_id"], state.get("invalidated_approvals", []))

    def test_interior_packet_binds_source_not_pdf_but_shows_pdf(self) -> None:
        packet = build_gate_packet(self.root, self.project_id, "interior")
        bound = packet["human_action"]["artifact_hashes_to_bind"]

        self.assertIn(self.content_hash, bound)
        self.assertIn(self.verify_hash, bound)
        self.assertNotIn(
            self.interior_pdf_hash, bound, "interior approval must NOT bind the downstream PDF hash"
        )

        # The built PDF stays visible to the human even though it is not bound.
        review_files = packet["human_action"]["review_files"] or []
        self.assertTrue(
            any("interior-v1.pdf" in rel for rel in review_files),
            f"built interior PDF should appear in review_files for visibility; got {review_files}",
        )


if __name__ == "__main__":
    unittest.main()
