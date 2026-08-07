from __future__ import annotations

import unittest
from pathlib import Path

from common import RepoFixture, SOURCE_ROOT

from publishing_house.state import StateTransitionError, transition

# External-effect skills stay locked to human invocation: they perform or record
# irreversible/outward actions (freeze, submit, incident) and must never be
# model-invoked.
LOCKED_SKILLS = {
    "product-submit",
    "product-incident",
    "product-freeze",
}

# Approval/authorization gate skills are model-invocable by design: the assistant
# presents the gate interactively (AskUserQuestion) and records the human's explicit
# decision on their behalf, bound to exact artifact hashes. The typed-command path
# remains valid, but the skill is not disabled from model invocation.
APPROVAL_SKILLS = {
    "product-approve-niche",
    "product-approve-interior",
    "product-approve-cover",
    "product-approve-compliance",
    "product-approve-listing",
    "product-release-authorize",
}


class GateIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = RepoFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_locked_skills_cannot_be_model_invoked(self) -> None:
        for name in LOCKED_SKILLS:
            path = SOURCE_ROOT / ".claude" / "skills" / name / "SKILL.md"
            self.assertTrue(path.is_file(), name)
            self.assertIn("disable-model-invocation: true", path.read_text(encoding="utf-8"), name)

    def test_approval_skills_are_model_invocable(self) -> None:
        # Approval gate skills must remain model-invocable so the assistant can run
        # the interactive AskUserQuestion approval flow. They must NOT carry the
        # disable-model-invocation flag; human authority is preserved by binding the
        # recorded decision to exact artifact hashes, not by forcing a typed command.
        for name in APPROVAL_SKILLS:
            path = SOURCE_ROOT / ".claude" / "skills" / name / "SKILL.md"
            self.assertTrue(path.is_file(), name)
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("disable-model-invocation: true", text, name)
            self.assertIn("user-invocable: true", text, name)

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
