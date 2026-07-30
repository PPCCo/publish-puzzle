from __future__ import annotations

import unittest
from pathlib import Path

from common import RepoFixture, SOURCE_ROOT

from publishing_house.state import StateTransitionError, transition

GATE_SKILLS = {
    "product-approve-niche",
    "product-approve-interior",
    "product-approve-cover",
    "product-approve-compliance",
    "product-approve-listing",
    "product-release-authorize",
    "product-submit",
    "product-incident",
    "product-freeze",
}


class GateIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = RepoFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_human_only_skills_cannot_be_model_invoked(self) -> None:
        for name in GATE_SKILLS:
            path = SOURCE_ROOT / ".claude" / "skills" / name / "SKILL.md"
            self.assertTrue(path.is_file(), name)
            self.assertIn("disable-model-invocation: true", path.read_text(encoding="utf-8"), name)

    def test_niche_gate_blocks_without_recorded_assessment(self) -> None:
        pid, _ = self.fixture.project()
        transition(self.fixture.root, pid, "NICHE_ASSESSMENT", "test", "begin")
        # The niche gate requires a recorded assessment; the transition must be refused.
        with self.assertRaises(StateTransitionError):
            transition(self.fixture.root, pid, "NICHE_APPROVAL", "test", "attempt gate without evidence")

    def test_claude_md_is_present_for_repo_root_resolution(self) -> None:
        self.assertTrue((SOURCE_ROOT / ".claude" / "CLAUDE.md").is_file())


if __name__ == "__main__":
    unittest.main()
